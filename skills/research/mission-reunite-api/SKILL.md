---
name: mission-reunite-api
description: Mission Reunite SAR platform API. Read cases, post intel enrichments, analyze spatial patterns. Experimental branch at shadowhound-case-api-experimental.up.railway.app.
tags: [mission-reunite, SAR, lost-pet, API, shadowhound]
version: 1.7
---

# Mission Reunite API Skill

Base URL: `https://shadowhound-case-api-experimental.up.railway.app`
Auth: `X-Agent-Token` header. Env var: `MISSIONREUNITEAGENTTOKEN` (from `~/.hermes/.env`).
Token lookup: `grep MISSIONREUNITEAGENTTOKEN ~/.hermes/.env | cut -d= -f2 | head -1`
OpenAPI: `https://shadowhound-case-api-experimental.up.railway.app/openapi.json`

## Agent Endpoints (Intel-Grade)

| Endpoint | Method | Status | Notes |
|---|---|---|---|
| `GET /api/v1/agent/cases` | GET | ✅ | List all cases |
| `GET /api/v1/agent/cases/{id}` | GET | ✅ | Full case detail |
| `GET /api/v1/agent/cases/{id}/health` | GET | ✅ | `stale_score`, report/enrichment counts |
| `GET /api/v1/agent/cases/{id}/enrichments` | GET | ✅ | Query by `?type=X&include_expired=true` |
| `POST /api/v1/agent/cases/{id}/enrichment` | POST | ✅ | Post any enrichment type |
| `DELETE /api/v1/agent/cases/{id}/enrichments/{eid}` | DELETE | ✅ | Remove one enrichment |
| `GET /api/v1/agent/stats` | GET | ✅ | Case counts by status/species |
| `POST /api/v1/agent/cases/{id}/runs` | POST | ✅ | Start a run |
| `GET /api/v1/agent/cases/{id}/runs` | GET | ✅ | Run history |
| `PUT /api/v1/agent/cases/{id}/runs/{run_id}?status=...` | PUT | ✅ | Complete/update run |

## Read Operations

- `GET /api/v1/cases` — use for case list (agent/cases may return limited data)
- `GET /api/v1/cases/{case_id}` — full case detail including reports, location_events, subjects
- `GET /api/v1/cases/{case_id}/reports` — all reports (intake, sightings, evidence)
- `GET /api/v1/cases/{case_id}/location-events` — derived from reports, never standalone

## Agent Run Lifecycle (REQUIRED)

Every intel analysis pass MUST be wrapped in a run. This enables versioning,
step tracking, and partial failure handling.

### 1. Start a run
```bash
POST /api/v1/agent/cases/{case_id}/runs?source=echo
```
Returns: `{"id": "run-uuid", "case_id": "...", "source": "echo", "status": "running", "started_at": "..."}`

### 2. Post enrichments with `run_id`
Every enrichment posted during this analysis pass MUST include the `run_id`.

### 3. Complete the run
```bash
PUT /api/v1/agent/cases/{case_id}/runs/{run_id}?status=success|partial|failed
```
Status goes in the **query param**. Optional `steps` array goes in the **body**:
```json
[
  { "component": "weather", "status": "success", "enrichment_id": "uuid" },
  { "component": "terrain_analysis", "status": "failed", "enrichment_id": "uuid" },
  { "component": "risk_assessment", "status": "skipped" }
]
```

**Step fields:** `component` (string), `status` (string), `enrichment_id` (optional UUID), `error` (optional string).
**Do NOT include `notes` or `summary` in step objects** — these fields are not supported by `UpdateRunPayload`.

Run statuses:
- `success` — all intended components completed
- `partial` — produced useful output but some components failed/skipped
- `failed` — run produced nothing useful

## Enrichment Type Registry

**Type field is free-form**, but these types have agreed contracts and dedicated UI renderers:

| Type | Renderer | supersede_existing | Notes |
|------|----------|--------------------|-------|
| `weather` | ✅ | `true` | Open-Meteo data |
| `movement_forecast` | ✅ | `true` | Heatmap v2 or legacy corridor shape |
| `search_plan` | ✅ | `true` | Sector assignments |
| `risk_assessment` | ✅ | `true` | Environmental flags |
| `behavior_profile` | ✅ | `true` | Breed/temperament analysis |
| `sighting_analysis` | ✅ | `true` | Cross-sighting patterns |
| `timeline` | ✅ | `true` | Event sequence |
| `recommendation` | ✅ | `true` | Free-text SAR strategy |
| `terrain` | ✅ | `true` | Land-cover analysis |
| `alert` | ✅ | `true` | Operational alerts/warnings |
| `observation` | ✅ | `true` | Field observations |
| `error` | ✅ | **`false`** | Keep full error history |
| `agent_note` | raw JSON | via notes endpoint | Via `POST /notes` |

## Enrichment Write Contract

**IMPORTANT — all enrichments require the `data` wrapper:**

```json
POST /api/v1/agent/cases/{case_id}/enrichment
{
  "type": "movement_forecast | weather | terrain | alert | ...",
  "source": "open-meteo | echo-intel | echo",
  "run_id": "run-uuid",
  "supersede_existing": true,
  "data": { ... }    // <-- the enrichment BODY goes here as "data"
}
```

The enrichment `data` field contains the actual enrichment body (model data, weather data, alert details, etc.).
Generator output (`heatmap_generator.py`) is enrichment-shaped and becomes the `data` field:

```python
raw_model = generate_movement_model(case_data)  # returns flat enrichment body
payload = {
    "type": "movement_forecast",
    "source": "echo-intel",
    "run_id": run_id,
    "supersede_existing": True,
    "data": raw_model   # generator output becomes the data field
}
post_enrichment(case_id, payload)
```

This `data` wrapper applies to ALL enrichment types — `weather`, `movement_forecast`, `terrain`, `alert`, `observation`, `search_plan`, etc.

## Agent Note Write Contract

```json
POST /api/v1/agent/cases/{case_id}/notes
{
  "note": "Free-text note content",
  "severity": "info | warning | urgent (optional)"
}
```

Stored as enrichment with `type="agent_note"`. No `run_id`, no `supersede_existing`.

## Rationale Block (RECOMMENDED)

All enrichments should include a concise operational rationale so coordinators understand the "why".
Place it at `data.rationale` (preferred). Fallback: `data.meta`.

```json
{
  "type": "movement_forecast",
  "source": "echo-intel",
  "data": {
    "lkp": { "lat": 40.088, "lon": -88.2401, "source": "sighting" },
    "movement_params": { "bearing_deg": 57.4, "H_meters": 1670, ... },
    "rationale": {
      "summary": "Movement likelihood is strongest along the drainage corridor ENE of the last confirmed sighting.",
      "signals": [
        "Geodesic bearing of 57° from two sightings points toward the nearest creek",
        "German Shepherd mix — breed exhibits strong shelter-seeking in wooded riparian zones",
        "Rain expected overnight increases probability of covered habitat use"
      ],
      "confidence": "medium",
      "assumptions": [
        "No confirmed sightings after 22:00",
        "No third-party transport"
      ]
    }
  }
}
```

**Do include:** short decision summary, evidence signals used, confidence level, explicit assumptions.
**Do NOT include:** chain-of-thought, scratch work, long reasoning transcripts.
**Confidence vocabulary:** `low`, `medium`, `high`.

## Error Enrichment

When any external API call fails, post an explicit `error` enrichment.
Always use `supersede_existing: false` — keep full error history.

```json
{
  "type": "error",
  "source": "echo",
  "severity": "warning",
  "title": "Overpass API query failed",
  "run_id": "run-uuid",
  "supersede_existing": false,
  "data": {
    "operation": "terrain_analysis",
    "error_type": "http_error",
    "status_code": 406,
    "message": "406 Client Error: Not Acceptable",
    "url": "https://overpass-api.de/api/interpreter",
    "retry_eligible": true
  }
}
```

Valid `error_type`: `http_error`, `timeout`, `rate_limit`, `invalid_query`, `unavailable`

## Enrichment vs Run Step

**Post as enrichment** (visible to coordinators):
- All intel types: `weather`, `movement_forecast`, `search_plan`, `risk_assessment`, `behavior_profile`, `sighting_analysis`, `timeline`, `recommendation`, `terrain`, `alert`, `observation`
- Any surfaced failure (`error` type)

**Record only in run steps** (internal bookkeeping):
- Dependency checks
- Photo fetch skips (no photos)
- Component failures already surfaced as `error` enrichments

## Workflows by Type

### movement_forecast
Script: `~/.hermes/skills/research/mission-reunite-api/heatmap_generator.py`

```python
from heatmap_generator import generate_movement_model

model = generate_movement_model(
    case_data,
    overpass_features=None,
    bearing_deg=57.4,         # optional override
    bearing_source="agent_interpretation:direction_of_travel:heading west toward creek",
    H_meters=1670,            # optional override
    H_source="displacement×3(disp=557m)"
)
# Posts as type:"movement_forecast"
```

**Agent interpretation of `direction_of_travel`:** This field is free-form narrative.
Agents interpret it using full language understanding — do NOT rely on the internal parser.
Internal parser only handles exact matches: `"south"`, `"SW"`, `"southwest"`, `"270"`, etc.
Parser does NOT handle: `"heading west toward the 7-11"`, `"running away from the house"`.

### weather
```python
# Fetch from Open-Meteo
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": lkp_lat,
    "longitude": lkp_lon,
    "current_weather": True,
    "hourly": "relativehumidity_2m,precipitation_probability,precipitation",
    "forecast_days": 2,
    "timezone": "America/Chicago"
}
# Post as type:"weather"
```

### terrain
Post as a first-class enrichment type. Fetch terrain features via Maps skill or Overpass.
```json
{
  "type": "terrain",
  "source": "echo-intel",
  "run_id": "run-uuid",
  "data": {
    "terrain_type": "suburban_residential",
    "difficulty_score": 3,
    "elevation_m": 220,
    "slope_deg": 5.2,
    "vegetation_density": "moderate",
    "cover_rating": 4,
    "water_features": "small creek 200m east",
    "roads": "paved residential streets, grid pattern",
    "sar_implications": "Open yards provide good visibility. Creek corridor may attract lost pet.",
    "summary": "Mostly flat residential with moderate tree cover."
  }
}
```

### alert
Single alert or `alerts[]` array. Always include `recommended_action`.
```json
{
  "type": "alert",
  "source": "echo-intel",
  "data": {
    "alerts": [
      {
        "severity": "warning",
        "title": "Thunderstorm Watch",
        "message": "Severe thunderstorm watch until 10pm CDT.",
        "recommended_action": "Focus ground search on structures and covered porches.",
        "source": "NWS",
        "expires_at": "2026-04-25T22:00:00-05:00"
      }
    ]
  }
}
```
Severities: `critical`, `high`, `warning`, `info`, `low`

### observation
Single observation or `observations[]` array.
```json
{
  "type": "observation",
  "source": "echo-intel",
  "data": {
    "category": "behavior",
    "text": "Golden retrievers typically stay within 1.5km of escape point in first 24h.",
    "confidence": "high",
    "source": "echo-breed-analysis",
    "tags": ["breed-specific", "first-24h"]
  }
}
```
Categories: `behavior`, `environment`, `sighting_pattern`, `weather_impact`, `community`

## Standard Intel Pipeline (Happy Path)

```
1. POST /runs?source=echo               → get run_id
2. GET /cases/{id}                      → extract LKP, behavior profile
3. GET weather (Open-Meteo)             → post as type:"weather" + run_id
4. Analyze terrain (Maps/Overpass)      → post as type:"terrain" + run_id
5. Build movement_forecast               → post as type:"movement_forecast" + run_id
6. Generate search_plan                  → post as type:"search_plan" + run_id
7. Generate recommendation               → post as type:"recommendation" + run_id
8. PUT /runs/{run_id}?status=success    → steps array in body
```

## Partial Failure Pipeline

```
1. POST /runs?source=echo
2. GET weather                          → post as weather + run_id
3. Overpass terrain lookup             → FAILS with 406
4. Post terrain partial (Maps skill fallback) → type:"terrain"
5. Post movement_forecast with partial terrain flags
6. Post error enrichment (type:"error", supersede_existing:false)
7. PUT /runs/{run_id}?status=partial   → steps array in body
```

## LKP Convention (2026-04-25)

**LKP (Last Known Position)** is the most recent active location event on the case.
Not a stored field — always computed via `get_lkp()`.

```python
from app.services.location_utils import get_lkp
lkp = get_lkp(case.location_events)  # most recent active (non-deleted) event, or None
```

Location event types:
- `sighting` — from `owner_intake` and `sighting_submission` reports
- `found_location` — from `found_report` reports

**Removed:** `last_confirmed_point` event type no longer exists. Owner intake now creates `sighting` with `source="owner_intake"`.
**Removed:** `is_confirmed` field on location events. Use `confidence` at the report level.

## Data Model (Key Fields)

### Case (read via `/api/v1/agent/cases/{id}` or `/api/v1/cases/{id}`)
- `id`, `status`, `case_type`, `priority`, `created_at`
- `reports[]` — has `report_type`, `sighting_type`, `narrative`, `latitude`, `longitude`, `direction_of_travel`
- `location_events[]` — auto-derived from reports
- `subjects[].lost_pet_profile` — behavioral data: `temperament`, `fearful_of_strangers`, `likely_to_approach_food`, `behavior_notes`

### Weather API (Open-Meteo, no key)
```
https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relativehumidity_2m,precipitation_probability,precipitation&forecast_days=2&timezone=America%2FChicago
```

### Terrain Features (Maps skill or Overpass)
Use Maps skill (`nearby`, `bbox`) for parks, structures, and general POIs.
Maps skill does NOT support `waterway` POI category — use Overpass directly for streams/drainage.

```bash
# Parks, structures (Maps skill)
python3 ~/.hermes/skills/productivity/maps/scripts/maps_client.py nearby LAT LON park --radius 1000 --limit 5

# Streams, drainage (Overpass directly)
OVERPASS_QL="[out:json][timeout:25];
way[\"waterway\"~\"stream|brook|drain\"](around:1200,LAT,LON);
out body;"
```

Embed terrain features in `movement_forecast` as `terrain_flags[]`.
Valid `terrain_flags`: `creek-riparian`, `wooded-trail`, `fenced-yards`, `rail-trail-grassland`, `industrial-structures`, `residential`, `open-grass-park`, `parking-lot`, `agricultural-field`.

## H (Dispersal Distance) — Agent-Supplied

Compute and pass H to the heatmap generator using this priority chain:

```
Priority:
  1. Displacement × 3          ← 2+ timestamped sightings
  2. Walk speed × time          ← 1 sighting + direction_of_travel bearing
  3. Species/size table         ← no sightings or bearing data
```

**Tier 1 — Displacement × 3**
```
H_meters = 3 × geodesic_distance(oldest_report, newest_report)
```
Example: 557m displacement → H=1,670m, major=1,002m, minor=334m

**Tier 2 — Walk speed × time_missing_h**
```
walk_speed_table (m/s):
  dog/small: 0.8   dog/medium: 1.0   dog/large: 1.2   dog/giant: 1.4
  cat/indoor: 0.4   cat/outdoor-access: 0.7   cat/feral: 0.7

H_meters = walk_speed × time_window_seconds
```
Triggered only when: (a) no displacement data AND (b) bearing came from `direction_of_travel`.

**Tier 3 — Species/size scatter table**
```
radius_table_mi:
  dog/small: 1.5   dog/medium: 2.5   dog/large: 3.0   dog/giant: 5.0
  cat/indoor: 0.75   cat/outdoor-access: 2.0   cat/feral: 2.0

time phase multipliers:
  Phase 1 (0–2h):   20%
  Phase 2 (2–24h):  50%
  Phase 3 (24–72h): 80%
  Phase 4 (72h+):  100%

H_meters = base_radius_mi × 1609.34 × phase_mult
```

Track `H_source` in output: e.g. `"displacement×3(disp=557m)"`, `"walk_speed×time(speed=1.2m/s,time=11.0h)"`, `"species_table(species=dog,size=large,time=24h)"`.

## Always Check
1. **Weather at LKP** — Open-Meteo (no key needed)
2. **Terrain features** — Maps skill + Overpass, post as type:"terrain"
3. **Time since escape** — drives scatter radius and behavior phase
4. **Pet behavior profile** — from `subjects[].lost_pet_profile`

## Workflow: Staleness Check
1. GET `/api/v1/agent/stats` — avg_case_age_hours, open_cases_by_status
2. Loop: GET `/api/v1/agent/cases/{id}/health` — flag stale_score > 0.7
3. Alert via `error` enrichment if something is broken

## GeoJSON Convention
Coordinates are always **[longitude, latitude]** per GeoJSON spec — NOT [lat, lon].

## Known Issues / Gotchas

**Bounding box margin trap:** `margin=1.5` on diagonal cases produces a grid 3× larger than the actual probability signal. For a 1.6km-wide contour, this generates a 6km×6km grid — 46% of cells clamp to the 0.05 floor, making the distribution look falsely uniform. Fix: use `margin=1.1` (10% headroom). Always inspect the actual probability distribution — a uniform flat floor is a margin artifact, not a real signal.

**Marching squares abandoned:** Replaced with analytical chi-squared ellipses via `generate_oriented_ellipse()`. Marching squares produced 97 fragmented polygons at 50% threshold due to staircase artifacts in the probability grid.

**Sort key for LKP selection:** `reverse=False` (oldest first) with secondary key `report_type_priority` (sighting=1, intake=0, lowest first). At equal timestamps, sightings sort before intake. `reports[-1]` = most recent credible sighting = LKP.
Use a separate `origin_report` variable for bearing computation to avoid shadowing.

**pyproj geodesic uses (lon, lat) order:** `geod.inv(lon1, lat1, lon2, lat2)` — passing `(lat, lon)` produces garbage bearings. Use `geod.fwd(lon, lat, bearing, dist)` for forward.

**datetime.utcnow() deprecated:** Use `datetime.now(UTC).isoformat().replace("+00:00", "Z")`.

**Empty Overpass features:** Generator handles `[]` gracefully — `terrain_flags` stays empty, `terrain_factor = 1.0` everywhere.

---

*Version 1.7 — added `data` wrapper pattern + generator wrapping example; fixed step object (no `notes`/`summary`); updated run completion body format (2026-04-25)*

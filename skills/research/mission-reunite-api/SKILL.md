---
name: mission-reunite-api
description: Mission Reunite SAR platform API. Read cases, post intel enrichments, analyze spatial patterns. Experimental branch at shadowhound-case-api-experimental.up.railway.app.
tags: [mission-reunite, SAR, lost-pet, API, shadowhound]
version: 1.5
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
| `PUT /api/v1/agent/cases/{id}/runs/{run_id}` | PUT | ✅ | Complete/update run |

## Read Operations

- `GET /api/v1/cases` — **use for case list** (agent/cases may return limited data)
- `GET /api/v1/cases/{case_id}` — full case detail including reports, location_events, subjects
- `GET /api/v1/cases/{case_id}/reports` — all reports (intake, sightings, evidence)
- `GET /api/v1/cases/{case_id}/location-events` — derived from reports, never standalone

## Agent Run Lifecycle (REQUIRED)

Every intel analysis pass should be wrapped in a run. This enables versioning,
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
Body (optional steps array):
```json
[
  { "component": "weather", "status": "success", "enrichment_id": "..." },
  { "component": "terrain_analysis", "status": "failed", "error": "406 ..." },
  { "component": "risk_assessment", "status": "skipped", "reason": "depends on terrain" }
]
```

Run statuses:
- `success` — all intended components completed
- `partial` — produced useful output but some components failed/skipped
- `failed` — run produced nothing useful

## Enrichment Type Registry

**Type field is free-form**, but these types have agreed contracts and dedicated UI renderers:

| Type | Renderer | Notes |
|------|----------|-------|
| `weather` | ✅ WeatherRenderer | Open-Meteo data |
| `movement_model` | ✅ MovementModelRenderer | GeoJSON, corridors, search zones |
| `search_plan` | ✅ SearchPlanRenderer | Sector assignments |
| `risk_assessment` | ✅ RiskAssessmentRenderer | Environmental flags |
| `behavior_profile` | ✅ BehaviorProfileRenderer | Breed/temperament analysis |
| `sighting_analysis` | ✅ SightingAnalysisRenderer | Cross-sighting patterns |
| `timeline` | ✅ TimelineRenderer | Event sequence |
| `recommendation` | ✅ RecommendationRenderer | Free-text SAR strategy |
| `error` | ✅ ErrorRenderer | Failures surfaced to coordinators |
| `agent_note` | raw JSON | Via notes endpoint |

**`terrain` is NOT a valid enrichment type.** Terrain analysis is a run *component*.
Its output should be embedded in `movement_model` or recorded as a run step (not an enrichment)
if it failed.

## Enrichment Write Contract

```json
POST /api/v1/agent/cases/{case_id}/enrichment
{
  "type": "weather | movement_model | search_plan | risk_assessment | behavior_profile | sighting_analysis | timeline | recommendation | error",
  "source": "open-meteo | echo-intel | echo",
  "run_id": "run-uuid",
  "severity": "info | warning | urgent (optional)",
  "title": "optional human-readable title",
  "data": { ... },
  "supersede_existing": true,
  "expires_at": "ISO-8601 (optional)"
}
```

## supersede_existing Policy by Type

| Type | supersede_existing |
|------|-------------------|
| `weather` | `true` |
| `movement_model` | `true` |
| `search_plan` | `true` |
| `risk_assessment` | `true` |
| `behavior_profile` | `true` |
| `sighting_analysis` | `true` |
| `timeline` | `true` |
| `recommendation` | `true` |
| `error` | **`false`** — keep full error history |

## Agent Note Write Contract

```json
POST /api/v1/agent/cases/{case_id}/notes
{
  "category": "observation | alert | recommendation",
  "severity": "info | warning | urgent",
  "title": "Brief title",
  "body": "Free-text observation"
}
```

Stored as enrichment with `type=category` (e.g. `observation`, `alert`, `recommendation`).
No `run_id`, no `supersede_existing` — each note is independent.

## Rationale Block (RECOMMENDED)

All enrichments should include a concise operational rationale so coordinators understand the "why":

```json
{
  "type": "movement_model",
  "source": "echo-intel",
  "data": {
    "lkp": { "lat": 40.088, "lon": -88.2401, "is_confirmed": true, "source": "sighting" },
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

## Error Enrichment

When any external API call fails, post an explicit `error` enrichment:

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
- `weather`, `movement_model`, `search_plan`, `risk_assessment`, `behavior_profile`, `sighting_analysis`, `timeline`, `recommendation`
- Any surfaced failure (`error` type)

**Record only in run steps** (internal bookkeeping):
- Dependency checks
- Photo fetch skips (no photos)
- Component failures that are already surfaced as `error` enrichments

## Standard Intel Pipeline (Happy Path)

```
1. POST /runs?source=echo           → get run_id
2. GET /cases/{id}                 → extract LKP, behavior profile
3. GET weather (Open-Meteo)          → post as type:"weather" + run_id
4. Analyze terrain (Maps skill)     → embed as terrain_flags[] in movement_model
5. Build movement_model             → post as type:"movement_model" + run_id
6. Generate search_plan             → post as type:"search_plan" + run_id
7. Generate recommendation         → post as type:"recommendation" + run_id
8. PUT /runs/{run_id}?status=success with steps array
```

## Partial Failure Pipeline

```
1. POST /runs?source=echo
2. GET weather                      → post as weather + run_id
3. Overpass terrain lookup         → FAILS with 406
4. Post movement_model with partial terrain flags (Maps skill fallback)
5. Post error enrichment (type:"error", supersede_existing:false) for Overpass failure
6. Post risk_assessment with available data
7. PUT /runs/{run_id}?status=partial
   steps: [
     {component:"weather", status:"success", enrichment_id:"..."},
     {component:"terrain_analysis", status:"failed", error:"406..."},
     {component:"movement_model", status:"success", enrichment_id:"..."},
     {component:"risk_assessment", status:"skipped", reason:"depends on terrain"},
     {component:"recommendation", status:"success", enrichment_id:"..."}
   ]
```

## Data Model (Key Fields)

### Case (read via `/api/v1/agent/cases/{id}` or `/api/v1/cases/{id}`)
- `id`, `status`, `case_type`, `priority`, `created_at`
- `reports[]` — has `report_type`, `sighting_type`, `narrative`, `latitude`, `longitude`, `direction_of_travel`
- `location_events[]` — **auto-derived from reports**, `event_type` distinguishes confirmed LKP from sightings
  - `event_type: "last_confirmed_point"` — owner intake (is_confirmed=true)
  - `event_type: "sighting"` — sighting submission (is_confirmed=false)
  - `event_type: "found_location"` — found report
- **`last_confirmed_point` and `sighting` LocationEvents are derived from reports, never standalone** — they reflect the report's `latitude`, `longitude`, `occurred_at` at the time of submission. Coordinate corrections on reports do NOT currently auto-sync to location events (pending `feature/lkp-standardization` merge)
- `subjects[].lost_pet_profile` — behavioral data: `temperament`, `fearful_of_strangers`, `likely_to_approach_food`, `behavior_notes`

### Weather API (Open-Meteo, no key)
```
https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relativehumidity_2m,precipitation_probability,precipitation&forecast_days=2&timezone=America%2FChicago
```

### Terrain Features (Maps skill or Overpass)
Use Maps skill (`nearby`, `bbox`) for parks, structures, and general POIs.
**Note:** Maps skill does NOT support `waterway` POI category — use Overpass directly
for stream/drainage/creek features.

```bash
# Parks, structures (Maps skill — correct path)
python3 ~/.hermes/skills/productivity/maps/scripts/maps_client.py nearby LAT LON park --radius 1000 --limit 5

# Streams, drainage (Overpass directly)
OVERPASS_QL="[out:json][timeout:25];
way[\"waterway\"~\"stream|brook|drain\"](around:1200,LAT,LON);
out body;"
```

Embed results in `movement_model`:
```json
{
  "type": "movement_model",
  "data": {
    "terrain_flags": ["creek-riparian", "wooded-trail", "fenced-yards"],
    "scatter_model_notes": "Creek bed 0.3mi east is primary corridor."
  }
}
```

Valid `terrain_flags`: `creek-riparian`, `wooded-trail`, `fenced-yards`, `rail-trail-grassland`,
`industrial-structures`, `residential`, `open-grass-park`, `parking-lot`, `agricultural-field`.

## Always Check
1. **Weather at LKP** — Open-Meteo (no key needed)
2. **Terrain features** — Maps skill, embed in movement_model
3. **Time since escape** — drives scatter radius and behavior phase
4. **Pet behavior profile** — from `subjects[].lost_pet_profile`

## Workflow: Staleness Check
1. GET `/api/v1/agent/stats` — avg_case_age_hours, open_cases_by_status
2. Loop: GET `/api/v1/agent/cases/{id}/health` — flag stale_score > 0.7
3. Alert via `error` enrichment if something is broken

## Movement Model Generator

Script: `~/.hermes/skills/research/mission-reunite-api/heatmap_generator.py`

```python
from heatmap_generator import generate_movement_model

# Agent-supplied overrides (recommended):
#   bearing_deg:    57.4  (interpret from direction_of_travel narrative)
#   bearing_source: "agent_interpretation:direction_of_travel:heading west toward creek"
#   H_meters:       1670  (computed from displacement, walk_speed×time, or species table)
#   H_source:       "displacement×3(disp=557m)"
#
# Generator fallback: if overrides not supplied, uses internal NL parser + three-tier H model.

model = generate_movement_model(
    case_data,
    overpass_features=None,
    bearing_deg=57.4,
    bearing_source="agent_interpretation:direction_of_travel:heading west toward creek",
    H_meters=1670,
    H_source="displacement×3(disp=557m)"
)
```

### Agent interpretation of direction_of_travel

**The `direction_of_travel` field is free-form narrative.** Agents should interpret it, not rely on the generator's internal parser.

Parser handles: `"south"`, `"SW"`, `"southwest"`, `"south-southwest"`, `"s, sw"`, `"270"`.
Parser does NOT handle: `"heading west toward the 7-11"`, `"running away from the house"`, `"toward the creek"`.

**Agent workflow:**
1. Read the `direction_of_travel` narrative from each sighting report
2. Interpret the direction using full language understanding
3. Pass the computed `bearing_deg` and a descriptive `bearing_source` to the generator

`bearing_source` should describe how you derived it, e.g.:
- `"agent_interpretation:direction_of_travel:heading west toward 7-11"`
- `"geodesic_oldest_to_newest"` (two georeferenced reports with timestamps)
- `"default"` (no bearing data)

### H (dispersal distance) — agent-supplied

Compute and pass H from the same three-tier model, then supply the value:

```
Priority chain:
  1. Displacement × 3          ← 2+ timestamped sightings
  2. Walk speed × time          ← 1 sighting + direction_of_travel bearing
  3. Species/size table         ← no sightings or bearing data
```

**Tier 1 — Displacement × 3 (highest priority)**
```
H_meters = 3 × geodesic_distance(oldest_report, newest_report)
```
Example: 557m displacement → H=1,670m, major=1,002m, minor=334m (Buddy)

**Tier 2 — Walk speed × time_missing_h (fallback)**
```
walk_speed_table (m/s):
  dog/small: 0.8   dog/medium: 1.0   dog/large: 1.2   dog/giant: 1.4
  cat/indoor: 0.4   cat/outdoor-access: 0.7   cat/feral: 0.7

H_meters = walk_speed × time_window_seconds
```
Triggered only when: (a) no displacement data AND (b) bearing came from `direction_of_travel`.

**Tier 3 — Species/size scatter table (final fallback)**
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

`H_source` tracked in output (e.g. `"displacement×3(disp=557m)"`, `"walk_speed×time(speed=1.2m/s,time=11.0h)"`, `"species_table(species=dog,size=large,time=24h)"`).

### Bounding box

Default margin = 1.1 (10% headroom beyond outer 5% chi-squared contour).
Grid cell size = 50m. All cells above 0.05 threshold are output.

### Known issues / gotchas

**Bounding box margin trap:** `margin=1.5` on diagonal cases produces a grid 3× larger than the actual probability signal. For a 1.6km-wide contour, this generates a 6km×6km grid — 46% of cells clamp to the 0.05 floor, making the distribution look falsely uniform. Fix: use `margin=1.1` (10% headroom). Always inspect the actual probability distribution — a uniform flat floor is a margin artifact, not a real signal.

**Marching squares abandoned:** Replaced with analytical chi-squared ellipses via
`generate_oriented_ellipse()`. Marching squares produced 97 fragmented polygons at 50%
threshold due to staircase artifacts in the probability grid.

**Sort key for LKP selection:** `reverse=False` (oldest first) with secondary key
`report_type_priority` (sighting=1, intake=0, lowest first). At equal timestamps,
sightings sort before intake. `reports[-1]` = most recent credible sighting = LKP.
Use a separate `origin_report` variable for bearing computation to avoid shadowing.

**pyproj geodesic uses (lon, lat) order:** `geod.inv(lon1, lat1, lon2, lat2)` — passing
`(lat, lon)` produces garbage bearings. Use `geod.fwd(lon, lat, bearing, dist)` for forward.

**datetime.utcnow() deprecated:** Use `datetime.now(UTC).isoformat().replace("+00:00", "Z")`.

**Empty Overpass features:** Generator handles `[]` gracefully — `terrain_flags` stays empty,
`terrain_factor = 1.0` everywhere.

## GeoJSON Convention
Coordinates are always **[longitude, latitude]** per GeoJSON spec — NOT [lat, lon].

---

*Version 1.5 — AgentNotePayload reshaped (category/title/body), rationale block documented, enrichment/step boundary clarified, heatmap generator: agent-supplied bearing/H overrides, auto-generates rationale block (2026-04-25)*

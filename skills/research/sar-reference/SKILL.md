---
name: sar-reference
description: "Lost pet SAR reference corpus — scatter radius models, behavioral phase analysis, weather effects, terrain feature优先级, and structured intel briefing format. For Mission Reunite case analysis."
tags: [SAR, lost-pet, scatter, behavior, weather, terrain, intel, briefing]
version: 1.1
---

# SAR Reference Corpus

Five reference documents covering the core knowledge domains for Mission Reunite lost pet intel analysis.

## Files

| File | Content |
|------|---------|
| `scatter-radius.md` | Distance models by species/size/terrain/time. Phase-based probability envelopes. |
| `behavior.md` | Behavioral phases (panic/denning/exploration/survival). Dogs vs. cats. Temperature effects. Breed-specific notes. |
| `weather.md` | Weather effects on movement and detection. Open-Meteo interpretation guide. Strategic overlays. |
| `terrain.md` | Linear feature优先级. Cover quality. Creek beds (#1 priority). OSM terrain analysis. Urban/rural adjustments. |
| `briefing-template.md` | Standard intel brief format. New case pipeline. Staleness check workflow. Example (Gracie). |

## Quick Lookup

### Terrain in movement_model
**Terrain features are NOT posted as a separate enrichment type.** Use the Maps skill to query
OSM features near the LKP, then embed findings in the `movement_model` enrichment:

```json
{
  "type": "movement_model",
  "source": "echo-intel",
  "data": {
    "terrain_flags": ["creek-riparian", "wooded-trail", "fenced-yards", "rail-trail-grassland"],
    "terrain_notes": "Creek bed 0.3mi east is primary corridor. Industrial structures provide cover to south."
  }
}
```

Valid `terrain_flags`: `creek-riparian`, `wooded-trail`, `fenced-yards`, `rail-trail-grassland`,
`industrial-structures`, `residential`, `open-grass-park`, `parking-lot`, `agricultural-field`.

### Phase-Based Search Priorities
```
Phase 1 (Panic/0-2hr):    Linear corridors. Initial heading. Mile radius.
Phase 2 (Denning/2-24hr): Intensive grid. 1/2-mile. All shelter.
Phase 3 (Explore/24-72hr): Expand radius. Dawn/dusk windows. Food sources.
Phase 4 (Survival/72+hr):  Traps. Scent dogs. Community alerts.
```

### Weather Decision Tree
```
Temp <40°F:   Contract radius 60-80%. Check heated structures.
Temp >85°F:   Dawn/dusk only. Water sources.
Wind >15mph:  Scent work marginal. Ground tracks visible.
Precipitation: Pet stationary. Intensive local search.
Darkness:     Thermal. Dawn/dusk windows optimal.
```

### Terrain Top 3
1. **Creek beds / Drainage** — water + cover + wildlife trails. #1 priority.
2. **Wood lines / Tree lines** — shade, concealment, animal paths.
3. **Fence lines** — familiar scent, boundary guidance.

## Usage

1. Load case from Mission Reunite API
2. Query Open-Meteo for weather at LKP
3. Query Maps skill for terrain features near LKP
4. Apply scatter-radius → probability envelope
5. Apply weather overlay → adjust priorities
6. Fill in briefing-template → post to case

## Data Sources

- Open-Meteo (free, no key): `api.open-meteo.com/v1/forecast`
- OSM/Nominatim via Maps skill
- University of Arizona Lost Pet Studies
- NCPWR terrain modeling
- Mission Reunite SAR behavioral database

---

*Analyst: Echo. For Mission Reunite coordinator use. All intel subject to on-ground judgment.*

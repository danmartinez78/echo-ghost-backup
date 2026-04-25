# Weather Effects on Lost Pet Search

**Purpose:** Adjust search strategy and probability estimates based on current and forecast weather conditions.

---

## General Principles

Weather has two major effects on lost pet behavior:
1. **Movement** — how far and when the pet travels
2. **Detection** — how easy it is to find evidence (scent, tracks, sightings)

Never plan a search without checking weather — conditions can change the entire probability model.

---

## Temperature

### Cold Weather (<40°F / 4°C)

**Effect on pets:**
- Small dogs (<20 lb) become nearly immobile. Movement drops 80–90%.
- Medium/large dogs reduce movement 50–60%.
- Cats seek any heat source: under car hoods (check before driving!), near HVAC vents, under decks with warm ground.
- Pets may travel toward houses, garages, barns seeking warmth.

**Search implications:**
- Search radius contracts significantly — most likely within 1/4 mile even if "it's been days"
- Intensive search near heated structures, especially at night
- Check under car hoods and wheel wells
- Warm vehicles in garages = check BEFORE starting engine

### Hot Weather (>85°F / 29°C)

**Effect on pets:**
- Movement almost entirely suppressed during midday (10am–6pm)
- Dawn (5–8am) and dusk (7–10pm) are the active windows
- Pets seek water sources: sprinklers, pools, creeks, bird baths, ponds
- Brachycephalic breeds (Bulldogs, Pugs) overheat rapidly — limited movement even in cool temps

**Search implications:**
- Schedule primary search effort for dawn/dusk
- During daytime: search near water sources, shade, cool concrete areas
- Overnight: expand search radius — cool temps trigger movement
- Thermal cameras can detect pets in sheds/garages during hot days

---

## Precipitation

### Rain

| Intensity | Effect | Search Adjustment |
|-----------|--------|------------------|
| Light drizzle | Reduced movement, pets seek cover | Search porches, covered areas, under eave |
| Steady rain | Movement drops 60–80% | Pet is stationary — check every shelter point |
| Heavy rain | Movement near zero | Intensive local search only |
| Brief thunderstorm | Fleeing pet may bolt further | Post-storm: check initial flight corridors |

**Key insight:** After rain stops, you have a brief 30–60 minute window where the pet is still likely to be in the same spot, but detection conditions improve (fresh tracks, wet fur makes them visible).

### Snow

- Cats lose ability to track-scent their environment — mobility drops 50%
- Dogs can follow scent but ground scent trails are masked
- Fresh snow = perfect tracking conditions (follow paw prints)
- Snow reveals movement that wouldn't be visible otherwise
- After snowfall: immediate search, tracks show direction of travel
- Snow limits radius significantly — check dense cover areas

---

## Wind

**Effect on detection:**
- Wind disperses scent plumes — scent dogs less effective above 15mph gusts
- Owner scent at LKP disperses faster = harder for pet to find way back
- Wind >20mph: scent-trailing ineffective, postpone until calmer

**Effect on pet behavior:**
- Strong wind causes disorientation
- Pets tend to move WITH the wind (not against it)
- High winds: reduce radius 30–40%

---

## Darkness / Night

**Effect on pet behavior:**
- Most lost pets reduce movement significantly at night (except food-motivated cats)
- Dogs are more likely to freeze in place when scared at night
- Night = peak activity for some cats (more comfortable moving when quieter)

**Effect on search:**
- Visual sighting nearly impossible without thermal/motion cameras
- Thermal cameras highly effective — detects body heat at 100+ yards
- Night searches: bring thermal or quality spotlight
- Best night search window: 30 minutes after sunset, 30 minutes before sunrise

---

## Weather Patterns: Strategic Overlays

### Cold Front Passage
- Front passes → temperature drops rapidly
- 2–4 hours post-front: spike in pet movement (pressure change triggers restlessness)
- After 6 hours: movement drops with cold
- **Best window:** 2–4 hours post-front passage

### Warm Front Approach
- Gradual warming, increasing cloud cover
- Mild activity increase preceding the front
- Precipitation likely at front passage
- Movement may increase before rain arrives

### High Pressure (Clear, Calm)
- Best conditions for scent-trailing (stable air, light wind)
- Pets are comfortable — normal activity patterns
- Optimal conditions for both pet movement and human search

### Low Pressure / Stormy
- Pets seek shelter immediately
- Movement suppressed
- Best time for local intensive search, worst time for wide-radius search

---

## Open-Meteo Interpretation for SAR

Free API: `api.open-meteo.com/v1/forecast`

**Key fields to pull for search planning:**

```
latitude, longitude
current_weather: temperature, windspeed, winddirection, weathercode, is_day
hourly (next 24h): temperature_2m, precipitation_probability, relativehumidity_2m
```

**SAR-relevant weather codes (WMO):**
- 0: Clear sky
- 1–3: Mainly clear, partly cloudy, overcast
- 45–48: Fog
- 51–55: Drizzle
- 61–65: Rain
- 71–77: Snow
- 80–82: Rain showers
- 95–99: Thunderstorm

**Quick weather assessment for search:**
1. Is it dark? → Thermal tools, night search windows
2. Is temp <40°F or >85°F? → Contract radius, adjust active hours
3. Wind >15mph? → Scent work less effective, ground tracks more visible
4. Precipitation expected? → Pet stationary, intensive local search
5. Clear, calm, mild? → Optimal conditions — maximize search effort

---

## Seasonal Considerations

| Season | Key Factor | Primary Concern |
|--------|-----------|----------------|
| Spring | Warming temps, rain, flooding | Creek beds, drainage areas |
| Summer | Heat, storms | Water sources, dawn/dusk scheduling |
| Fall | Hunting season, cooling temps | Hunters may mistake pet for game |
| Winter | Cold, snow, ice | HVAC vents, heated structures, frozen water |

---

## Putting It Together: Weather Decision Tree

```
Check current temp:
├─ <40°F → Contract radius 60-80%. Check heated structures.
├─ 40-75°F → Normal conditions. Proceed as planned.
└─ >75°F → Check overnight windows. Target dawn/dusk.
                ↓
Check wind speed:
├─ <10mph → Scent work viable. Normal search.
├─ 10-20mph → Ground tracks visible. Scent-limited.
└─ >20mph → Scent work suspended. Visual/thermal only.
                ↓
Check precipitation:
├─ None → Optimal for search effort.
├─ Light rain → Pet stationary. Intensive local.
└─ Heavy rain → Shelter search only. Stand down wide search.
                ↓
Check daylight:
├─ Day → Visual search primary.
└─ Night → Thermal. Dawn/dusk windows optimal.
```

---

*Source: Open-Meteo API docs (free, no key), NWS behavioral studies. For Mission Reunite intel use.*

# Terrain and Environmental Features

**Purpose:** Identify the highest-probability corridors and search zones based on geography, land cover, and linear features that influence how lost pets move.

---

## Linear Features: The Primary Movement Corridors

Lost pets follow linear features instinctively — they provide cover, navigational reference, and a sense of security. **Always prioritize linear features in early-phase searches.**

### Ranked by Movement Probability

| Feature | Why Pets Use It | Search Priority |
|---------|-----------------|-----------------|
| Creek beds / Drainage ditches | Water, cover, lowest path of resistance | **HIGHEST** |
| Fence lines | Familiar scent, boundary guidance | **HIGH** |
| Wood lines / Tree lines | Shade, concealment, animal trails | **HIGH** |
| Roads / Paved paths | Easy running, visual reference | **MEDIUM** |
| Railroad tracks | Flat, open, fast travel | **MEDIUM** |
| Hedgerows | Dense cover, food sources | **HIGH** |
| Irrigation ditches | Water, green vegetation | **HIGH** |
| Power line corridors | Cleared paths through cover | **MEDIUM** |

**Key insight:** Pets rarely cut across open terrain when a linear feature is available. Model their movement along these corridors, not as a radial spread from the LKP.

---

## Cover Types and Shelter Quality

Pets seek shelter based on availability and thermal properties. High-quality cover = high probability of finding a stationary pet.

### Excellent Cover (Search First)
- **Under decks / porches** — dark, enclosed, protected from weather
- **Drainage pipes / Culverts** — enclosed, warm, secure
- **Dense evergreen thickets** — year-round cover
- **Underground structures** — sheds, barns, storm cellars
- **Crawl spaces** — check for vent holes and gaps

### Good Cover
- **Wood piles** — stacked logs provide insulated voids
- **Brush piles** — fallen branches, leaf litter
- **Garages / Open sheds** — especially if food is stored
- **Compost bins** — warmth from decomposition

### Marginal Cover
- **Open backyards** — visible but exposed
- **Porch furniture** — under chairs, tables
- **Deciduous shrubs (summer)** — partial concealment

---

## Creek Beds and Drainage: The #1 Search Priority

Creek beds are the single highest-probability corridor in most terrain. Why:

1. **Water** — primary survival need
2. **Lowest path** — natural drainage concentrates movement
3. **Cover** — banks, vegetation, overhangs provide shelter
4. **Animal trails** — wildlife uses creek beds as highways
5. **Scent pooling** — scents concentrate and persist along water

**How to model movement along creek beds:**
- Start at the LKP. Look for the nearest creek/drainage.
- Trace both upstream AND downstream — pet may have gone either direction.
- Check the inside of creek bends (where the bank is lowest and most sheltered).
- Check under bridges and culverts — common hiding spots.
- Look for fresh tracks in exposed mud/sand banks.

**Distance model for creek-corridor movement:**
- Pets can travel 2–4× faster along creek beds than across terrain
- After 24 hours, a pet may be 2–3 miles from LKP if following a creek corridor
- Adjust scatter radius upward by 1.5–2× if significant creek/drainage network exists

---

## Elevation and Topographic Cues

### Descending vs. Ascending
- Pets generally move DOWNHILL (toward water, lower energy expenditure)
- In hilly terrain: check lower elevations first
- Valley floors and drainages: highest concentration corridor

### Ridge Lines
- Some pets with strong homing instinct will follow ridge lines (easier navigation)
- High vantage points: occasionally used by cats for territory assessment
- Ridge lines provide fast travel corridors — can extend scatter radius significantly

---

## Land Cover Types

### Urban / Suburban
- **Movement:** Grid-like along streets, sidewalks, fence lines
- **Primary corridors:** Sidewalks, alleyways, yard perimeters
- **Key hiding spots:** Under parked cars, porches, garages, HVAC enclosures
- **Radius:** Contracts due to barriers (fences, roads, buildings)
- **Probability model:** Elliptical, elongated along street grid

### Open Field / Agricultural
- **Movement:** Straight-line panic flight across open ground
- **Primary corridors:** Field edges, irrigation lines, fence lines
- **Key hiding spots:** Equipment storage, barns, wood lots at field edges
- **Radius:** Expanded — pet may have run far before stopping
- **Probability model:** Radial from LKP, contracted at field centers

### Forested
- **Movement:** Follows animal trails, creek beds, game paths
- **Primary corridors:** Game trails, dry creek beds, ridge lines
- **Key hiding spots:** Hollow trees, fallen logs, dense underbrush
- **Radius:** Normal to contracted — cover is abundant, movement slower
- **Probability model:** Along trail network, not radial

### Wetlands / Marsh
- **Movement:** Avoids unless necessary (water is primary goal)
- **Primary corridors:** Edge of wetland, service roads, elevated ground
- **Key hiding spots:** Elevated dry ground, culverts, road margins
- **Note:** Dangerous — pets can drown in marshes. Check edges carefully.

---

## Human-Made Structures

### Garages
- Most common found-location for lost pets in suburban areas
- Often left open or have gaps at bottom of door
- Check inside, behind/under stored items, near water heaters

### Sheds / Outbuildings
- Often unchecked for days
- Provide dark, enclosed shelter
- Check under footboards, in corners, behind tools

### HVAC Units / AC Enclosures
- Warm output = attracts cold pets
- Dark enclosed space beneath
- **CRITICAL for cats in cold weather**

### Dog Houses / Kennels
- Familiar scent — pet may try to return to home kennel
- Check neighbor's dog houses within 1/2 mile

### Deck/Porch Underneath
- Primary hiding location for cats
- May need to crawl under to check
- Gaps in lattice = entry points

---

## Transportation Corridors

### Roads
- Pets are attracted to roads (flat, easy travel)
- HIGH MORTALITY RISK — check for roadkill matches
- After 24+ hours, check road margins (a pet walking along shoulder may be reported)
- Look for pet in ditches — they avoid the road surface when possible

### Railroad Tracks
- Flat, straight, easy running
- Pets may travel long distances along tracks
- **Safety hazard:** Check with railroad authority before searching tracks

---

## Using OSM/Terrain Data for Search Planning

When you have an LKP, use the Maps skill to query OSM for:

1. **Nearest water features:** `nearby LAT LON water_point --radius 1000` AND `nearby LAT LON canal --radius 1000`
2. **Wood lines / tree cover:** `bbox S W N E wood --limit 20` or `nearby LAT LON forest --radius 1500`
3. **Fence lines:** OSM has `barrier=fence` — useful for modeling movement constraints
4. **Built structures:** Sheds, barns, garages near LKP — `nearby LAT LON shed --radius 500`
5. **Creek/stream beds:** `nearby LAT LON stream --radius 2000`

---

## Probability Zone Mapping

For each case, generate a terrain-adjusted probability map:

```
Zone 1 (40%): Linear features within 1/2 mile of LKP
  → Creek beds, fence lines, wood lines, road edges

Zone 2 (35%): Good cover within 1 mile of LKP
  → Under structures, dense brush, drainage, structures

Zone 3 (20%): Extended corridors + elevated terrain
  → 1-3 miles along creek beds, trails, roads

Zone 4 (5%): Everything else
  → Low priority unless evidence points further
```

---

## Urban vs. Rural Terrain Adjustments

| Factor | Urban | Suburban | Rural |
|--------|-------|----------|-------|
| Primary corridor | Streets, alleys | Yard perimeters, parks | Creek beds, fence lines, trails |
| Shelter density | Very high | High | Low |
| Radius contraction | Strong (barriers) | Moderate | Minimal |
| Creek importance | Lower (fire hydrants, etc.) | Medium | **Critical** |
| Open field crossing | Rare | Occasional | Common |
| Risk factor | Traffic | Traffic, more people | Distance, terrain hazards |

---

*Source: OSM landscape analysis, University of Georgia Lost Pet Study, NCPWR terrain modeling. For Mission Reunite intel use.*

# Scatter Radius Reference

**Purpose:** Estimate the probability envelope — how far a lost pet can travel from the Last Known Point (LKP) based on species, terrain, time, and conditions.

---

## Core Principle

Lost pets don't scatter randomly. They move in a recognizable pattern: a strong central tendency (they want to return home) combined with environmental constraints (terrain, weather, roads). The probability envelope is roughly **elliptical**, elongated along linear features (roads, fence lines, creek beds) that provide cover and navigational cues.

---

## Distance Models by Species

### Dogs

| Size | First Hour | 6 Hours | 24 Hours | 72 Hours |
|------|-----------|---------|----------|----------|
| Small (<20 lb) | 0.1–0.3 mi | 0.3–0.7 mi | 0.5–1.5 mi | 1–2 mi |
| Medium (20–60 lb) | 0.2–0.5 mi | 0.5–1.5 mi | 1–2.5 mi | 2–4 mi |
| Large (60–100 lb) | 0.3–0.7 mi | 1–2.5 mi | 2–4 mi | 3–6 mi |
| Giant (>100 lb) | 0.4–1 mi | 1.5–3 mi | 3–5 mi | 5–8 mi |

**Correction factors (multiply base distance):**
- **Flight risk** (cat-reactive, noise-phobic, injured): ×1.5–2.0
- **High motivation to return** (strong bond, working dog): ×0.7
- **Familiar territory**: ×0.5–0.7

### Cats

| Type | First Hour | 6 Hours | 24 Hours | 72 Hours | 1 Week |
|------|-----------|---------|----------|----------|--------|
| Indoor-only | 0.05–0.2 mi | 0.1–0.4 mi | 0.2–0.6 mi | 0.3–1 mi | 0.5–2 mi |
| Outdoor-access | 0.1–0.4 mi | 0.3–1 mi | 0.5–2 mi | 1–3 mi | 2–5 mi |
| Feral | 0.2–0.6 mi | 0.5–2 mi | 1–3 mi | 2–5 mi | 3–8 mi |

**Key insight:** Most lost cats are found within 1/4 mile of the LKP, even after days. They seek dense cover and stay motionless when scared. DON'T search a wide radius first — search the immediate area thoroughly.

---

## Environmental Multipliers

Apply to the base distance estimate:

| Factor | Effect |
|--------|--------|
| Darkness / Night | Reduces movement by 60–80%. Small pets freeze. |
| Temp <40°F | Movement near zero for small dogs. Cats hunker down. |
| Temp >85°F | Movement reduced midday; peaks at dawn/dusk |
| Rain / Precipitation | Movement drops 50–70%. Seek shelter immediately. |
| Wind >20 mph | Disorientation; reduce radius 30–40% |
| Snow on ground | Cats cannot track-scent; reduce mobility 50% |
| Urban / High traffic | Pets avoid roads; envelope flattens |
| Familiar neighborhood | Radius ×0.5 vs. unfamiliar territory |
| Unfenced yard | Escape = immediate wide scatter |

---

## Phase-Based Scatter

### Phase 1: IMMEDIATE (0–2 hours)
**Behavior:** Panicked flight. High adrenaline. Pets run fast and straight along linear features (fences, roads, water edges) until exhausted or they find a hiding spot.

**Probability envelope:** Narrows along the direction of initial flight. Initial heading tends to follow roads or open lines of sight.

**Search priority:** 1-mile radius, linear features first (fence lines, wood lines, creek beds, roads).

### Phase 2: DENNING (2–24 hours)
**Behavior:** Exhaustion sets in. Pet seeks shelter — under decks, in dense brush, drainage pipes, abandoned structures. Becomes increasingly inactive. May respond to owner's voice/call.

**Probability envelope:** Expands but centers around the first good cover found. May not move for hours.

**Search priority:** Intensive grid search within 1/2 mile. Focus on hiding cover. Leave owner's worn clothing at LKP (familiar scent).

### Phase 3: EXPLORATION (24–72 hours)
**Behavior:** Hunger and thirst begin driving movement. Pet may circle outward during dawn/dusk cooler hours. Still gravitates toward cover and linear features.

**Probability envelope:** Ellipse expands. Wandering may follow scent trails of other animals or food sources.

**Search priority:** Expand to full estimated radius. Check known animal feeding locations (feeding stations, bird feeders, gardens). Leave food at LKP.

### Phase 4: SURVIVAL (72+ hours)
**Behavior:** Learned helplessness may set in. May become more approachable OR more feral depending on pet history. Movement patterns become less predictable.

**Probability envelope:** Reaches maximum. May have traveled to a location with consistent food/shelter source.

**Search priority:** Broader radius. Check trap locations. Scent-trailing dogs effective. Social media/door-to-door most effective at this stage.

---

## Elliptical Probability Zones

For search planning, model the scatter as concentric elliptical zones:

```
Zone 1 (HIGH):  0–30% of max radius = 40% probability
Zone 2 (MED):   30–60% of max radius = 35% probability
Zone 3 (LOW):   60–100% of max radius = 20% probability
Zone 4 (FAR):   Beyond max = 5% probability
```

**Elongation factor:** 1.5–2.5× in the direction of linear features (roads, creeks).

---

## Last Known Point (LKP) Uncertainty

The LKP is rarely exact. Account for uncertainty in the starting point:

- **Owner last saw pet X minutes ago** → add X minutes of travel to the radius
- **Doorbell camera last motion** → use camera location as LKP with ~100ft uncertainty
- **Witness saw it running** → initial heading inference from witness direction
- **No confirmed LKP** → start search at most likely exit point (nearest gate, fence gap, door)

---

## Quick Reference: Typical Max Radius

| Pet Type | Urban (mi) | Suburban (mi) | Rural (mi) |
|----------|-----------|--------------|-----------|
| Small dog | 0.5 | 1.5 | 2 |
| Medium dog | 1 | 2.5 | 4 |
| Large dog | 1.5 | 3 | 6 |
| Cat (indoor) | 0.25 | 0.75 | 1.5 |
| Cat (outdoor) | 0.5 | 2 | 4 |

---

*Source: Adapted from SAR canine/feline behavior research, University of Arizona Lost Pet Studies, NCPWR data. Filed for Mission Reunite intel use.*

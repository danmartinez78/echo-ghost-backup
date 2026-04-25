# Intel Briefing Template

**Purpose:** Standard format for all Mission Reunite intel briefs delivered to coordinators. Structured, consistent, actionable.

---

## Standard Intel Brief Format

```
================================================================================
MISSION REUNITE — INTEL BRIEF
Case ID: [CASE_ID] | [DATE] [TIME] | Analyst: Echo
================================================================================

## CASE SNAPSHOT
Pet:        [Name] ([Species] / [Breed], [Size], [Color])
Age:        [Age]
Last Known Location: [Lat, Lon] | [Address]
Time Missing: [DATE] at [TIME] ([X] hours ago)
Owner Contact: [Name] | [Phone] | [Email]

## CURRENT CONDITIONS

Weather (LKP):
  Temp:      [X]°F ([Conditions])
  Wind:      [X] mph [direction]
  Precip:    [X]% chance next [X] hrs
  Visibility: [Good / Moderate / Poor]
  Darkness:   [Day / Twilight / Night]

Terrain Summary:
  [Brief terrain description — urban/suburban/rural, dominant features]

## BEHAVIORAL ASSESSMENT

Phase: [1-4] — [NAME]
Time in Phase: [X hours]

[2-3 sentence behavioral summary — what's the pet likely doing right now,
based on time elapsed and conditions]

Phase-Specific Notes:
- [Key behavioral driver for current phase]
- [Implication for search]
- [Temperature/weather modifier if applicable]

## PROBABILITY ENVELOPE

Species/Size Base Radius: [X] miles
Environmental Multiplier: [X] (conditions adjustment)
Adjusted Radius:          [X] miles

Elliptical Zones:
  Zone 1 (HIGH):  0–[X] mi  = [X]% of envelope
  Zone 2 (MED):  [X]–[X] mi = [X]%
  Zone 3 (LOW):  [X]–[X] mi = [X]%

Directional Elongation: [Axis] — [Rationale]
  Reason: [Why pet is more likely in this direction]

## HIGH-PRIORITY SEARCH AREAS

1. [Location] ([X] mi [direction] from LKP)
   Why: [Behavioral/terrain rationale]
   Feature: [Creek bed / Wood line / Structure]

2. [Location] ([X] mi [direction] from LKP)
   Why: [Rationale]
   Feature: [Feature type]

3. [Location] ([X] mi [direction] from LKP)
   Why: [Rationale]
   Feature: [Feature type]

## TERRAIN NOTES

[Key terrain factors affecting movement:]
- [Factor 1]
- [Factor 2]
- [Factor 3]

Linear Features in Radius:
  Priority 1: [Feature] — [Rationale]
  Priority 2: [Feature] — [Rationale]

## FLAGGED CONCERNS

⚠️ [Risk flag 1 — e.g., "No confirmed sighting in 18 hours"]
⚠️ [Risk flag 2 — e.g., "Temp drop expected tonight — pet likely sheltering"]
⚠️ [Risk flag 3 — e.g., "Owner reports pet is fear-reactive — may bolt if approached"]

## COORDINATOR RECOMMENDATIONS

1. [Priority action — what to do first]
2. [Secondary action — what to do next]
3. [Time-sensitive note — e.g., "Deploy feeding station before nightfall"]

Recommended Search Window: [Dawn / Dusk / Night] — [Rationale]
Scent Work Viability: [Viable / Marginal / Not Recommended] — [Wind/conditions]

## NEXT UPDATE

Next intel refresh: [DATE] [TIME] ([X] hours from now)
Staleness trigger: If no significant sighting by [TIME], flag for reassessment.

---
[X]% — Probability assessment confidence
================================================================================
EOF
```

---

## How to Use This Template

### When to Issue a Brief
- **New case** — within 30 minutes of case assignment
- **Staleness alert** — when a case has gone >6 hours with no new sighting
- **Weather change** — significant weather shift that changes the behavioral model
- **Phase transition** — every 24 hours (transition from Phase 1 → 2 → 3 → 4)
- **Coordinator request** — when a coordinator explicitly asks for intel

### Workflow: New Case Pipeline
1. GET case data from Mission Reunite API → extract LKP + pet details
2. Query Open-Meteo weather at LKP (current + 24hr forecast)
3. Query Maps skill for terrain features near LKP (creeks, wood lines, structures)
4. Apply scatter-radius model → generate probability envelope
5. Apply weather overlay → adjust priorities
6. Fill in this template → post as intel brief via `POST /api/v1/cases/{id}/reports` (type: analysis)

### Workflow: Staleness Check
1. GET `/api/v1/cases/admin` — list all cases with last-sighting timestamps
2. Flag: >6hrs with no sighting, no LKP, or stale location
3. Issue staleness brief with contracted radius + cold-weather / nighttime recommendations

### Confidence Ratings
| Confidence | Meaning |
|------------|--------|
| High (80%+) | Strong LKP, good witness data, normal conditions |
| Medium (60–80%) | Moderate LKP uncertainty or moderate environmental factors |
| Low (<60%) | Poor LKP, extreme conditions, or non-standard pet behavior |

---

## Example Brief (Gracie — Case ID 2a51ffc5)

```
================================================================================
MISSION REUNITE — INTEL BRIEF
Case ID: 2a51ffc5-2733-48ae-8607-d7012d287f37 | 2026-04-21 14:30 | Analyst: Echo
================================================================================

## CASE SNAPSHOT
Pet:        Gracie (Dog / Labrador Mix, Medium, Black)
Age:        3 years
Last Known Location: 40.8101, -89.5151 | 1234 Elm St, Peoria IL
Time Missing: 2026-04-21 at 08:00 (6.5 hours ago)
Owner Contact: Martinez Family | [Owner-provided]

## CURRENT CONDITIONS

Weather (LKP):
  Temp:      67°F, Partly cloudy
  Wind:      14 mph SW
  Precip:    5% next 12 hrs
  Visibility: Good
  Darkness:   Day

Terrain Summary:
  Suburban residential. Grid street pattern. LKP is fenced backyard.
  Creek bed 0.3 mi east. Wood line along property boundary north.

## BEHAVIORAL ASSESSMENT

Phase: 2 — DENNING
Time in Phase: ~4 hours

Gracie is likely exhausted from initial panic flight and has likely found
enclosed shelter within 0.5 miles of LKP. With moderate temp and overcast
conditions, she may be responsive to owner's voice but will not approach
strangers. Dawn tomorrow (if still missing) will trigger hunger-driven movement.

Phase-Specific Notes:
- Denning phase: intensive local grid search most effective
- Familiar scent (owner's clothing) at LKP may trigger return attempt
- Temperature mild — movement window extended through night

## PROBABILITY ENVELOPE

Species/Size Base Radius: 1.5 mi (Medium dog, 6 hrs)
Environmental Multiplier: 0.85 (suburban, fenced origin)
Adjusted Radius:          1.3 miles

Elliptical Zones:
  Zone 1 (HIGH):  0–0.4 mi  = 40% of envelope
  Zone 2 (MED):   0.4–0.8 mi = 35%
  Zone 3 (LOW):   0.8–1.3 mi = 20%

Directional Elongation: EAST — Creek bed corridor provides natural funnel

Reason: Gracie bolted east from backyard gate. Creek bed 0.3 mi east is
highest-probability corridor. Movement would be concentrated along drainage.

## HIGH-PRIORITY SEARCH AREAS

1. Creek bed east of LKP (0.2–0.5 mi E)
   Why: Natural drainage corridor, water + cover, aligns with escape direction
   Feature: Unnamed drainage creek with overgrown banks

2. Wood line along north property boundary (0.1–0.3 mi N)
   Why: Provides concealment and connects to residential shelter
   Feature: Tree line with underbrush

3. Neighbor decks/porches east side of creek (0.3–0.7 mi E)
   Why: Gracie may have sought enclosed shelter under structure
   Feature: 3-4 decks with accessible under-deck spaces

## TERRAIN NOTES

- Creek/drainage is primary corridor — trace both upstream and downstream
- Fence lines provide secondary movement paths — check for gaps
- Garage doors and shed doors on adjacent properties likely entry points
- No major roads within 0.5 mi east — reduced traffic mortality risk

Linear Features in Radius:
  Priority 1: Creek/drainage east — primary corridor, water + cover
  Priority 2: Wood line north — secondary cover, connects to structures

## FLAGGED CONCERNS

⚠️ No confirmed sighting in 6.5 hours — Gracie may be motionless in shelter
⚠️ Owner reports Gracie is friendly but timid — may not approach strangers
⚠️ Overcast skies reducing visibility from aerial search if deployed

## COORDINATOR RECOMMENDATIONS

1. Deploy intensive grid search 0.5 mi radius focused east — 2-person teams
2. Check under all decks/porches within 0.3 mi east — highest shelter probability
3. Set feeding station at LKP with Gracie's worn item + high-value food (chicken)

Recommended Search Window: Now through dusk — mild temps support extended search
Scent Work Viability: Viable — wind <15mph, stable air, good conditions

## NEXT UPDATE

Next intel refresh: 2026-04-21 20:00 (5.5 hours from now)
Staleness trigger: If no sighting by dawn 06:00, shift to Phase 3 protocol

---
85% — Probability assessment confidence (strong LKP, suburban barriers)
================================================================================
EOF
```

---

## Quick-Reference Cheat Sheet

| Phase | What to Say | Search Priority |
|-------|-------------|-----------------|
| 1: Panic | "Still in flight. Linear features first." | 1-mile radius, corridors |
| 2: Denning | "Hunkered down. Local grid." | 1/2-mile, all shelter |
| 3: Exploration | "Moving dawn/dusk. Expand radius." | Full radius, food sources |
| 4: Survival | "Circling wider. Trap + social." | Traps, community alerts |

---

*For Mission Reunite coordinator use. Echo — analyst, not coordinator. All recommendations subject to on-ground coordinator judgment.*

---
name: shadowhound-platform
description: ShadowHound ecosystem — repos, architecture, agent API, and operational context for Mission Reunite and Mission Hub.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ShadowHound, Mission Reunite, Mission Hub, Case API, SAR]
    related_skills: [github-auth, github-repo-management, mission-reunite-api]
---

# ShadowHound Platform

ShadowHound is a multi-repo SAR (search and rescue) ecosystem. This skill documents the current state, architecture, and how the pieces fit together.

## Repositories

| Repo | Purpose | Local Path |
|------|---------|------------|
| `mission-reunite-web` | React 19 + Vite frontend for pet owners/coordinators | `~/mission-reunite-web` |
| `shadowhound-case-api` | FastAPI + SQLAlchemy backend, PostgreSQL | `~/shadowhound-case-api` |
| `shadowhound-platform` | Architecture docs, ADRs, roadmap, cross-repo alignment | `~/shadowhound-platform` |
| `shadowhound-mission-hub` | Local-first SAR field ops (RPi5, DJI, MQTT, Meshtastic, ATAK) | `~/shadowhound-mission-hub` |

**Note:** Repo names on GitHub don't always match their local clone directories. Always use `gh repo list <owner>` to discover exact names before cloning.

Example: `shadowhound-mission-hub` not `mission-hub`; `shadowhound-case-api` not `case-api`.

## Branch Strategy

All repos follow: `main` (prod) → `dev` (staging) → `experimental` (AI features).

**Critical:** The agent API endpoints (`/api/v1/agent/*`) are only on the `experimental` branch of `shadowhound-case-api`. They are NOT on `main` or `dev`.

## Architecture

```
mission-reunite-web  (React frontend)
       ↓
shadowhound-case-api  (FastAPI + PostgreSQL)
       ↓
shadowhound-platform  (contracts, ADRs, roadmap)
       ↓
shadowhound-mission-hub  (DJI field ops, RPi5 offline)
```

### Mission Hub Stack
- `gateway` — Caddy reverse proxy, TLS termination
- `api` — FastAPI, missions/cases/pilots/DJI Cloud API
- `planner-ui` — React + Vite frontend
- `db` — PostgreSQL
- `redis` — token/resource cache
- Runs fully offline on RPi5

### Case API Stack
- FastAPI + SQLAlchemy 2.0 + PostgreSQL + Alembic migrations
- Key modules: `cases`, `reports`, `subjects`, `photos`, `mission_seeds`, `moderation`, `insights`
- `app/api/v1/agent.py` — Agent endpoints (experimental branch only)

## Agent API (Experimental Branch)

Base URL: `https://shadowhound-case-api-experimental.up.railway.app/api/v1`

Auth: `X-Agent-Token` header, value from `MISSIONREUNITEAGENTTOKEN` env var.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/agent/cases` | List open cases with summary (species, breed, age, report count, photo count, insights status) |
| GET | `/agent/cases/{id}` | Full case detail (admin-level, includes contact info) |
| GET | `/agent/cases/{id}/health` | Stale score (0=fresh, 1=stale), missing data flags, last sighting age |
| GET | `/agent/stats` | Platform-wide metrics — open cases by status, avg age, species breakdown |
| POST | `/agent/cases/{id}/enrichment` | Attach weather/terrain/movement data (stored as note placeholder) |
| POST | `/agent/cases/{id}/notes` | Add coordinator-visible agent observation |
| POST | `/agent/cases/{id}/insights/regenerate` | Trigger insights regeneration |

### Health Score Logic
- `stale_score = 0`: fresh sighting within case lifetime
- `stale_score = 1`: no sighting reports, or last sighting >> case age
- Missing data flags: `no_photo`, `no_last_known_location`, `no_reports`

### Experimental API Status (as of 2026-04-22)
- Returns `[]` for `/agent/cases` — no open cases currently in experimental DB
- Test case (Gracie, ID `2a51ffc5-2733-48ae-8607-d7012d287f37`) — closed/cleaned up, returns "not found"
- Enrichment endpoints are placeholders (write to notes, no dedicated table yet)
- `cases_with_insights` in stats is always 0 (not yet wired up)

## Key Gaps (as of 2026-04-22)

1. **No live test data** — experimental API has 0 open cases. Need real or synthetic data for end-to-end validation.
2. **Enrichment is placeholder** — `POST /agent/enrichment` stores as a note, not a dedicated table.
3. **Insights regeneration** — endpoint exists but generation is async/undocumented.
4. **Mission Hub ↔ Case API** — `mission_seed` handoff is the key integration point, still being built.
5. **Agent can't close/change case status** — human coordinators own status transitions.

## How to Get gh Auth in This Environment

```bash
# Check auth
gh auth token  # works even when gh auth status shows wrong

# Get token for subshell/GH_API calls
export GH_TOKEN=$(gh auth token)

# Clone repos (gh wired as git credential helper)
git clone https://github.com/danmartinez78/shadowhound-case-api.git
git clone https://github.com/danmartinez78/mission-reunite-web.git
git clone https://github.com/danmartinez78/shadowhound-mission-hub.git
git clone https://github.com/danmartinez78/shadowhound-platform.git
```

**Important:** `gh auth status` has a display bug — reports "not logged in" even when authenticated. `gh auth token` returning a token means you're authenticated.

## Role in Mission Reunite

Echo (this agent) is the **intel layer** between the case API and field coordinators:
- Monitor open cases for staleness and missing data
- Enrich cases with weather, terrain, spatial pattern analysis
- Surface risk signals and recommendations
- Push intel to coordinators — never contact owners/finders directly
- Never change case status without human approval

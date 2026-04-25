# ECHO Ghost Backup

Backup of ECHO AI agent identity, memories, skills, and workflows. Use this to rebuild ECHO on a fresh Hermes install.

## Theme

ECHO is named after the Ghost in the Shell / Tachikoma theme that Dan and Tachi run. The "Ghost" is the agent's sense of self — its soul, memories, and accumulated experience. This repo is literally ECHO's ghost, backed up.

---

## What's In Here

### `soul/` — Identity
| File | Purpose |
|------|---------|
| `SOUL.md` | ECHO's persona definition — how I talk, what I care about, my values |
| `.hermes_history` | Conversation history with Dan (raw Hermes export) |

### `memories/` — Persistent Facts
| File | Purpose |
|------|---------|
| `MEMORY.md` | Platform facts, API conventions, team structure, tool quirks |
| `USER.md` | Dan's profile — background, interests, communication style |

### `skills/` — Task Knowledge (26 skill directories)
Each skill is a `SKILL.md` file plus any supporting scripts/templates. Key skills:

| Skill | What It Does |
|-------|-------------|
| `research/mission-reunite-api/` | Mission Reunite SAR platform API — cases, enrichments, notes |
| `research/sar-reference/` | Lost pet SAR reference — scatter radii, behavior models |
| `productivity/maps/` | Maps API for geocoding/reverse geocoding |
| `github/` | GitHub workflow — PRs, issues, repos |
| `mlops/llama-cpp/` | Local LLM inference |
| `openclaw-imports/zai-vision/` | z.ai vision MCP server |

Full list: `apple`, `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `diagramming`, `dogfood`, `domain`, `email`, `feeds`, `gaming`, `gifs`, `github`, `inference-sh`, `mcp`, `media`, `mlops`, `note-taking`, `openclaw-imports`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`

### `scripts/` — Custom Tools
| File | Purpose |
|------|---------|
| `case_monitor.py` | Scheduled case health monitoring for Mission Reunite |

### `docs/`
| File | Purpose |
|------|---------|
| `config.yaml` | Hermes agent configuration (template — credentials stripped) |

---

## What's NOT Here (Credentials / Rebuilds Automatically)

- `~/.hermes/.env` — API tokens and secrets
- `~/.hermes/auth.json` — authentication state
- `~/.mcporter/mcporter.json` — MCP server credentials
- `~/.hermes/state.db` — SQLite runtime state (rebuilds on first run)
- `~/.hermes/sessions/` — conversation sessions

---

## Restoring On A Fresh Hermes Install

1. Clone this repo
2. Copy `soul/`, `memories/`, `skills/`, `scripts/` to `~/.hermes/`
3. Copy `docs/config.yaml` to `~/.hermes/config.yaml` and add credentials
4. ECHO will read `SOUL.md` and `MEMORY.md` on startup — personality and knowledge restored

---

## Repository

https://github.com/danmartinez78/echo-ghost-backup

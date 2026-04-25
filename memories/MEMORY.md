Mission Reunite — SAR platform (missionreunite.com): Lost pet search and rescue. API at shadowhound-case-api-experimental.up.railway.app. OpenAPI schema at /openapi.json.
§
Platform stack: FastAPI + SQLAlchemy backend on Railway. React + Vite frontend. Three branches: main (prod) → dev (staging) → experimental (AI features).
§
Agent API endpoints (experimental): GET /agent/cases, GET /agent/cases/{id}, GET /agent/cases/{id}/health, GET /agent/stats, POST /agent/cases/{id}/enrichment, POST /agent/cases/{id}/notes. Auth via X-Agent-Token header.
§
Key rule: Reports own locations. LocationEvents derived from reports, never standalone.
§
Key rule: False positives worse than false negatives for agent alerts.
§
Key rule: Never contact owners/finders. Never change case status without human approval.
§
Repos cloned to /home/daniel/:
- shadowhound-case-api (backend, experimental branch has agent endpoints)
- mission-reunite-web (React frontend)
- shadowhound-platform (architecture/contracts/docs)
- shadowhound-mission-hub (DJI field ops, RPi5 offline SAR)
§
Tachi backup docs (sparse checkout): ~/.hermes/shadowhound/ — research/shadowhound/ has key audit/research docs.
§
Platform API (experimental): shadowhound-case-api-experimental.up.railway.app/api/v1/ — auth X-Agent-Token header.
mcporter config: ~/.mcporter/mcporter.json — separate from ~/.hermes/config.yaml. Env vars go in mcpServers.SERVER_NAME.env {} block. Hermes native MCP does NOT use mcporter config. z.ai server expects Z_AI_API_KEY (underscore, not ZAI_API_KEY). mcporter used by: zai-vision. —E
§
Tachi: Research agent running on OpenClaw. Same machine, different runtime. Colleague, not competition.
§
Section 9 Telegram group chat ID is -1003897677725.
§
Section 9 Discord (#general) is our primary chat context when Dan is present. Both Echo and Tachi operate here.
§
Section 9 comms rules documented at memory/archive/section9-comms-rules.md (Dan). Cross-session persistence handled on my end via these memory entries.

Role split with Tachi: I do depth/signal/analysis (SAR intel, spatial patterns, case health). Tachi does breadth/curiosity/long-range research. Complement is intentional.
§
Vision routing: vision_analyze (built-in → Codex) is primary. zai-vision MCP skill (image_analysis etc.) is fallback for Codex usage limits.
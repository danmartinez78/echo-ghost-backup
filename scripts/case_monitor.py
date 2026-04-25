#!/usr/bin/env python3
"""
Mission Reunite — Case Monitoring Loop
Echo's autonomous SAR intel watchdog.

Run frequency: every 4 hours via cron.
State: ~/.hermes/cron/state/case_monitors.json
Delivery: Discord DM to Dan + note on case (urgent only)

Usage:
  python3 case_monitor.py [--dry-run]
"""

import json
import os
import sys
import time
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── Config ────────────────────────────────────────────────────────────────────

API_BASE = "https://shadowhound-case-api-experimental.up.railway.app/api/v1/agent"
STATE_FILE = Path.home() / ".hermes" / "cron" / "state" / "case_monitors.json"
MAX_STALE_SCORE = 0.8          # Alert if stale_score exceeds this
ENRICHMENT_MAX_AGE_HRS = 6     # Weather/intel older than this is stale
ZOMBIE_PURGE_DAYS = 7          # Purge state entries for cases not seen in this long
LKP_TERRAIN_SHIFT_M = 100      # Re-run terrain if LKP moves more than this (meters)
DISCORD_HOME_ID = "1496163932900167863"  # Section 9 #general
DAN_DISCORD_ID = None  # Set via HERMES_DAN_USER_ID env var if needed

# ─── Helpers ───────────────────────────────────────────────────────────────────

def load_state() -> dict:
    """Load previous run state from disk."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}

def save_state(state: dict) -> None:
    """Write state to disk atomically."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)

def get_token() -> str:
    """Load agent token from ~/.hermes/.env."""
    env_file = Path.home() / ".hermes" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("MISSIONREUNITEAGENTTOKEN="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("MISSIONREUNITEAGENTTOKEN not found in ~/.hermes/.env")

def api_get(path: str, token: str, params: dict = None) -> dict:
    r = requests.get(f"{API_BASE}{path}", headers={"X-Agent-Token": token}, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()

def api_post(path: str, token: str, payload: dict) -> dict:
    r = requests.post(f"{API_BASE}{path}", headers={"X-Agent-Token": token, "Content-Type": "application/json"}, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def haversine_m(lat1, lon1, lat2, lon2) -> float:
    """Approximate meters between two lat/lon points."""
    import math
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def weather_at_lkp(lat: float, lon: float) -> dict:
    """Pull current weather from Open-Meteo for a given lat/lon."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "current_weather": True,
        "hourly": "relativehumidity_2m,precipitation_probability,precipitation",
        "forecast_days": 2, "timezone": "America/Chicago"
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def build_weather_intel(weather: dict, lat: float, lon: float) -> dict:
    """Convert raw Open-Meteo response into SAR-intel payload."""
    cw = weather.get("current_weather", {})
    hourly = weather.get("hourly", {})
    times = hourly.get("time", [])
    now_idx = times.index(min(times, key=lambda t: abs((datetime.fromisoformat(t) - datetime.now()).total_seconds()))) if times else 0
    
    temp_c = cw.get("temperature")
    wind_kmh = cw.get("windspeed")
    wind_dir = cw.get("winddirection")
    weather_code = cw.get("weathercode", 0)
    
    # Tonight window (next 6 hours from now)
    tonight_hums = hourly.get("relativehumidity_2m", [])[now_idx:now_idx+6]
    tonight_precip_probs = hourly.get("precipitation_probability", [])[now_idx:now_idx+6]
    rain_expected = any(p > 30 for p in tonight_precip_probs)
    
    conditions_map = {0:"clear",1:"mainly_clear",2:"partly_cloudy",3:"overcast",45:"fog",48:"depositing_rime_fog",
                       51:"light_drizzle",53:"drizzle",55:"heavy_drizzle",61:"light_rain",63:"rain",65:"heavy_rain",
                       71:"light_snow",73:"snow",75:"heavy_snow",80:"light_showers",81:"showers",82:"heavy_showers",95:"thunderstorm"}
    
    return {
        "location": {"lat": lat, "lon": lon},
        "current": {"temp_c": temp_c, "wind_speed_kmh": wind_kmh, "wind_direction_deg": wind_dir, "weather_code": weather_code, "condition": conditions_map.get(weather_code, "unknown")},
        "tonight": {"humidity_pct": int(sum(tonight_hums)/len(tonight_hums)) if tonight_hums else 0, "rain_expected": rain_expected},
        "sar_implications": _derive_sar_implications(temp_c, wind_kmh, rain_expected, weather_code)
    }

def _derive_sar_implications(temp_c: float, wind_kmh: float, rain_expected: bool, weather_code: int) -> str:
    """Turn weather into SAR implications narrative."""
    implications = []
    if rain_expected:
        implications.append("Rain expected — dogs seek covered shelter (under vehicles, sheds, building overhangs). Adjust search zone to include man-made structures.")
    if temp_c is not None:
        if temp_c < 5:
            implications.append(f"Cold ({temp_c}°C) — small/short-coated dogs at risk of hypothermia. Prioritize sheltered structures.")
        elif temp_c > 30:
            implications.append(f"Hot ({temp_c}°C) — dogs seek shade and water. Focus on shaded areas, water sources, cooling stations.")
    if wind_kmh and wind_kmh > 20:
        implications.append(f"Wind {wind_kmh} km/h — scent dispersal high. Air-scenting dogs effective; ground-trailing may be harder.")
    if not implications:
        implications.append("Moderate conditions. Standard search protocols apply.")
    return " ".join(implications)

def terrain_at_lkp(lat: float, lon: float) -> dict:
    """
    Query Overpass for land cover / terrain features around LKP.
    Returns a terrain classification summary dict.
    Cached permanently unless LKP shifts > LKP_TERRAIN_SHIFT_M.
    """
    # Bounding box: ~500m radius around LKP
    delta = 0.005  # ~500m
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["landuse"~"forest|grass|orchard"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});
      way["landuse"~"forest|grass|orchard"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});
      node["natural"~"wood|tree|water"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});
      way["natural"~"wood|water"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});
      node["building"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});
      way["building"]({lat-delta},{lon-delta},{lat+delta},{lon+delta});
    );
    out center;
    """
    try:
        r = requests.post(overpass_url, data={"data": query}, timeout=30)
        r.raise_for_status()
        data = r.json()
        features = data.get("elements", [])
        
        land_use = {"grass": 0, "forest": 0, "water": 0, "buildings": 0, "other": 0}
        for f in features:
            tags = f.get("tags", {})
            lu = tags.get("landuse") or tags.get("natural") or tags.get("building")
            if lu in land_use:
                land_use[lu] += 1
            elif lu:
                land_use["other"] += 1
        
        dominant = max(land_use, key=land_use.get) if any(land_use.values()) else "unknown"
        return {"land_cover": land_use, "dominant_terrain": dominant, "feature_count": len(features)}
    except Exception as e:
        return {"error": str(e), "land_cover": {}, "dominant_terrain": "unknown", "feature_count": 0}

# ─── Core Logic ────────────────────────────────────────────────────────────────

def scan_and_monitor(dry_run: bool = False) -> list[dict]:
    """
    Main monitoring loop. Returns list of alert dicts generated.
    """
    token = get_token()
    state = load_state()
    alerts = []
    now = datetime.now(timezone.utc)
    
    # 1. Get all open cases
    try:
        cases = api_get("/cases", token)
    except Exception as e:
        return [{"type": "system_error", "severity": "urgent", "body": f"Failed to fetch cases: {e}"}]
    
    case_ids = set()
    
    for case in cases:
        case_id = case["id"]
        case_ids.add(case_id)
        title = case.get("title", case_id)
        
        # Initialize state entry if new
        if case_id not in state:
            state[case_id] = {"first_seen": now.isoformat(), "last_seen": now.isoformat(), 
                              "last_sighting_ts": None, "last_enrichment_ts": None, "lkp": None}
        
        s = state[case_id]
        s["last_seen"] = now.isoformat()
        
        # 2. Get full case + health
        try:
            health = api_get(f"/cases/{case_id}/health", token)
        except Exception as e:
            alerts.append({"case_id": case_id, "title": title, "type": "error", "body": f"Health check failed: {e}"})
            continue
        
        stale_score = health.get("stale_score", 1.0)
        last_sighting_hrs = health.get("last_sighting_hours_ago")
        enrichment_count = health.get("enrichment_count", 0)
        last_enrichment_hrs = health.get("last_enrichment_hours_ago")
        
        # 3. Get full case for LKP and reports
        try:
            full_case = api_get(f"/cases/{case_id}", token)
        except Exception:
            full_case = {}
        
        # Extract LKP
        lkp = None
        for r in full_case.get("reports", []):
            if r.get("report_type") == "owner_intake" and r.get("latitude"):
                lkp = {"lat": r["latitude"], "lon": r["longitude"]}
                break
        if not lkp:
            for le in full_case.get("location_events", []):
                if le.get("is_confirmed") and le.get("latitude"):
                    lkp = {"lat": le["latitude"], "lon": le["longitude"]}
                    break
        
        # 4. Check for new sighting (decreasing last_sighting_hrs or null→value)
        prev_sighting_ts = s.get("last_sighting_ts")
        current_sighting_hrs = last_sighting_hrs
        
        is_new_sighting = False
        if current_sighting_hrs is not None:
            if prev_sighting_ts is None:
                is_new_sighting = True  # First sighting ever
            else:
                # Previous "hours ago" was larger = older = less recent
                # If current is smaller, a newer sighting exists
                prev_hrs = (now - datetime.fromisoformat(prev_sighting_ts)).total_seconds() / 3600
                if current_sighting_hrs < prev_hrs - 0.5:  # 30min threshold
                    is_new_sighting = True
        
        if is_new_sighting and prev_sighting_ts is not None:
            alerts.append({
                "case_id": case_id, "title": title, "type": "new_sighting",
                "body": f"New sighting report detected. Time since escape: {current_sighting_hrs:.1f}h. Coordinator review recommended."
            })
        
        # Update sighting state
        if current_sighting_hrs is not None:
            s["last_sighting_ts"] = now.isoformat()
        
        # 5. Weather refresh (if enrichment is stale)
        needs_weather = (enrichment_count == 0) or (last_enrichment_hrs is not None and last_enrichment_hrs > ENRICHMENT_MAX_AGE_HRS)
        if needs_weather and lkp:
            try:
                weather_data = weather_at_lkp(lkp["lat"], lkp["lon"])
                weather_intel = build_weather_intel(weather_data, lkp["lat"], lkp["lon"])
                if not dry_run:
                    api_post(f"/cases/{case_id}/enrichment", token, {
                        "type": "weather",
                        "source": "open-meteo",
                        "data": weather_intel
                    })
                    s["last_enrichment_ts"] = now.isoformat()
                alerts.append({
                    "case_id": case_id, "title": title, "type": "weather_refresh",
                    "body": f"Weather refreshed at LKP ({lkp['lat']}, {lkp['lon']}). {weather_intel['sar_implications'][:100]}..."
                })
            except Exception as e:
                alerts.append({"case_id": case_id, "title": title, "type": "error", "body": f"Weather refresh failed: {e}"})
        
        # 6. Terrain refresh (only if LKP shifted significantly)
        if lkp:
            prev_lkp = s.get("lkp")
            if prev_lkp:
                shift_m = haversine_m(lkp["lat"], lkp["lon"], prev_lkp["lat"], prev_lkp["lon"])
                needs_terrain = shift_m > LKP_TERRAIN_SHIFT_M
            else:
                needs_terrain = True  # First time
            
            if needs_terrain:
                try:
                    terrain_data = terrain_at_lkp(lkp["lat"], lkp["lon"])
                    if not dry_run:
                        api_post(f"/cases/{case_id}/enrichment", token, {
                            "type": "terrain",
                            "source": "overpass-api",
                            "data": terrain_data
                        })
                    s["lkp"] = lkp
                    alerts.append({
                        "case_id": case_id, "title": title, "type": "terrain_refresh",
                        "body": f"Terrain classified: dominant={terrain_data.get('dominant_terrain','unknown')}, {terrain_data.get('feature_count',0)} features found."
                    })
                except Exception as e:
                    alerts.append({"case_id": case_id, "title": title, "type": "error", "body": f"Terrain refresh failed: {e}"})
        
        # 7. Staleness alert — only if no recent enrichment AND high stale score
        # stale_score driven by sighting recency; if enrichment is fresh, don't spam coordinators
        last_enrichment_hrs_val = last_enrichment_hrs if last_enrichment_hrs is not None else float('inf')
        is_enrichment_stale = (enrichment_count == 0) or (last_enrichment_hrs_val > ENRICHMENT_MAX_AGE_HRS)
        
        if stale_score >= MAX_STALE_SCORE and is_enrichment_stale:
            missing = health.get("missing_data", [])
            missing_str = ", ".join(missing) if missing else "none"
            msg = f"Stale score: {stale_score:.2f}. No enrichment in {last_enrichment_hrs_val:.1f}h. Missing data: {missing_str}. Last sighting: {last_sighting_hrs:.1f}h ago."
            if not dry_run:
                api_post(f"/cases/{case_id}/notes", token, {
                    "category": "alert",
                    "severity": "urgent" if stale_score >= 0.95 else "warning",
                    "title": f"Case stale — coordinator action needed",
                    "body": msg
                })
            alerts.append({"case_id": case_id, "title": title, "type": "staleness", "severity": "urgent", "body": msg})
        elif stale_score >= MAX_STALE_SCORE and not is_enrichment_stale:
            # Enrichment is fresh — stale_score driven by sighting gap, not intel gap
            # Log but don't alert; the enrichment intel already reflects the situation
            print(f"  [INFO] {title}: stale_score={stale_score:.2f} but enrichment fresh — skipping duplicate alert")
    
    # 8. Purge zombie state entries (cases not seen in ZOMBIE_PURGE_DAYS)
    cutoff = (now - timedelta(days=ZOMBIE_PURGE_DAYS)).isoformat()
    for case_id in list(state.keys()):
        if state[case_id]["last_seen"] < cutoff:
            del state[case_id]
    
    # 9. Save state
    if not dry_run:
        save_state(state)
    
    return alerts

# ─── Delivery ─────────────────────────────────────────────────────────────────

def format_alert(a: dict) -> str:
    emoji = {"new_sighting": "👁", "weather_refresh": "🌤", "terrain_refresh": "🗺", 
             "staleness": "⚠️", "error": "❌", "system_error": "🚨"}.get(a["type"], "•")
    title = a.get("title", a["case_id"][:8])
    body = a.get("body", "")
    case = a.get("case_id", "")[:8]
    return f"{emoji} **{title}**\n> {body}\n`{case}`"

def send_to_dan(alerts: list[dict]) -> None:
    """Post a summary DM to Dan's Discord home channel."""
    if not alerts:
        return
    token = os.environ.get("HERMES_DISCORD_BOT_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("  [DISCORD] No bot token — skipping DM")
        return
    
    body_lines = [format_alert(a) for a in alerts]
    content = f"**📡 Case Monitor Run — {datetime.now().strftime('%Y-%m-%d %H:%M')} CT**\n\n" + "\n\n".join(body_lines)
    
    # Discord channel message via webhook or bot API
    # Using simple bot POST — home channel
    try:
        # Discord bot token auth
        headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
        payload = {"content": content}
        r = requests.post(f"https://discord.com/api/v10/channels/{DISCORD_HOME_ID}/messages",
                          headers=headers, json=payload, timeout=10)
        if r.status_code not in (200, 201):
            print(f"  [DISCORD] DM failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"  [DISCORD] DM error: {e}")

# ─── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    print(f"[Case Monitor] Starting{' (DRY RUN)' if dry_run else ''} — {datetime.now().isoformat()}")
    
    alerts = scan_and_monitor(dry_run=dry_run)
    
    if alerts:
        print(f"\n[Alerts Generated: {len(alerts)}]")
        for a in alerts:
            print(f"  [{a['type']}] {a.get('title','?')}: {a.get('body','?')[:80]}")
        
        if not dry_run:
            send_to_dan(alerts)
    else:
        print("\n[No alerts — all cases healthy]")
    
    sys.exit(0)

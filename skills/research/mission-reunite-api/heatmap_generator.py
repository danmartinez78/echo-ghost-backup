#!/usr/bin/env python3
"""
Movement Model Heatmap Generator v2
Computes a 2D Gaussian probability surface centered on the LKP,
weighted by terrain features, and outputs contour GeoJSON + ranked cells.
"""

import json, math, sys, datetime, datetime as dt
from pyproj import Geod
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import numpy as np

# ─── Constants ────────────────────────────────────────────────────────────────

ELLIPSOID = "WGS84"
CELL_SIZE_M = 50          # grid cell resolution in meters
THRESHOLDS = [0.5, 0.2, 0.05]  # probability contour levels
geod = Geod(ellps=ELLIPSOID)

# Terrain weights: feature OSM type → probability multiplier
# Based on SAR terrain优先级 research
TERRAIN_WEIGHTS = {
    "stream":        1.5,   # water + cover + wildlife trails → dogs seek
    "brook":         1.5,
    "drain":         1.3,
    "river":         1.5,
    "waterway":      1.4,
    "park":          0.7,   # open, exposed
    "grass":         0.6,   # low cover
    "wood":          1.4,   # shade + concealment
    "natural":       1.3,   # uncultivated cover
    "garden":        1.1,   # mild attraction (food, shelter)
    "scrub":         1.2,   # dense low cover
    "residential":   0.9,   # familiar territory but also dangerous
    "industrial":    0.5,   # hazardous, low cover
    "retail":        0.4,
    "commercial":    0.5,
    "farm":          0.4,
    "farmland":      0.3,
    "pavement":      0.2,   # roads, parking — avoid
    "road":          0.3,
    "footway":       0.8,   # trails — moderate attraction
    "path":          1.0,
    "track":         0.9,
    "default":       1.0,   # unmodified land
}

# ─── Geodesic helpers ─────────────────────────────────────────────────────────

def geodesic_point(lat_deg, lon_deg, distance_m, bearing_deg):
    """Move distance_m along bearing_deg from (lon, lat). Returns (lon, lat)."""
    az12, az21, dist = geod.inv(lon_deg, lat_deg,
                                  lon_deg + 0.001, lat_deg + 0.001)  # dummy
    # Forward: fwd(distance_m, bearing_deg)
    lon2, lat2, _ = geod.fwd(lon_deg, lat_deg, bearing_deg, distance_m)
    return lon2, lat2


def geodesic_distance(lat1, lon1, lat2, lon2):
    """Haversine distance in meters."""
    _, _, dist = geod.inv(lon1, lat1, lon2, lat2)
    return dist


def compute_bearing(lat1, lon1, lat2, lon2):
    """Compute forward azimuth from (lat1,lon1) to (lat2,lon2) in degrees."""
    az12, _, _ = geod.inv(lon1, lat1, lon2, lat2)  # geod.inv(lon1,lat1, lon2,lat2)
    return (az12 + 360) % 360


# ─── Cardinal / NL direction parser ───────────────────────────────────────────

CARDINAL_HEADINGS = {
    "n": 0,     "north": 0,
    "nne": 22,  "north-northeast": 22, "north north east": 22,
    "ne": 45,   "northeast": 45,        "north-east": 45,    "north east": 45,
    "ene": 67,  "east-northeast": 67,  "east north east": 67,
    "e": 90,    "east": 90,
    "ese": 112, "east-southeast": 112,  "east south east": 112,
    "se": 135,  "southeast": 135,       "south-east": 135,   "south east": 135,
    "sse": 157, "south-southeast": 157, "south south east": 157,
    "s": 180,   "south": 180,
    "ssw": 202, "south-southwest": 202, "south south west": 202,
    "sw": 225,  "southwest": 225,       "south-west": 225,   "south west": 225,
    "wsw": 247, "west-southwest": 247,  "west south west": 247,
    "w": 270,   "west": 270,
    "wnw": 292, "west-northwest": 292,  "west north west": 292,
    "nw": 315,  "northwest": 315,       "north-west": 315,   "north west": 315,
    "nnw": 337, "north-northwest": 337, "north north west": 337,
}


def parse_nl_direction(dot):
    """
    Convert a natural-language direction string to a heading in degrees.
    Handles: 'south', 'SSW', 'north-northeast', 'south west', 'NNE', 'east', etc.
    Returns None if the input can't be parsed.
    """
    if dot is None:
        return None

    # Already numeric?
    try:
        return float(dot) % 360
    except (TypeError, ValueError):
        pass

    # Normalize string
    raw = str(dot).strip().lower()

    # Handle "S" / "SSW" / "ENE" / "NW" etc. (all-caps abbreviations)
    # Try direct lookup first
    if raw in CARDINAL_HEADINGS:
        return CARDINAL_HEADINGS[raw]

    # Handle "south-southwest" style with hyphen
    if raw in CARDINAL_HEADINGS:
        return CARDINAL_HEADINGS[raw]

    # Handle comma-separated or "or" variants like "s, sw"
    # e.g. "s, sw" or "south or southwest" — take the primary direction
    primary = raw.split(",")[0].split(" or ")[0].strip()
    if primary in CARDINAL_HEADINGS:
        return CARDINAL_HEADINGS[primary]

    return None


def generate_oriented_ellipse(lon_center, lat_center, major_m, minor_m, bearing_deg,
                                num_points=64):
    """
    Generate an oriented ellipse as a Shapely Polygon.
    bearing_deg: direction of major axis (degrees clockwise from north).
    Returns: shapely Polygon in (lon, lat) coordinates.
    """
    angles = np.linspace(0, 2 * math.pi, num_points, endpoint=False)
    points = []
    for theta in angles:
        # parametric ellipse in local plane
        x_local = major_m * math.cos(theta)
        y_local = minor_m * math.sin(theta)
        # rotate by bearing (local x-axis = major axis direction)
        br_rad = math.radians(bearing_deg)
        x_rot = x_local * math.cos(br_rad) - y_local * math.sin(br_rad)
        y_rot = x_local * math.sin(br_rad) + y_local * math.cos(br_rad)
        # convert offsets (meters) to lat/lon degrees
        # at mid-latitude: 1° lat ≈ 111km, 1° lon ≈ 85km
        lat_offset = y_rot / 111320.0
        lon_offset = x_rot / (111320.0 * math.cos(math.radians(lat_center)))
        points.append((lon_center + lon_offset, lat_center + lat_offset))
    return Polygon(points)


def contour_at_threshold(probability_grid, cell_size_m, min_lat, min_lon, threshold):
    """
    Extract contour polygon at given probability threshold using marching squares.
    Fixes invalid geometries with a buffer(0) pass.
    probability_grid: 2D numpy array (rows=lat, cols=lon), row 0 = max lat
    Returns: shapely Polygon or None
    """
    rows, cols = probability_grid.shape
    active = probability_grid >= threshold

    polygons = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            SW = 1 if active[i, j] else 0
            SE = 1 if active[i, j+1] else 0
            NE = 1 if active[i+1, j+1] else 0
            NW = 1 if active[i+1, j] else 0
            cell_code = SW | (SE << 1) | (NE << 2) | (NW << 3)
            if cell_code in (0, 15):
                continue

            # cell bounds
            lat_i = min_lat + (rows - 1 - i) * cell_size_m / 111320.0
            lat_ip1 = min_lat + (rows - 1 - (i + 1)) * cell_size_m / 111320.0
            mid_lat = (lat_i + lat_ip1) / 2
            lon_j = min_lon + j * cell_size_m / (111320.0 * math.cos(math.radians(mid_lat)))
            lon_jp1 = min_lon + (j + 1) * cell_size_m / (111320.0 * math.cos(math.radians(mid_lat)))
            y0, y1 = lat_i, lat_ip1
            x0, x1 = lon_j, lon_jp1

            # Bilinear interpolation helper
            def sample_prob(i_, j_):
                return probability_grid[max(0, min(i_, rows-1)), max(0, min(j_, cols-1))]

            def interp_pt(val, val_a, val_b, coord_a, coord_b):
                if abs(val_a - val_b) < 1e-10:
                    return coord_a
                t = (threshold - val_a) / (val_b - val_a)
                return coord_a + t * (coord_b - coord_a)

            pSW = sample_prob(i, j)
            pSE = sample_prob(i, j+1)
            pNW = sample_prob(i+1, j)
            pNE = sample_prob(i+1, j+1)

            pts = []
            # bottom edge SW→SE
            if (cell_code in (1,2,3,4,5,6,9,10,11) and pSW >= threshold != (pSE >= threshold)):
                pts.append((interp_pt(threshold, pSW, pSE, x0, x1), y0))
            # right edge SE→NE
            if (cell_code in (2,3,6,7,10,11,14,15) and pSE >= threshold != (pNE >= threshold)):
                pts.append((x1, interp_pt(threshold, pSE, pNE, y0, y1)))
            # top edge NW→NE
            if (cell_code in (4,5,6,7,8,9,10,11,12,13,14,15) and pNW >= threshold != (pNE >= threshold)):
                pts.append((interp_pt(threshold, pNW, pNE, x0, x1), y1))
            # left edge SW→NW
            if (cell_code in (1,3,5,7,8,9,11,12,13,14,15) and pSW >= threshold != (pNW >= threshold)):
                pts.append((x0, interp_pt(threshold, pSW, pNW, y0, y1)))

            if len(pts) >= 3:
                try:
                    poly = Polygon(pts)
                    if poly.is_valid:
                        polygons.append(poly)
                    else:
                        fixed = poly.buffer(0)
                        if fixed.is_valid and not fixed.is_empty:
                            polygons.append(fixed)
                except Exception:
                    pass

    if not polygons:
        return None
    try:
        result = unary_union(polygons)
        if hasattr(result, 'buffer'):
            result = result.buffer(0)
        return result
    except Exception:
        return None


def bbox_from_ellipse(lon_c, lat_c, major_m, minor_m, bearing_deg, margin=1.1):
    """
    Compute bounding box around ellipse with margin factor.
    Default margin=1.1 gives 10% headroom beyond outer contour.
    """
    # Use diagonal as worst case
    diagonal_m = math.sqrt(major_m**2 + minor_m**2) * margin
    lat_range = diagonal_m / 111320.0
    lon_range = diagonal_m / (111320.0 * math.cos(math.radians(lat_c)))
    return {
        "min_lat": lat_c - lat_range,
        "max_lat": lat_c + lat_range,
        "min_lon": lon_c - lon_range,
        "max_lon": lon_c + lon_range,
    }


# ─── Helper functions (extracted for agent-level overrides) ────────────────────

def _get_species_size(case_data):
    subjects = case_data.get("subjects", [])
    pet = subjects[0].get("lost_pet_profile", {}) if subjects else {}
    species = pet.get("species", "dog").lower()
    size = (pet.get("size") or pet.get("size_class") or "medium").lower()
    return species, size


def _compute_bearing_from_reports(reports):
    """
    Internal bearing fallback: try direction_of_travel parsing, then geodesic.
    Returns (bearing_deg, bearing_source). Either may be None.
    """
    for r in reversed(reports):  # newest first
        dot_raw = r.get("direction_of_travel")
        parsed = parse_nl_direction(dot_raw)
        if parsed is not None:
            return round(parsed, 1) % 360, f"direction_of_travel:{dot_raw!r}"

    if len(reports) >= 2:
        origin_report = reports[0]
        lkp_report = reports[-1]
        bearing = compute_bearing(
            float(origin_report["latitude"]), float(origin_report["longitude"]),
            float(lkp_report["latitude"]),   float(lkp_report["longitude"])
        )
        return round(bearing, 1) % 360, "geodesic_oldest_to_newest"

    return None, None


def _compute_H_from_case(case_data, reports):
    """
    Internal H fallback: three-tier composite model.
    Returns (H_meters, H_source, major_axis_m, minor_axis_m).
    """
    species, size = _get_species_size(case_data)

    # Tier 1: Displacement × 3
    geo_time_reports = [
        (r, float(r["latitude"]), float(r["longitude"]), r.get("occurred_at") or r.get("reported_at"))
        for r in reports
        if r.get("latitude") and r.get("longitude") and (r.get("occurred_at") or r.get("reported_at"))
    ]
    geo_time_reports.sort(key=lambda x: x[3] or "")

    if len(geo_time_reports) >= 2:
        r_oldest = geo_time_reports[0]
        r_newest = geo_time_reports[-1]
        lat1, lon1 = r_oldest[1], r_oldest[2]
        lat2, lon2 = r_newest[1], r_newest[2]
        _, _, disp_m = geod.inv(lon1, lat1, lon2, lat2)
        H_meters = disp_m * 3.0
        H_source = f"displacement×3(disp={disp_m:.0f}m)"
        return H_meters, H_source, int(0.6 * H_meters), int(0.2 * H_meters)

    # Tier 2: Walk speed × time (only if bearing came from direction_of_travel)
    walk_speed_table = {
        ("dog", "small"): 0.8, ("dog", "medium"): 1.0,
        ("dog", "large"): 1.2, ("dog", "giant"): 1.4,
        ("cat", "indoor"): 0.4, ("cat", "outdoor-access"): 0.7, ("cat", "feral"): 0.7,
    }
    walk_speed = walk_speed_table.get((species, size), 1.0)

    time_missing_h = case_data.get("time_missing_h") or 24.0
    if geo_time_reports:
        t_oldest = geo_time_reports[0][3]
        t_newest = geo_time_reports[-1][3]
        if t_oldest and t_newest:
            try:
                t_oldest_dt = dt.datetime.fromisoformat(t_oldest.replace("Z", "+00:00"))
                t_newest_dt = dt.datetime.fromisoformat(t_newest.replace("Z", "+00:00"))
                time_missing_h = abs((t_newest_dt - t_oldest_dt).total_seconds()) / 3600
            except Exception:
                time_missing_h = 24.0

    H_meters = walk_speed * time_missing_h * 3600
    H_source = f"walk_speed×time(speed={walk_speed:.1f}m/s,time={time_missing_h:.1f}h)"
    return H_meters, H_source, int(0.6 * H_meters), int(0.2 * H_meters)


def _compute_species_table_H(species, size, time_missing_h):
    radius_table_mi = {
        ("dog", "small"): 1.5, ("dog", "medium"): 2.5, ("dog", "large"): 3.0, ("dog", "giant"): 5.0,
        ("cat", "indoor"): 0.75, ("cat", "outdoor-access"): 2.0, ("cat", "feral"): 2.0,
    }
    base_radius_mi = radius_table_mi.get((species, size), 2.0)
    phase_mult = (
        1.0 if time_missing_h >= 72 else
        0.8 if time_missing_h >= 24 else
        0.5 if time_missing_h >= 2 else
        0.2
    )
    H_meters = int(base_radius_mi * 1609.34 * phase_mult)
    H_source = f"species_table(species={species},size={size},time={time_missing_h:.0f}h)"
    return H_meters, H_source, int(0.6 * H_meters), int(0.2 * H_meters)


# ─── Main generation ──────────────────────────────────────────────────────────

def generate_movement_model(case_data, overpass_features=None,
                           bearing_deg=None, bearing_source=None,
                           H_meters=None, H_source=None):
    """
    case_data: parsed case JSON from Mission Reunite API
    overpass_features: list of OSM feature dicts with 'type', 'lat', 'lon', 'distance'

    Optional overrides (recommended — supply these from agent analysis rather than
    relying on the generator's internal parsing):
      bearing_deg:    heading in degrees clockwise from north (e.g. 57.4)
      bearing_source: string describing source (e.g. "direction_of_travel:south",
                      "geodesic_oldest_to_newest", "agent_interpretation")
      H_meters:       dispersal distance in meters (computed from displacement,
                      walk_speed×time, or species table)
      H_source:        string describing H source (e.g. "displacement×3(disp=557m)")

    Returns: movement_model dict matching enrichment schema v2
    """

    # ── Step 1: Extract LKP (most recent confirmed sighting) ──────────────────
    # Sort: oldest first (reverse=False), sightings before intake at equal timestamps
    # With reverse=False: reports[0]=oldest, reports[-1]=newest
    reports = sorted(
        [r for r in case_data.get("reports", []) if r.get("latitude") and r.get("longitude")],
        key=lambda r: (
            r.get("created_at") or r.get("reported_at") or "",
            1 if r.get("report_type") in ("sighting_submission", "sighting", "confirmed_sighting") else 0
        ),
        reverse=False
    )

    if not reports:
        raise ValueError("No georeferenced reports found in case")

    # reports[0] = oldest = movement origin, reports[-1] = newest = LKP
    lkp_report = reports[-1]
    origin_report = reports[0]

    lkp_lat = float(lkp_report["latitude"])
    lkp_lon = float(lkp_report["longitude"])
    lkp_source = lkp_report.get("report_type", "unknown")
    lkp_is_confirmed = lkp_report.get("sighting_type") == "confirmed_sighting" or \
                       lkp_report.get("report_type") in ("confirmed_sighting", "sighting")

    # ── Step 2: Bearing — use agent-supplied value, or fall back to internal logic ──
    # NOTE: prefer passing bearing_deg directly — this fallback is for
    # cases where no agent interpretation was performed
    if bearing_deg is None:
        bearing_deg, bearing_source = _compute_bearing_from_reports(reports)
        if bearing_deg is None:
            bearing_deg = 0.0
            bearing_source = bearing_source or "default"

    if bearing_source is None:
        bearing_source = "agent_override"

    bearing_deg = round(bearing_deg, 1) % 360

    # ── Step 3: H (dispersal distance) — use agent-supplied value, or fall back to internal logic ──
    if H_meters is None or H_source is None:
        H_meters_internal, H_source_internal, major_axis_m, minor_axis_m = \
            _compute_H_from_case(case_data, reports)
        if H_meters is None:
            H_meters = H_meters_internal
        if H_source is None:
            H_source = H_source_internal

    if H_meters is None:
        species, size = _get_species_size(case_data)
        H_meters, H_source, major_axis_m, minor_axis_m = \
            _compute_species_table_H(species, size, case_data.get("time_missing_h", 24.0))

    H_meters = int(H_meters)
    major_axis_m = max(major_axis_m, 100)   # floor: 100m minimum
    minor_axis_m = max(minor_axis_m, 50)

    # ── Step 4: Generate probability grid ─────────────────────────────────────
    bounds = bbox_from_ellipse(lkp_lon, lkp_lat, major_axis_m, minor_axis_m, bearing_deg)

    # Grid dimensions
    lat_span = bounds["max_lat"] - bounds["min_lat"]
    lon_span = bounds["max_lon"] - bounds["min_lon"]
    n_lat = max(int(lat_span * 111320.0 / CELL_SIZE_M), 10)
    n_lon = max(int(lon_span * 111320.0 * math.cos(math.radians(lkp_lat)) / CELL_SIZE_M), 10)

    # Build coordinate arrays
    lats = np.linspace(bounds["max_lat"], bounds["min_lat"], n_lat)
    lons = np.linspace(bounds["min_lon"], bounds["max_lon"], n_lon)

    # Gaussian PDF on rotated grid
    # Rotate each point into the ellipse's principal axis frame
    br_rad = math.radians(bearing_deg)
    cos_b = math.cos(br_rad)
    sin_b = math.sin(br_rad)

    pdf_grid = np.zeros((n_lat, n_lon))
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            # Offset from center in meters
            dlat_m = (lat - lkp_lat) * 111320.0
            dlon_m = (lon - lkp_lon) * 111320.0 * math.cos(math.radians(lkp_lat))
            # Rotate to ellipse frame
            x_rot =  dlat_m * cos_b + dlon_m * sin_b   # along bearing
            y_rot = -dlat_m * sin_b + dlon_m * cos_b   # perp to bearing
            # Gaussian in rotated frame
            z = (x_rot / major_axis_m) ** 2 + (y_rot / minor_axis_m) ** 2
            pdf_grid[i, j] = math.exp(-0.5 * z)

    # Normalize so peak = 1.0
    pdf_grid /= pdf_grid.max()

    # ── Step 5: Terrain weighting ─────────────────────────────────────────────
    terrain_factor_grid = np.ones((n_lat, n_lon))
    if overpass_features:
        for feat in overpass_features:
            feat_type = feat.get("type", "default").lower()
            weight = TERRAIN_WEIGHTS.get(feat_type, TERRAIN_WEIGHTS["default"])
            feat_lat = feat.get("lat") or feat.get("latitude")
            feat_lon = feat.get("lon") or feat.get("longitude")
            if feat_lat is None or feat_lon is None:
                continue
            # Apply weight to nearby cells
            for i, lat in enumerate(lats):
                for j, lon in enumerate(lons):
                    dist = geodesic_distance(lat, lon, feat_lat, feat_lon)
                    if dist < 50:  # feature is within 50m of cell
                        # Smooth falloff beyond 50m
                        factor = weight if dist < 10 else weight * (1 - (dist - 10) / 40)
                        terrain_factor_grid[i, j] *= max(0.1, min(factor, 2.0))

    # Weighted probability
    weighted_grid = pdf_grid * terrain_factor_grid
    weighted_grid /= weighted_grid.max()  # re-normalize so peak = 1.0

    # ── Step 6: Extract heatmap cells (only above threshold) ─────────────────
    threshold_min = THRESHOLDS[-1]  # 0.05
    cells = []
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            prob = weighted_grid[i, j]
            if prob >= threshold_min:
                cells.append({
                    "lat": round(lat, 6),
                    "lon": round(lon, 6),
                    "probability": round(float(prob), 3),
                    "terrain_factor": round(float(terrain_factor_grid[i, j]), 2),
                })

    # Sort by probability descending
    cells.sort(key=lambda c: c["probability"], reverse=True)

    # ── Step 7: Contour ellipses via chi-squared levels ───────────────────────
    # For 2D Gaussian: r^2 = -2*ln(P) where P is probability
    # r^2 ~ chi2(2) → contour radii scale with sqrt(-2*ln(P))
    #   P=0.50  → scale = sqrt(1.386) = 1.177
    #   P=0.20  → scale = sqrt(3.219) = 1.794
    #   P=0.05  → scale = sqrt(5.992) = 2.448
    CHI2_SCALES = {0.5: 1.177, 0.2: 1.794, 0.05: 2.448}

    contour_features = []
    for threshold, scale in CHI2_SCALES.items():
        major_contour = major_axis_m * scale
        minor_contour = minor_axis_m * scale
        # Clamp so outer contour doesn't exceed grid bounds
        major_contour = min(major_contour, (bounds["max_lat"] - bounds["min_lat"]) * 111320 * 0.45)
        minor_contour = min(minor_contour, (bounds["max_lon"] - bounds["min_lon"]) * 111320 * 0.45)
        ellipse_poly = generate_oriented_ellipse(
            lkp_lon, lkp_lat, major_contour, minor_contour, bearing_deg, num_points=64
        )
        if ellipse_poly.is_valid:
            ellipse_poly = ellipse_poly.simplify(0.0001, preserve_topology=True)
            coords = [[round(lon, 7), round(lat, 7)] for lon, lat in ellipse_poly.exterior.coords]
            contour_features.append({
                "properties": {
                    "threshold": threshold,
                    "label": f"{int(threshold * 100)}%",
                },
                "geometry": {"type": "Polygon", "coordinates": [coords]}
            })

    # ── Step 8: Terrain flags ─────────────────────────────────────────────────
    terrain_flags = []
    if overpass_features:
        for feat in overpass_features:
            ftype = feat.get("type", "").lower()
            if ftype in ("stream", "brook", "drain", "river", "waterway"):
                terrain_flags.append("near_stream")
                break
        for feat in overpass_features:
            ftype = feat.get("type", "").lower()
            if ftype in ("wood", "natural", "scrub"):
                terrain_flags.append("wooded_cover")
                break
        for feat in overpass_features:
            ftype = feat.get("type", "").lower()
            if ftype in ("footway", "path", "track"):
                terrain_flags.append("near_trail")
                break

    # ── Step 9b: Build rationale ─────────────────────────────────────────────────
    # Dynamic rationale using available signals
    signals = []
    assumptions = []

    if bearing_source.startswith("direction_of_travel"):
        dot_val = bearing_source.split(":")[1].strip("'\"")
        signals.append(f"Direction of travel from recent sighting: {dot_val}")
    elif bearing_source == "geodesic_oldest_to_newest":
        signals.append(f"Geodesic bearing of {bearing_deg:.0f}° from {len(reports)} georeferenced reports")

    if H_source.startswith("displacement"):
        disp_m = float(H_source.split("disp=")[1].split("m)")[0]) if "disp=" in H_source else None
        if disp_m:
            signals.append(f"Displacement of {disp_m:.0f}m between reports drives scatter radius (H={H_meters:.0f}m)")
    elif H_source.startswith("walk_speed"):
        signals.append(f"Walk-speed model: {H_source.split('(')[1].rstrip(')')}")
    elif H_source.startswith("species_table"):
        signals.append(f"Species/size scatter table: {H_source.split('(')[1].rstrip(')')}")

    if terrain_flags:
        signals.append(f"Terrain signals: {', '.join(terrain_flags[:3])}")
    # NOTE: if terrain_flags is empty, we did not actually check terrain.
    # Do NOT append a misleading "no terrain" signal — terrain analysis is a
    # future enrichment step, not a finding that no terrain exists.

    assumptions.append("No confirmed sightings after last report timestamp")
    assumptions.append("No third-party transport or human-caused relocation")

    rationale = {
        "summary": f"Probability surface centered on last confirmed point, oriented {bearing_deg:.0f}° along primary movement axis.",
        "signals": signals,
        "confidence": "medium" if bearing_source != "default" else "low",
        "assumptions": assumptions,
    }

    # ── Step 9c: Assemble enrichment payload ───────────────────────────────────
    movement_model = {
        "type": "movement_forecast",
        "version": 2,
        "lkp": {
            "lat": round(lkp_lat, 6),
            "lon": round(lkp_lon, 6),
            "source": lkp_source,
        },
        "movement_params": {
            "bearing_deg": round(bearing_deg, 1),
            "bearing_source": bearing_source,
            "H_meters": H_meters,
            "H_source": H_source,
            "major_axis_m": major_axis_m,
            "minor_axis_m": minor_axis_m,
            "dispersion_model": "gaussian_2d",
        },
        "grid": {
            "cell_size_m": CELL_SIZE_M,
            "bounds": {k: round(v, 6) for k, v in bounds.items()},
        },
        "heatmap_cells": cells,
        "contours": {
            "type": "FeatureCollection",
            "features": contour_features,
        },
        "terrain_flags": list(set(terrain_flags)),
        "rationale": rationale,
        "generated_at": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
    }

    return movement_model


if __name__ == "__main__":
    # Load case data
    with open("/tmp/buddy_case.json") as f:
        case_data = json.load(f)

    # Load Overpass features if available
    overpass_features = []
    try:
        with open("/tmp/overpass_features.json") as f:
            raw = json.load(f)
            if isinstance(raw, list):
                features = raw
            elif isinstance(raw, dict):
                features = raw.get("elements", [])
            else:
                features = []
            for elem in features:
                if elem.get("type") == "way":
                    tags = elem.get("tags", {})
                    feat_type = tags.get("waterway") or tags.get("landuse") or tags.get("natural") or "default"
                    overpass_features.append({
                        "type": feat_type,
                        "id": elem.get("id"),
                        "distance": elem.get("dist", 500),
                    })
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    model = generate_movement_model(case_data, overpass_features)

    # Write output
    output_path = "/tmp/buddy_heatmap_v2.json"
    with open(output_path, "w") as f:
        json.dump(model, f, indent=2)

    print(f"Generated: {output_path}")
    print(f"  LKP: ({model['lkp']['lat']}, {model['lkp']['lon']})")
    print(f"  Bearing: {model['movement_params']['bearing_deg']}°")
    print(f"  Major×Minor: {model['movement_params']['major_axis_m']}m × {model['movement_params']['minor_axis_m']}m")
    print(f"  Grid: {len(model['heatmap_cells'])} cells above 5%")
    print(f"  Contours: {len(model['contours']['features'])} features")

    sys.path.insert(0, "/home/daniel/.hermes/skills/research/mission-reunite-api")
    print("\nDone.")

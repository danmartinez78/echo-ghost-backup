#!/usr/bin/env python3
"""
Movement Model Generator — Echo Intel Pipeline
Uses: Haversine distance/bearing, local tangent plane for corridor polygons.
"""
import math
import json
from typing import List, Tuple

R = 6378137.0  # WGS84 semi-major axis

def haversine_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing from lat1/lon1 to lat2/lon2 in degrees from north."""
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δλ = math.radians(lon2 - lon1)
    x = math.sin(Δλ) * math.cos(φ2)
    y = math.cos(φ1)*math.sin(φ2) - math.sin(φ1)*math.cos(φ2)*math.cos(Δλ)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def destination_point(lat: float, lon: float, bearing_deg: float, dist_m: float) -> Tuple[float, float]:
    """
    Destination point using simple spherical approximation.
    Accurate to ~0.5% for distances < 100km. Sufficient for search zone geometry.
    Returns (lat, lon).
    """
    φ1 = math.radians(lat)
    α = math.radians(bearing_deg)
    δ = dist_m / R

    φ2 = math.asin(
        math.sin(φ1) * math.cos(δ) +
        math.cos(φ1) * math.sin(δ) * math.cos(α)
    )
    λ2 = math.radians(lon) + math.atan2(
        math.sin(α) * math.sin(δ) * math.cos(φ1),
        math.cos(δ) - math.sin(φ1) * math.sin(φ2)
    )
    return math.degrees(φ2), (math.degrees(λ2) + 540) % 360 - 180


def geodesic_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in meters."""
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def oriented_corridor(center_lat: float, center_lon: float,
                      bearing_deg: float, length_m: float, width_m: float,
                      num_segments: int = 24) -> List[List[float]]:
    """
    Generate a corridor polygon oriented along bearing_deg.
    Uses simple spherical destination for centerline, then constructs
    perpendicular sides using local tangent plane (accurate for offsets < 1km).
    Returns closed GeoJSON [lon, lat] polygon coordinates.
    """
    half_l = length_m / 2
    half_w = width_m / 2
    perp = (bearing_deg + 90) % 360

    # Bearing vector components in local tangent plane (degrees per meter)
    # 1 meter north ≈ 1/111320 degrees lat
    # 1 meter east  ≈ 1/(111320*cos(lat)) degrees lon
    lat_per_m = 1.0 / 111320.0
    lon_per_m = 1.0 / (111320.0 * math.cos(math.radians(center_lat)))

    # Bearing unit vector (north=1,0 in local frame)
    cos_b = math.cos(math.radians(bearing_deg))
    sin_b = math.sin(math.radians(bearing_deg))
    # Perpendicular unit vector (clockwise 90°)
    cos_p = math.cos(math.radians(perp))   # = -sin_b
    sin_p = math.sin(math.radians(perp))   # = cos_b

    left_pts = []
    right_pts = []

    for i in range(num_segments + 1):
        t = i / num_segments  # 0 to 1 along corridor
        d = -half_l + t * length_m  # distance from center along bearing

        # Center point of this segment
        c_lat, c_lon = destination_point(center_lat, center_lon, bearing_deg, d)

        # Perpendicular offset in local tangent plane
        dlat = cos_p * half_w * lat_per_m
        dlon = sin_p * half_w * lon_per_m

        # Left side: offset in +perp direction
        l_lat = c_lat + dlat
        l_lon = c_lon + dlon
        # Right side: offset in -perp direction
        r_lat = c_lat - dlat
        r_lon = c_lon - dlon

        left_pts.append([l_lon, l_lat])
        right_pts.append([r_lon, r_lat])

    # Build closed polygon
    coords = left_pts + right_pts[::-1] + [left_pts[0]]
    return coords


def geodesic_ellipse(center_lat: float, center_lon: float,
                     semi_major_m: float, semi_minor_m: float,
                     rotation_deg: float, num_points: int = 32) -> List[List[float]]:
    """
    Generate an ellipse polygon using local tangent plane.
    Returns GeoJSON [lon, lat] closed coordinates.
    """
    lat_per_m = 1.0 / 111320.0
    lon_per_m = 1.0 / (111320.0 * math.cos(math.radians(center_lat)))
    α = math.radians(rotation_deg)

    coords = []
    for i in range(num_points):
        θ = 2 * math.pi * i / num_points
        # Local ellipse point in rotated frame (meters from center)
        dx = semi_major_m * math.cos(θ)
        dy = semi_minor_m * math.sin(θ)
        # Rotate by α
        rx = dx * math.cos(α) - dy * math.sin(α)
        ry = dx * math.sin(α) + dy * math.cos(α)
        # Convert to lat/lon offset
        dlat = ry * lat_per_m
        dlon = rx * lon_per_m
        coords.append([center_lon + dlon, center_lat + dlat])
    coords.append(coords[0])
    return coords


def build_movement_model(case_data: dict, overpass_features: List[dict]) -> dict:
    """
    Build a complete movement_model enrichment payload.
    """
    reports = case_data.get('reports', [])
    sightings = [r for r in reports if r.get('report_type') == 'sighting_submission']
    owner_intakes = [r for r in reports if r.get('report_type') == 'owner_intake']

    # --- 1. LKP: most recent sighting, else owner intake ---
    if sightings:
        sightings.sort(key=lambda r: r.get('occurred_at', ''), reverse=True)
        lkp_report = sightings[0]
    elif owner_intakes:
        lkp_report = owner_intakes[0]
    else:
        lkp_report = reports[0] if reports else None

    lkp_lat = lkp_report['latitude']
    lkp_lon = lkp_report['longitude']

    # --- 2. Movement bearing from owner intake to LKP ---
    owner_intake = owner_intakes[0] if owner_intakes else None
    if sightings and owner_intake:
        movement_bearing = haversine_bearing(
            owner_intake['latitude'], owner_intake['longitude'],
            lkp_lat, lkp_lon
        )
    else:
        movement_bearing = 85.0

    # --- 3. Scatter parameters ---
    base_radius_m = 1200
    corridor_length_m = base_radius_m * 2  # 2400m
    corridor_width_m = 200                   # 200m

    # --- 4. Terrain flags ---
    terrain_flags = []
    for feat in overpass_features:
        tags = feat.get('tags', {})
        w = tags.get('waterway', '')
        if w in ('stream', 'brook', 'drain', 'river') or 'stream' in w:
            terrain_flags.append('creek-riparian')
        elif tags.get('leisure') == 'park' or tags.get('landuse') == 'grass':
            terrain_flags.append('open-grass-park')
        elif tags.get('landuse') == 'wood' or tags.get('natural') == 'wood':
            terrain_flags.append('wooded-trail')
        elif tags.get('leisure') == 'garden':
            terrain_flags.append('garden')
        elif tags.get('landuse') == 'residential':
            terrain_flags.append('residential')
    terrain_flags = sorted(set(terrain_flags))

    # --- 5. Search zones ---
    zone1 = oriented_corridor(lkp_lat, lkp_lon, movement_bearing,
                               corridor_length_m, corridor_width_m, num_segments=24)
    perp = (movement_bearing + 90) % 360
    zone2 = oriented_corridor(lkp_lat, lkp_lon, perp,
                               base_radius_m * 1.2, 350, num_segments=16)
    zone3 = geodesic_ellipse(lkp_lat, lkp_lon,
                               semi_major_m=base_radius_m * 1.5,
                               semi_minor_m=base_radius_m * 0.75,
                               rotation_deg=movement_bearing, num_points=32)

    # --- 6. Waypoints ---
    waypoints = []
    for s in sightings:
        waypoints.append({
            'lat': s['latitude'], 'lon': s['longitude'],
            'source': 'sighting_submission', 'confirmed': False,
            'notes': s.get('narrative', '')[:100]
        })
    for oi in owner_intakes:
        waypoints.append({
            'lat': oi['latitude'], 'lon': oi['longitude'],
            'source': 'owner_intake', 'confirmed': True,
            'notes': oi.get('narrative', '')[:100]
        })

    # --- 7. Corridor LineString ---
    corridor_coords = [[oi['longitude'], oi['latitude']] for oi in owner_intakes]
    corridor_coords += [[s['longitude'], s['latitude']] for s in sightings]

    model = {
        'center': {'lat': lkp_lat, 'lon': lkp_lon},
        'radius_m': base_radius_m,
        'waypoints': waypoints,
        'corridors': [{
            'type': 'LineString',
            'coordinates': corridor_coords,
            'bearing_deg': round(movement_bearing, 1)
        }],
        'search_zones': [
            {'type': 'Polygon', 'coordinates': [zone1],
             'name': 'Primary Creek Corridor', 'priority': 1},
            {'type': 'Polygon', 'coordinates': [zone2],
             'name': 'Riparian Cross-Section', 'priority': 2},
            {'type': 'Polygon', 'coordinates': [zone3],
             'name': 'Probability Ellipse (Reference)', 'priority': 3}
        ],
        'movement_vector': {
            'bearing_deg': round(movement_bearing, 1),
            'speed_kmh_estimate': 1.5,
            'confidence': 'low'
        },
        'terrain_flags': terrain_flags,
        'scatter_model_notes': (
            f"Scatter centered on most recent sighting ({lkp_lat:.4f}, {lkp_lon:.4f}). "
            f"Movement bearing {movement_bearing:.0f} deg from owner intake. "
            f"{len(overpass_features)} terrain features analyzed. "
            f"Terrain flags: {', '.join(terrain_flags)}."
        )
    }
    return model


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: movement_model.py <case.json> <overpass_features.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        case_data = json.load(f)
    with open(sys.argv[2]) as f:
        overpass_features = json.load(f)
    model = build_movement_model(case_data, overpass_features)
    print(json.dumps(model, indent=2))

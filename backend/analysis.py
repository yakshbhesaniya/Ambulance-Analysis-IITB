# backend/analysis.py
from collections import defaultdict
import json
from geojson import Feature, FeatureCollection, LineString as GLineString
from backend.models import SessionLocal, Trip

def build_frequency_geojson():
    """
    Read stored trip routes and build a GeoJSON linestring collection
    with 'count' property per unique segment (naive approach).
    """
    session = SessionLocal()
    trips = session.query(Trip).all()
    session.close()

    segment_counts = defaultdict(int)
    for t in trips:
        if not t.route_geojson:
            continue
        data = json.loads(t.route_geojson)
        features = data.get("features", [])
        if features:
            geom = features[0].get("geometry", {})
            coords = geom.get("coordinates")
        else:
            coords = None
        if not coords:
            continue
        for i in range(len(coords)-1):
            a = tuple(coords[i])   # (lng, lat)
            b = tuple(coords[i+1])
            seg = (a, b) if a < b else (b, a)
            segment_counts[seg] += 1

    features = []
    for seg, cnt in segment_counts.items():
        coords = [ [seg[0][0], seg[0][1]], [seg[1][0], seg[1][1]] ]
        feat = Feature(geometry=GLineString(coords), properties={"count": cnt})
        features.append(feat)

    return FeatureCollection(features)

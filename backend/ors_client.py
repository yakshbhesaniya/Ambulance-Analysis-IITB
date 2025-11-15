# backend/ors_client.py
import requests
import json
import config

BASE_URL = "https://api.openrouteservice.org"

def get_route(start, via, end, profile="driving-car"):
    """
    start, via, end: tuples (lng, lat)
    returns: dict with 'geojson', 'summary' (distance m, duration s)
    """
    url = f"{BASE_URL}/v2/directions/{profile}/geojson"
    coords = [ [start[0], start[1]], [via[0], via[1]], [end[0], end[1]] ]
    body = {
        "coordinates": coords,
        "instructions": False
    }
    headers = {
        "Authorization": config.ORS_API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # extract route summary if present
    summary = {}
    features = data.get("features", [])
    if features:
        props = features[0].get("properties", {})
        seg_summary = props.get("summary", {})
        summary = {
            "distance_m": seg_summary.get("distance"),
            "duration_s": seg_summary.get("duration")
        }
    return {"geojson": data, "summary": summary}

def get_isochrones(center, ranges_minutes=(3,5,7,10)):
    url = f"{BASE_URL}/isochrones"
    body = {
        "locations": [[center[0], center[1]]],
        "profile": "driving-car",
        "range": [r*60 for r in ranges_minutes],
        "units": "m"
    }
    headers = {
        "Authorization": config.ORS_API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()

def geocode_place(text, country="IN", size=1):
    """
    Fallback geocoder using ORS /geocode/search
    returns first (lng, lat) tuple or None
    """
    url = f"{BASE_URL}/geocode/search"
    params = {
        "api_key": config.ORS_API_KEY,
        "text": text,
        "size": size,
        "boundary.country": country
    }
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    features = data.get("features") or []
    if not features:
        return None
    # coordinates in features[0].geometry.coordinates = [lng, lat]
    coords = features[0].get("geometry", {}).get("coordinates")
    if coords and len(coords) >= 2:
        return (coords[0], coords[1])
    return None

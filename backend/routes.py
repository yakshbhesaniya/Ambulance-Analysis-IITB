# backend/routes.py
from flask import Blueprint, request, jsonify, current_app
from backend.models import SessionLocal, Trip, init_db
from backend.ors_client import get_route, get_isochrones, geocode_place
from backend.analysis import build_frequency_geojson
from backend.utils import trips_to_csv, geojson_to_coords
import json
from datetime import datetime, timedelta
import config

api_bp = Blueprint("api", __name__)

# ensure DB tables exist
init_db()

# A small local lookup for common place names around IITB.
LOCATIONS = {
    "Gulmohar Park": (72.9118, 19.1342),
    "IITB Main Gate": (72.9133, 19.1334),
    "Hiranandani": (72.9196, 19.1292),
    "Powai Lake": (72.9075, 19.1231),
    "Kanjurmarg": (72.9500, 19.1390),
}

@api_bp.route("/locations", methods=["GET"])
def list_locations():
    return jsonify({"locations": LOCATIONS})

@api_bp.route("/trip/last", methods=["GET"])
def last_trip():
    session = SessionLocal()
    t = session.query(Trip).order_by(Trip.id.desc()).first()
    session.close()
    if not t:
        return jsonify({"last": None})
    return jsonify({
        "last": {
            "id": t.id,
            "date": t.date.isoformat() if t.date else None,
            "next_odometer": t.next_odometer,
            "distance_km": t.distance_km,
            "arrival_time": t.arrival_time.isoformat() if t.arrival_time else None
        }
    })

@api_bp.route("/trip", methods=["POST"])
def create_trip():
    """
    Expected JSON body:
    {
      "location_name": str,      # from (human name)
      "patient_name": str,
      "driver_name": str,
      "purpose": str,            # pickup/drop
      "notes": str (optional)
    }
    """
    body = request.get_json() or {}
    location_name = (body.get("location_name") or "").strip()
    if not location_name:
        return jsonify({"error":"location_name required"}), 400

    patient_name = body.get("patient_name", "")
    driver_name = body.get("driver_name", "")
    purpose = body.get("purpose", "")
    notes = body.get("notes", "")

    # determine start_odometer automatically from last trip
    session = SessionLocal()
    last = session.query(Trip).order_by(Trip.id.desc()).first()
    start_odometer = None
    if last and last.next_odometer is not None:
        start_odometer = float(last.next_odometer)
    else:
        start_odometer = 0.0

    # resolve place name -> (lng, lat)
    coords = None
    if location_name in LOCATIONS:
        coords = LOCATIONS[location_name]  # (lng, lat)
    else:
        try:
            coords = geocode_place(location_name)
        except Exception:
            coords = None

    if not coords:
        session.close()
        return jsonify({"error":"Could not resolve location name to coordinates. Add to LOCATIONS or check spelling."}), 400

    pickup_lng, pickup_lat = coords[0], coords[1]

    # compute route: hospital -> pickup -> hospital
    start = (config.HOSPITAL_LNG, config.HOSPITAL_LAT)
    via = (pickup_lng, pickup_lat)
    end = (config.HOSPITAL_LNG, config.HOSPITAL_LAT)
    try:
        route_resp = get_route(start, via, end)
    except Exception as e:
        session.close()
        return jsonify({"error": "ORS route failed", "detail": str(e)}), 500

    summary = route_resp.get("summary", {})
    geojson = route_resp.get("geojson")

    # compute km and times
    distance_m = summary.get("distance_m") or 0
    distance_km = round(distance_m / 1000.0, 3)
    route_seconds = int(summary.get("duration_s") or 0)

    departure_time = datetime.utcnow()
    arrival_time = departure_time + timedelta(seconds=route_seconds)
    date_only = departure_time

    next_odometer = None
    try:
        next_odometer = round(float(start_odometer) + distance_km, 3)
    except Exception:
        next_odometer = None

    # store
    trip = Trip(
        request_time=departure_time,
        departure_time=departure_time,
        arrival_time=arrival_time,
        date=date_only,
        location_name=location_name,
        patient_name=patient_name,
        driver_name=driver_name,
        purpose=purpose,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        start_odometer=start_odometer,
        distance_km=distance_km,
        next_odometer=next_odometer,
        route_seconds=route_seconds,
        notes=notes,
        route_geojson=json.dumps(geojson)
    )
    session.add(trip)
    session.commit()
    session.refresh(trip)
    session.close()

    return jsonify({
        "id": trip.id,
        "date": trip.date.isoformat(),
        "departure_time": trip.departure_time.isoformat(),
        "arrival_time": trip.arrival_time.isoformat(),
        "distance_km": trip.distance_km,
        "start_odometer": trip.start_odometer,
        "next_odometer": trip.next_odometer,
        "route_seconds": trip.route_seconds,
        "geojson": geojson
    })

@api_bp.route("/trip/export", methods=["GET"])
def export_trips():
    session = SessionLocal()
    trips = session.query(Trip).all()
    resp = trips_to_csv(trips)
    session.close()
    return resp

@api_bp.route("/analysis/isochrones", methods=["GET"])
def isochrones():
    center = (config.HOSPITAL_LNG, config.HOSPITAL_LAT)
    try:
        data = get_isochrones(center, ranges_minutes=(3,5,7,10))
    except Exception as e:
        return jsonify({"error":"isochrones failed", "detail": str(e)}), 500
    return jsonify(data)

@api_bp.route("/analysis/frequency", methods=["GET"])
def frequency():
    try:
        fc = build_frequency_geojson()
    except Exception as e:
        return jsonify({"error":"analysis failed", "detail": str(e)}), 500
    return jsonify(fc)

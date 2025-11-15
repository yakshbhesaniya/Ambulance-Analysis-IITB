# backend/utils.py
import csv
from io import StringIO
from flask import Response
import json

def trips_to_csv(trips):
    """
    trips: list of SQLAlchemy Trip objects
    returns: Flask Response with CSV
    Columns:
    Date,Km Reading,From,Departure,Destination,Arrival,Distance,Next Km,Driver,User,Purpose
    """
    si = StringIO()
    writer = csv.writer(si)
    header = ["Date","Km Reading","From","Departure","Destination","Arrival","Distance_km","Next_Km","Driver","User","Purpose"]
    writer.writerow(header)
    for t in trips:
        date = t.date.isoformat() if t.date else ""
        departure = t.departure_time.isoformat() if t.departure_time else ""
        arrival = t.arrival_time.isoformat() if t.arrival_time else ""
        dest = "IITB Hospital"
        writer.writerow([
            date,
            t.start_odometer or "",
            t.location_name or "",
            departure,
            dest,
            arrival,
            t.distance_km or "",
            t.next_odometer or "",
            t.driver_name or "",
            t.patient_name or "",
            t.purpose or ""
        ])
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition":"attachment;filename=ambulance_trips.csv"}
    )
def geojson_to_coords(geojson):
    # convenience parser - returns list of (lng,lat) from ORS route geojson
    if not geojson:
        return []
    if isinstance(geojson, str):
        geojson = json.loads(geojson)
    features = geojson.get("features", [])
    if not features:
        return []
    geom = features[0].get("geometry", {})
    coords = geom.get("coordinates", [])
    return coords

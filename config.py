# config.py
import os

# Put your OpenRouteService API key here or set ORS_API_KEY env var
ORS_API_KEY = os.environ.get("ORS_API_KEY", "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImYxZWQ5YTVhOWVhNDRiMjk5NGQ0N2ZkMTExMDQzYWE5IiwiaCI6Im11cm11cjY0In0=")

# Hospital coordinates (IITB) - Updated coordinates
HOSPITAL_LAT = float(os.environ.get("HOSPITAL_LAT", 19.1309507))
HOSPITAL_LNG = float(os.environ.get("HOSPITAL_LNG", 72.9146062))

# IITB Campus bounding box (to limit isochrones to campus area)
# Based on hostel coordinates: North 19.138, South 19.129, East 72.916, West 72.904
IITB_BBOX = [
    float(os.environ.get("IITB_BBOX_WEST", 72.904)),   # West (min longitude)
    float(os.environ.get("IITB_BBOX_SOUTH", 19.129)),  # South (min latitude)
    float(os.environ.get("IITB_BBOX_EAST", 72.916)),  # East (max longitude)
    float(os.environ.get("IITB_BBOX_NORTH", 19.138))  # North (max latitude)
]

# Database URL (SQLite file inside instance folder)
DB_URL = os.environ.get("DB_URL", "sqlite:///instance/ambulance.db")

# Flask
DEBUG = True

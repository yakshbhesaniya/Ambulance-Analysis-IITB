# config.py
import os

# Put your OpenRouteService API key here or set ORS_API_KEY env var
ORS_API_KEY = os.environ.get("ORS_API_KEY", "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImYxZWQ5YTVhOWVhNDRiMjk5NGQ0N2ZkMTExMDQzYWE5IiwiaCI6Im11cm11cjY0In0=")

# Hospital coordinates (IITB) - change if needed
HOSPITAL_LAT = float(os.environ.get("HOSPITAL_LAT", 19.1334))
HOSPITAL_LNG = float(os.environ.get("HOSPITAL_LNG", 72.9133))

# Database URL (SQLite file inside instance folder)
DB_URL = os.environ.get("DB_URL", "sqlite:///instance/ambulance.db")

# Flask
DEBUG = True

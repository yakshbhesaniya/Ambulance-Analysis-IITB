import os

# Database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///ambulance.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# OpenRouteService API configuration
ORS_API_KEY = os.environ.get('ORS_API_KEY', 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImYxZWQ5YTVhOWVhNDRiMjk5NGQ0N2ZkMTExMDQzYWE5IiwiaCI6Im11cm11cjY0In0')

# Routing configuration
ROUTING_TIMEOUT = 10  # Request timeout for API calls (seconds)
HAVERSINE_SPEED_KMH = 30  # Assumed speed for Haversine calculations (km/h)

# IITB Hospital coordinates (lat, lon)
HOSPITAL_COORDS = [19.1309507, 72.9146062]

# IITB Campus locations for pickup
CAMPUS_LOCATIONS = {
    "Hostel 1 (Queen of the Campus)": [19.1360511, 72.9139822],
    "Hostel 2 (The Wild Ones)": [19.1360302, 72.9125194],
    "Hostel 3 (Vitruvians)": [19.1360347, 72.9114388],
    "Hostel 4 (Madhouse)": [19.1360347, 72.9114388],  # Using H3 coords as placeholder
    "Hostel 5 (Penthouse)": [19.1353150, 72.9103374],
    "Hostel 6 (Vikings)": [19.1352447, 72.9070937],
    "Hostel 8": [19.1339352, 72.9112112],
    "Hostel 9 (Pluto)": [19.1349887, 72.9081793],
    "Hostel 10 (Phoenix)": [19.1296172, 72.9159134],
    "Hostel 11 (Athena)": [19.1335136, 72.9122780],
    "Hostel 12 (Crown of the Campus)": [19.1355082, 72.9057432],
    "Hostel 13 (House of Titans)": [19.1355082, 72.9057432],
    "Hostel 14 (The Silicon Ship)": [19.1355082, 72.9057432],
    "Hostel 15 (Trident)": [19.1374068, 72.9135782],
    "Hostel 16 (Olympus)": [19.1377654, 72.9128483],
    "Hostel 17 (Kings Landing)": [19.1348411, 72.9086540],
    "Hostel 18": [19.1360071, 72.9094808],
    "Tansa": [19.1357613, 72.9104464],
}

# Initial odometer reading
INITIAL_ODOMETER = 0

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from models import db, AmbulanceTrip
import config
import route_optimizer
import requests
import json
from datetime import datetime, timedelta
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
CORS(app)

db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get-current-odometer', methods=['GET'])
def get_current_odometer():
    """Get the current odometer reading (last trip's end reading or initial value)"""
    last_trip = AmbulanceTrip.query.order_by(AmbulanceTrip.id.desc()).first()
    if last_trip:
        current_reading = last_trip.km_reading_end
    else:
        current_reading = config.INITIAL_ODOMETER
    return jsonify({'odometer': current_reading})

@app.route('/api/get-locations', methods=['GET'])
def get_locations():
    """Get all campus locations"""
    locations = []
    for name, coords in config.CAMPUS_LOCATIONS.items():
        locations.append({
            'name': name,
            'lat': coords[0],
            'lon': coords[1]
        })
    return jsonify({'locations': locations})

@app.route('/api/get-route', methods=['POST'])
def get_route():
    """Calculate route from hospital to pickup and back using OpenRouteService"""
    data = request.json
    pickup_coords = [data['pickup_lon'], data['pickup_lat']]
    hospital_coords = [config.HOSPITAL_COORDS[1], config.HOSPITAL_COORDS[0]]  # lon, lat for ORS
    
    try:
        # Route 1: Hospital to Pickup
        route1 = calculate_route(hospital_coords, pickup_coords)
        
        # Route 2: Pickup to Hospital
        route2 = calculate_route(pickup_coords, hospital_coords)
        
        # Combine routes
        total_distance = route1['distance'] + route2['distance']
        total_duration = route1['duration'] + route2['duration']
        
        # Combine geometries
        combined_geometry = route1['geometry'] + route2['geometry']
        
        return jsonify({
            'success': True,
            'route1': route1,
            'route2': route2,
            'total_distance': total_distance,
            'total_duration': total_duration,
            'combined_geometry': combined_geometry
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_route(start_coords, end_coords):
    """
    Calculate route between two points using route_optimizer with 3-tier fallback.
    
    Args:
        start_coords: [lon, lat] of starting point
        end_coords: [lon, lat] of ending point
    
    Returns:
        Dict with distance (km), duration (minutes), and geometry (list of [lat, lon])
    """
    return route_optimizer.calculate_route(start_coords, end_coords, config.ORS_API_KEY)

@app.route('/api/submit-trip', methods=['POST'])
def submit_trip():
    """Submit a new ambulance trip"""
    data = request.json
    
    try:
        # Get current odometer
        last_trip = AmbulanceTrip.query.order_by(AmbulanceTrip.id.desc()).first()
        km_reading_start = last_trip.km_reading_end if last_trip else config.INITIAL_ODOMETER
        
        # Calculate route
        pickup_coords = [data['pickup_lon'], data['pickup_lat']]
        hospital_coords = [config.HOSPITAL_COORDS[1], config.HOSPITAL_COORDS[0]]
        
        route1 = calculate_route(hospital_coords, pickup_coords)
        route2 = calculate_route(pickup_coords, hospital_coords)
        
        total_distance = route1['distance'] + route2['distance']
        total_duration = route1['duration'] + route2['duration']
        combined_geometry = route1['geometry'] + route2['geometry']
        
        # Calculate times
        departure_time = datetime.strptime(f"{data['date']} {data['time']}", "%Y-%m-%d %H:%M")
        arrival_time = departure_time + timedelta(minutes=total_duration)
        
        # Calculate end odometer
        km_reading_end = km_reading_start + total_distance
        
        # Create new trip
        new_trip = AmbulanceTrip(
            date=data['date'],
            time=data['time'],
            km_reading_start=km_reading_start,
            km_reading_end=km_reading_end,
            pickup_location=data['pickup_location'],
            pickup_lat=data['pickup_lat'],
            pickup_lon=data['pickup_lon'],
            patient_name=data['patient_name'],
            driver_name=data['driver_name'],
            purpose=data['purpose'],
            notes=data.get('notes', ''),
            distance_km=total_distance,
            duration_minutes=total_duration,
            departure_time=departure_time.strftime("%H:%M:%S"),
            arrival_time=arrival_time.strftime("%H:%M:%S"),
            route_geometry=json.dumps(combined_geometry)
        )
        
        db.session.add(new_trip)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'trip': new_trip.to_dict(),
            'route1': route1,
            'route2': route2,
            'total_distance': total_distance,
            'total_duration': total_duration
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    """Export all ambulance trips to CSV"""
    trips = AmbulanceTrip.query.order_by(AmbulanceTrip.created_at.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Date', 'Time', 'KM Reading Start', 'KM Reading End',
        'Pickup Location', 'Patient Name', 'Driver Name', 'Purpose',
        'Notes', 'Distance (km)', 'Duration (min)', 'Departure Time',
        'Arrival Time', 'Created At'
    ])
    
    # Write data
    for trip in trips:
        writer.writerow([
            trip.id, trip.date, trip.time, trip.km_reading_start,
            trip.km_reading_end, trip.pickup_location, trip.patient_name,
            trip.driver_name, trip.purpose, trip.notes, trip.distance_km,
            trip.duration_minutes, trip.departure_time, trip.arrival_time,
            trip.created_at.strftime("%Y-%m-%d %H:%M:%S") if trip.created_at else ''
        ])
    
    # Prepare file for download
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'ambulance_trips_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/get-isochrones', methods=['GET'])
def get_isochrones():
    """Get isochrone zones from hospital (3, 5, 7 minutes)"""
    hospital_coords = [config.HOSPITAL_COORDS[1], config.HOSPITAL_COORDS[0]]
    
    try:
        isochrones = []
        for minutes in [3, 5, 7]:
            isochrone = calculate_isochrone(hospital_coords, minutes * 60)
            isochrones.append({
                'minutes': minutes,
                'geometry': isochrone
            })
        
        return jsonify({'success': True, 'isochrones': isochrones})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_isochrone(coords, seconds):
    """Calculate isochrone using OpenRouteService"""
    url = 'https://api.openrouteservice.org/v2/isochrones/driving-car'
    
    headers = {
        'Authorization': config.ORS_API_KEY,
        'Content-Type': 'application/json'
    }
    
    body = {
        'locations': [coords],
        'range': [seconds]
    }
    
    response = requests.post(url, json=body, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        # Convert coordinates from lon,lat to lat,lon
        geometry = []
        for coord in data['features'][0]['geometry']['coordinates'][0]:
            geometry.append([coord[1], coord[0]])
        return geometry
    else:
        raise Exception(f"OpenRouteService API error: {response.status_code}")

@app.route('/api/get-route-frequency', methods=['GET'])
def get_route_frequency():
    """Analyze route frequency from historical data"""
    trips = AmbulanceTrip.query.all()
    
    # Create a dictionary to count route segments
    route_segments = {}
    
    for trip in trips:
        if trip.route_geometry:
            geometry = json.loads(trip.route_geometry)
            # Create segments from consecutive points
            for i in range(len(geometry) - 1):
                # Create a segment key (rounded to reduce precision)
                p1 = (round(geometry[i][0], 4), round(geometry[i][1], 4))
                p2 = (round(geometry[i+1][0], 4), round(geometry[i+1][1], 4))
                segment = tuple(sorted([p1, p2]))  # Sort to make direction-independent
                
                route_segments[segment] = route_segments.get(segment, 0) + 1
    
    # Convert to list with frequency
    max_frequency = max(route_segments.values()) if route_segments else 1
    
    segments_list = []
    for segment, count in route_segments.items():
        segments_list.append({
            'coordinates': [[segment[0][0], segment[0][1]], [segment[1][0], segment[1][1]]],
            'frequency': count,
            'normalized_frequency': count / max_frequency
        })
    
    return jsonify({
        'success': True,
        'segments': segments_list,
        'max_frequency': max_frequency
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# app.py
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import requests

def create_app():
    app = Flask(__name__, static_folder="frontend", template_folder="templates")
    app.config.from_pyfile("config.py", silent=True)
    CORS(app)

    # import and register API blueprint
    from backend.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    # serve index
    @app.route("/", methods=["GET"])
    def index():
        return app.send_static_file("index.html")

    # allow static files under /frontend
    @app.route("/frontend/<path:p>", methods=["GET"])
    def frontend_static(p):
        return send_from_directory("frontend", p)

    return app

if __name__ == "__main__":
    os.makedirs("instance", exist_ok=True)
    app = create_app()
    app.run(debug=True)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    # Calculate route using ORS and get distance (km reading start is always 0)
    route = client.directions(
        coordinates=[[IITB_LON, IITB_LAT], [data['pickup_lon'], data['pickup_lat']], [IITB_LON, IITB_LAT]],
        profile='driving-car'
    )
    distance = route['routes'][0]['summary']['distance'] / 1000  # in km
    conn = get_db()
    conn.execute('INSERT INTO trips (pickup_lat, pickup_lon, time_taken, distance) VALUES (?, ?, ?, ?)',
                 (data['pickup_lat'], data['pickup_lon'], ..., distance))
    conn.commit()
    return {"status": "success", "data": data}

@app.route('/api/analysis/isochrones')
def api_isochrones():
    try:
        # Example: Generate isochrones for IITB hospital
        center = [IITB_LON, IITB_LAT]  # Replace with actual coordinates
        intervals = [180, 300, 420]  # seconds: 3min, 5min, 7min
        isochrones = client.isochrones(
            locations=[center],
            profile='driving-car',
            range=intervals
        )
        return jsonify({'isochrones': isochrones['features']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/frequency')
def api_frequency():
    try:
        conn = get_db()
        trips = conn.execute('SELECT pickup_lat, pickup_lon FROM trips').fetchall()
        # Example: Count frequency of each route (simplified)
        route_counts = {}
        for trip in trips:
            key = f"{trip['pickup_lat']},{trip['pickup_lon']}"
            route_counts[key] = route_counts.get(key, 0) + 1
        # Prepare data for frontend (color coding based on frequency)
        routes = []
        for key, count in route_counts.items():
            lat, lon = map(float, key.split(','))
            color = 'red' if count > 5 else 'orange' if count > 2 else 'green'
            routes.append({'coords': [[IITB_LAT, IITB_LON], [lat, lon]], 'color': color, 'count': count})
        return jsonify({'routes': routes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

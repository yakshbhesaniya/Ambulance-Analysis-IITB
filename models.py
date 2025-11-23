from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class AmbulanceTrip(db.Model):
    __tablename__ = 'ambulance_trips'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    km_reading_start = db.Column(db.Float, nullable=False)
    km_reading_end = db.Column(db.Float, nullable=False)
    pickup_location = db.Column(db.String(100), nullable=False)
    pickup_lat = db.Column(db.Float, nullable=False)
    pickup_lon = db.Column(db.Float, nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    distance_km = db.Column(db.Float, nullable=False)
    duration_minutes = db.Column(db.Float, nullable=False)
    departure_time = db.Column(db.String(20), nullable=False)
    arrival_time = db.Column(db.String(20), nullable=False)
    route_geometry = db.Column(db.Text)  # Store route as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'time': self.time,
            'km_reading_start': self.km_reading_start,
            'km_reading_end': self.km_reading_end,
            'pickup_location': self.pickup_location,
            'pickup_lat': self.pickup_lat,
            'pickup_lon': self.pickup_lon,
            'patient_name': self.patient_name,
            'driver_name': self.driver_name,
            'purpose': self.purpose,
            'notes': self.notes,
            'distance_km': self.distance_km,
            'duration_minutes': self.duration_minutes,
            'departure_time': self.departure_time,
            'arrival_time': self.arrival_time,
            'route_geometry': self.route_geometry,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

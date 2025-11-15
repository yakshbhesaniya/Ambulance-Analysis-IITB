# backend/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import config

Base = declarative_base()
engine = create_engine(config.DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)

    # automatic / computed
    request_time = Column(DateTime, default=datetime.utcnow)   # form submit time (UTC)
    departure_time = Column(DateTime, nullable=True)           # when ambulance departed (current)
    arrival_time = Column(DateTime, nullable=True)             # when ambulance returned to hospital
    date = Column(DateTime, nullable=True)                     # date part (duplicate of request_time)

    # form fields
    location_name = Column(String(200), nullable=False)        # "From" location name (user input)
    patient_name = Column(String(200), nullable=True)          # User / patient
    driver_name = Column(String(200), nullable=True)
    purpose = Column(String(100), nullable=True)               # pickup / drop

    # coordinates & destination (always hospital)
    pickup_lat = Column(Float, nullable=False)
    pickup_lng = Column(Float, nullable=False)

    # odometer & kms
    start_odometer = Column(Float, nullable=True)              # Km Reading (before trip)
    distance_km = Column(Float, nullable=True)                 # computed distance (route_km)
    next_odometer = Column(Float, nullable=True)               # start_odometer + distance_km

    # ORS metrics
    route_seconds = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)
    route_geojson = Column(Text, nullable=True)  # store GeoJSON string

def init_db():
    Base.metadata.create_all(engine)

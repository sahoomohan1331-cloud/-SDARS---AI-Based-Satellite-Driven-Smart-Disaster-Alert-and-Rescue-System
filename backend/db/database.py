import os
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Database setup
# Using SQLite for ease of use, but engineered for easy swap to PostgreSQL
DB_URL = "sqlite:///./sdars_database.db"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    location_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    overall_risk = Column(String)
    primary_threat = Column(String)
    
    # Store full JSON for flexibility
    weather_data = Column(JSON)
    risk_scores = Column(JSON) # {fire: 0.3, flood: 0.1, cyclone: 0.0}
    
    # Relationships
    alerts = relationship("AlertRecord", back_populates="prediction")

class AlertRecord(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String) # SMS, Email, System
    severity = Column(String)
    recipient = Column(String)
    message = Column(String)
    status = Column(String) # sent, failed, pending

    prediction = relationship("PredictionRecord", back_populates="alerts")

class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    coordinates = Column(JSON)  # List of [lat, lon] points
    severity_threshold = Column(String)
    notification_channels = Column(JSON)
    recipient_emails = Column(JSON, default=[]) # List of custom emails for this zone
    user_id = Column(String, default="default_user")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    is_verified = Column(Integer, default=0) # 0=Pending, 1=Verified
    otp_code = Column(String, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    subscribed_zones = Column(JSON, default=[]) # List of zone IDs
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemSettings(Base):
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True)
    value = Column(JSON)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CrowdReport(Base):
    """Sprint 3: Citizen ground-truth observations"""
    __tablename__ = "crowd_reports"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    latitude = Column(Float)
    longitude = Column(Float)
    location_name = Column(String, nullable=True)
    report_type = Column(String)  # smoke, flooding, tremor, blocked_road, storm_damage
    description = Column(String)
    severity = Column(String, default="MODERATE")  # LOW, MODERATE, HIGH, CRITICAL
    reporter_id = Column(String, nullable=True)  # Anonymous if null
    is_verified = Column(Integer, default=0)  # 0=pending, 1=verified, -1=rejected
    photo_url = Column(String, nullable=True)

class RiverGauge(Base):
    """Sprint 5: River level monitoring (simulated for demo)"""
    __tablename__ = "river_gauges"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    station_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    water_level_m = Column(Float)  # Current water level in meters
    danger_level_m = Column(Float, default=10.0)  # Threshold for danger
    flow_rate = Column(Float, nullable=True)  # m3/s
    status = Column(String, default="NORMAL")  # NORMAL, ALERT, DANGER, SEVERE

class Resource(Base):
    """Sprint 4: Emergency resource inventory"""
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    resource_type = Column(String)  # shelter, hospital, fire_station, vehicle, warehouse
    latitude = Column(Float)
    longitude = Column(Float)
    capacity = Column(Integer, default=0)
    current_occupancy = Column(Integer, default=0)
    status = Column(String, default="AVAILABLE")  # AVAILABLE, FULL, DAMAGED, OFFLINE
    contact_info = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HistoricalDisaster(Base):
    """Sprint 5: Past disaster events for frequency analysis & benchmarking"""
    __tablename__ = "historical_disasters"

    id = Column(Integer, primary_key=True, index=True)
    disaster_name = Column(String)
    disaster_type = Column(String)  # cyclone, flood, heatwave, landslide, drought
    location_name = Column(String)
    country = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    year = Column(Integer)
    severity = Column(String)  # MODERATE, HIGH, CRITICAL
    casualties = Column(Integer, default=0)
    economic_loss_usd_m = Column(Float, default=0.0)
    description = Column(String)

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

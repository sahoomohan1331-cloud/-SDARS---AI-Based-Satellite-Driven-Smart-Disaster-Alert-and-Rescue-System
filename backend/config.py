"""
Configuration settings for SDARS AI System
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
NASA_API_KEY = os.getenv('NASA_API_KEY', 'DEMO_KEY')
SENTINEL_HUB_CLIENT_ID = os.getenv('SENTINEL_HUB_CLIENT_ID', '')
SENTINEL_HUB_CLIENT_SECRET = os.getenv('SENTINEL_HUB_CLIENT_SECRET', '')

# Alert Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_EMAIL = os.getenv('SMTP_EMAIL', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Database Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'sdars_db')

# Server Configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'True').lower() == 'true'

# Model Paths
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
FIRE_MODEL_PATH = os.path.join(MODELS_DIR, 'fire_detection_model.h5')
FLOOD_MODEL_PATH = os.path.join(MODELS_DIR, 'flood_detection_model.h5')
CYCLONE_MODEL_PATH = os.path.join(MODELS_DIR, 'cyclone_prediction_model.h5')
WEATHER_MODEL_PATH = os.path.join(MODELS_DIR, 'weather_timeseries_model.pkl')

# Data Storage
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SATELLITE_DATA_DIR = os.path.join(DATA_DIR, 'satellite')
WEATHER_DATA_DIR = os.path.join(DATA_DIR, 'weather')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')

# Disaster Thresholds
FIRE_CONFIDENCE_THRESHOLD = 0.75
FLOOD_CONFIDENCE_THRESHOLD = 0.70
CYCLONE_CONFIDENCE_THRESHOLD = 0.65

# Weather Change Thresholds (for anomaly detection)
TEMP_CHANGE_THRESHOLD = 5.0  # Celsius
PRESSURE_CHANGE_THRESHOLD = 10.0  # hPa
HUMIDITY_CHANGE_THRESHOLD = 20.0  # %
RAINFALL_THRESHOLD = 50.0  # mm/hour

# Locations to Monitor (Global Scope - All Continents)
MONITORED_LOCATIONS = [
    # Asia
    {"name": "Tokyo, JP", "lat": 35.6762, "lon": 139.6503, "region": "Asia"},
    {"name": "Mumbai, IN", "lat": 19.0760, "lon": 72.8777, "region": "Asia"},
    {"name": "Singapore, SG", "lat": 1.3521, "lon": 103.8198, "region": "Asia"},
    {"name": "Seoul, KR", "lat": 37.5665, "lon": 126.9780, "region": "Asia"},
    {"name": "Bangkok, TH", "lat": 13.7563, "lon": 100.5018, "region": "Asia"},
    # Europe
    {"name": "London, UK", "lat": 51.5074, "lon": -0.1278, "region": "Europe"},
    {"name": "Paris, FR", "lat": 48.8566, "lon": 2.3522, "region": "Europe"},
    {"name": "Berlin, DE", "lat": 52.5200, "lon": 13.4050, "region": "Europe"},
    {"name": "Madrid, ES", "lat": 40.4168, "lon": -3.7038, "region": "Europe"},
    # Americas
    {"name": "New York, US", "lat": 40.7128, "lon": -74.0060, "region": "Americas"},
    {"name": "Los Angeles, US", "lat": 34.0522, "lon": -118.2437, "region": "Americas"},
    {"name": "São Paulo, BR", "lat": -23.5505, "lon": -46.6333, "region": "Americas"},
    {"name": "Toronto, CA", "lat": 43.6532, "lon": -79.3832, "region": "Americas"},
    # Africa & Middle East
    {"name": "Cairo, EG", "lat": 30.0444, "lon": 31.2357, "region": "Africa"},
    {"name": "Lagos, NG", "lat": 6.5244, "lon": 3.3792, "region": "Africa"},
    {"name": "Dubai, AE", "lat": 25.2048, "lon": 55.2708, "region": "Middle East"},
    # Oceania
    {"name": "Sydney, AU", "lat": -33.8688, "lon": 151.2093, "region": "Oceania"},
    {"name": "Auckland, NZ", "lat": -36.8509, "lon": 174.7645, "region": "Oceania"},
]

# Create necessary directories
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(SATELLITE_DATA_DIR, exist_ok=True)
os.makedirs(WEATHER_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

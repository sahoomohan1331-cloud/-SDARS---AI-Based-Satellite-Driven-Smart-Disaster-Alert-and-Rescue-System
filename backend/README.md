# 🛰️ SDARS - AI-Based Satellite-Driven Smart Disaster Alert and Rescue System

## Overview

SDARS is a **multi-modal AI system** that predicts natural disasters by analyzing:
- 🛰️ **Satellite imagery** (thermal data, vegetation indices, water detection)
- 🌡️ **Weather time-series data** (temperature, pressure, humidity changes over time)

The system detects:
- 🔥 **Forest Fires** - Using thermal anomalies + weather patterns
- 🌊 **Floods** - Using water indices + rainfall data
- 🌪️ **Cyclones** - Using pressure drops + wind patterns

## Key Features

✅ **Multi-Modal Analysis** - Combines satellite + weather data  
✅ **Time-Series Tracking** - Monitors weather changes before disasters  
✅ **Real-Time Monitoring** - Continuous data collection and analysis  
✅ **NASA FIRMS Integration** - Active fire detection from VIIRS satellite  
✅ **REST API** - Easy integration with any frontend  
✅ **Alert System** - Automated warnings for high-risk areas  

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  DATA SOURCES                       │
├─────────────────────────────────────────────────────┤
│  NASA FIRMS  │  OpenWeather  │  Sentinel Hub       │
│  (Fire Data) │  (Weather)    │  (Satellite Images) │
└──────┬────────────────┬────────────────┬───────────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────────────────────────────────────────────┐
│              DATA COLLECTORS                        │
├─────────────────────────────────────────────────────┤
│  • Satellite Collector (thermal, NDVI, NDWI)       │
│  • Weather Collector (current + historical)        │
│  • Change Calculator (detect rapid changes)        │
└──────┬──────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│           MULTI-MODAL AI PREDICTOR                  │
├─────────────────────────────────────────────────────┤
│  • Feature Extraction (satellite + weather)        │
│  • Fire Risk Model (thermal + weather)             │
│  • Flood Risk Model (NDWI + rainfall)              │
│  • Cyclone Risk Model (pressure + wind)            │
└──────┬──────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│              OUTPUT & ALERTS                        │
├─────────────────────────────────────────────────────┤
│  • REST API Endpoints                              │
│  • Real-Time Monitoring Service                    │
│  • Email/SMS Alerts (optional)                     │
└─────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys**
   
   Edit `.env` file and add your API keys:
   ```env
   OPENWEATHER_API_KEY=your_key_here
   NASA_API_KEY=DEMO_KEY
   ```
   
   **Get Free API Keys:**
   - OpenWeatherMap: https://openweathermap.org/api (Free tier available)
   - NASA API: https://api.nasa.gov/ (Use `DEMO_KEY` for testing)

4. **Test the installation**
   ```bash
   python test_system.py
   ```

---

## Usage

### 1. Run Real-Time Monitor (Demo Mode)

Collects satellite + weather data and runs AI predictions:

```bash
python services/realtime_monitor.py
```

**Output:**
```
🛰️  SDARS Real-Time Monitor initialized
📍 Monitoring 5 locations

📡 Collecting data for Mumbai...
  ✓ Weather: 32°C, 65% humidity, 1010 hPa
  ✓ Weather changes: temp Δ6h=3.2°C, pressure Δ6h=-2.1 hPa
  ✓ NASA FIRMS: 0 active fire points detected
  ✓ Satellite imagery processed

🤖 Running AI analysis for Mumbai...
🚨 ALERT for Mumbai!
   Primary Threat: FIRE
   Risk Level: MEDIUM
   Confidence: 62%
```

### 2. Start API Server

Launch the REST API for frontend integration:

```bash
python api/server.py
```

**API will be available at:** `http://localhost:8000`

**API Documentation:** `http://localhost:8000/docs`

### 3. Test Individual Components

**Weather Data Collection:**
```bash
python data_collectors/weather_collector.py
```

**Satellite Data Collection:**
```bash
python data_collectors/satellite_collector.py
```

**AI Prediction Engine:**
```bash
python ai_models/multi_modal_predictor.py
```

---

## API Endpoints

### POST `/api/predict`
Run disaster prediction for a location

**Request:**
```json
{
  "lat": 19.0760,
  "lon": 72.8777,
  "name": "Mumbai"
}
```

**Response:**
```json
{
  "timestamp": "2026-01-30T17:15:00",
  "primary_threat": "fire",
  "overall_risk_level": "MEDIUM",
  "fire": {
    "risk_level": "MEDIUM",
    "confidence": 0.62,
    "reasons": [
      "High temperature, low humidity, strong winds",
      "Rapid temperature increase: +5.2°C in 6h"
    ]
  },
  "flood": {...},
  "cyclone": {...}
}
```

### GET `/api/weather/{lat}/{lon}`
Get current weather data

### GET `/api/fires/{lat}/{lon}`
Get NASA FIRMS fire hotspots

### GET `/api/locations`
Get list of monitored locations

---

## How the Multi-Modal AI Works

### 1. **Satellite Feature Extraction**
- **Thermal Analysis**: Detects hot spots and temperature anomalies
- **NDVI (Vegetation Index)**: Measures vegetation health
- **NDWI (Water Index)**: Detects water bodies and floods
- **Spectral Features**: Multi-band analysis (Red, NIR, Thermal)

### 2. **Weather Feature Extraction**
- **Current State**: Temperature, pressure, humidity, wind
- **Time-Series Changes**: Rate of change over 1h, 3h, 6h, 12h
- **Trend Analysis**: Hourly rates of change
- **Historical Statistics**: Mean, std deviation over 3-7 days

### 3. **Combined Prediction**

**Fire Detection:**
- ✓ Thermal hotspots (satellite) + High temp (weather)
- ✓ Low NDVI (satellite) + Low humidity (weather)
- ✓ Rapid temperature rise (weather change)

**Flood Detection:**
- ✓ High NDWI (satellite) + Heavy rainfall (weather)
- ✓ Increased water coverage (satellite) + Humidity spike (weather change)

**Cyclone Detection:**
- ✓ Dense clouds (satellite) + Pressure drop (weather change)
- ✓ Rotating patterns (satellite) + Strong winds (weather)

---

## Configuration

Edit `config.py` to customize:

```python
# Disaster prediction thresholds
FIRE_CONFIDENCE_THRESHOLD = 0.75
FLOOD_CONFIDENCE_THRESHOLD = 0.70
CYCLONE_CONFIDENCE_THRESHOLD = 0.65

# Weather change thresholds
TEMP_CHANGE_THRESHOLD = 5.0  # Celsius
PRESSURE_CHANGE_THRESHOLD = 10.0  # hPa
RAINFALL_THRESHOLD = 50.0  # mm/hour

# Monitored locations
MONITORED_LOCATIONS = [
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
    # Add more locations...
]
```

---

## Future Enhancements

🚀 **Machine Learning Models**
- Train CNNs on real satellite imagery datasets
- LSTM for time-series weather prediction
- Transfer learning from pre-trained models

🚀 **Real Satellite Data Integration**
- Sentinel Hub API for high-res imagery
- Google Earth Engine integration
- MODIS thermal data

🚀 **Advanced Features**
- Evacuation route planning
- Resource allocation optimization
- Social media sentiment analysis
- Real-time drone integration

🚀 **Production Deployment**
- Docker containerization
- Cloud deployment (AWS/GCP/Azure)
- Database integration (MongoDB/PostgreSQL)
- Scalable microservices architecture

---

## Technologies Used

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.8+ |
| **AI/ML** | TensorFlow, Keras, PyTorch, Scikit-learn |
| **Data Processing** | NumPy, Pandas, OpenCV |
| **APIs** | NASA FIRMS, OpenWeatherMap, Sentinel Hub |
| **Web Server** | FastAPI, Uvicorn |
| **Visualization** | Matplotlib, Plotly |

---

## License

MIT License - Feel free to use for your project!

---

## Contact & Support

For questions or contributions:
- Create an issue on GitHub
- Email: your-email@example.com

---

**Built with ❤️ for disaster prevention and saving lives**

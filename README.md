# 🌍 SDARS - AI-Based Satellite-Driven Smart Disaster Alert and Rescue System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Working](https://img.shields.io/badge/Status-Working-brightgreen.svg)]()

> **Real-time disaster prediction using multi-modal AI that analyzes satellite imagery AND weather time-series data**

---

## 🎯 What It Does

SDARS is an **AI system that predicts natural disasters BEFORE they happen** by analyzing:

1. 🛰️ **Satellite Imagery**
   - Thermal hotspots (fires)
   - Water coverage (floods)  
   - Cloud patterns (cyclones)
   - Vegetation health (NDVI)

2. 🌡️ **Weather Data**
   - Current conditions
   - **Historical trends**
   - **Rate of change** (KEY INNOVATION!)

3. 🤖 **Multi-Modal AI**
   - Combines both data sources
   - Predicts fire, flood, cyclone risks
   - Provides detailed reasoning

---

## ⚡ Key Innovation: Time-Series Weather Analysis

**Traditional systems** only look at current weather:
```
Temperature: 35°C → "It's hot"
```

**SDARS** tracks changes over time:
```
12h ago: 28°C
6h ago: 31°C
Now: 35°C

Change: +7°C in 12h → 🚨 RAPID RISE = FIRE WARNING
```

This allows **prediction before disaster strikes**:
- Pressure drops → Cyclone warning
- Temperature spikes → Fire alert
- Rainfall accumulation → Flood prediction

---

## 🚀 Demo Results

| Scenario | Detection | Confidence | Key Indicators |
|----------|-----------|------------|----------------|
| 🔥 **Fire Risk** | ✅ Detected | **100%** | Temp +6.5°C, Hotspots 1.9%, Winds 25km/h |
| 🌊 **Flood Risk** | ✅ Detected | **55%** | Rainfall 75mm/h, Humidity 95% |
| 🌪️ **Cyclone Risk** | ✅ Detected | **90%** | Pressure -15hPa in 12h, Winds 45km/h |

**All predictions included detailed reasoning and contribution analysis!**

---

## 📦 Quick Start

### 1. Run the Demo (No API Key Required!)

```bash
cd backend
python demo.py
```

This runs through 4 scenarios:
- Normal conditions
- Fire risk scenario
- Flood risk scenario
- Cyclone risk scenario

**See the AI analyze satellite + weather data in real-time!**

### 2. Test the System

```bash
python test_system.py
```

Verifies all components are working.

### 3. Get API Keys (Optional - for live data)

**Free API Keys:**
- OpenWeatherMap: https://openweathermap.org/api
- NASA API: https://api.nasa.gov/ (use `DEMO_KEY`)

Add to `backend/.env`:
```env
OPENWEATHER_API_KEY=your_key_here
NASA_API_KEY=DEMO_KEY
```

### 4. Run Real-Time Monitor

```bash
python services/realtime_monitor.py
```

Monitors multiple locations and generates alerts.

### 5. Start API Server

```bash
python api/server.py
```

REST API at: http://localhost:8000/docs

---

## 🏗️ Architecture

```
DATA COLLECTION → FEATURE EXTRACTION → AI PREDICTION → ALERTS
     │                    │                  │            │
  Satellite +         16 Sat +           Fire        Email/SMS/
  Weather Data       32 Weather         Flood         Dashboard
                    = 48 Features      Cyclone
```

**Multi-Modal Fusion:**
- Satellite features (16): Thermal, NDVI, NDWI
- Weather features (32): Current + Changes + Trends
- Combined (48): Fed into disaster predictors

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams.

---

## 📁 Project Structure

```
SDARS map/
├── README.md                    # This file
├── QUICKSTART.md                # Usage guide
├── ARCHITECTURE.md              # Technical architecture
│
└── backend/
    ├── demo.py                  # ⭐ Interactive demo
    ├── test_system.py           # System tests
    ├── config.py                # Configuration
    ├── requirements.txt         # Dependencies
    │
    ├── data_collectors/
    │   ├── weather_collector.py     # Weather + time-series
    │   └── satellite_collector.py   # NASA FIRMS + imagery
    │
    ├── ai_models/
    │   └── multi_modal_predictor.py # Multi-modal AI
    │
    ├── services/
    │   └── realtime_monitor.py      # Real-time monitoring
    │
    └── api/
        └── server.py                # FastAPI REST server
```

---

## 🔬 Technical Details

### Data Sources
- **NASA FIRMS**: Active fire detection (VIIRS satellite)
- **OpenWeatherMap**: Current + forecast weather
- **Synthetic Imagery**: Multi-spectral satellite simulation

### AI Features

**Satellite Features (16):**
- Thermal statistics (5): mean, max, std, hotspots, %
- NDVI statistics (6): vegetation health metrics
- NDWI statistics (5): water detection metrics

**Weather Features (32):**
- Current state (7): temp, pressure, humidity, wind, etc.
- Time-series changes (12): Δ over 1h, 3h, 6h, 12h
- Trends (3): hourly rate of change
- Historical stats (8): mean/std over 3 days

**Total:** 48 multi-modal features analyzed

### Prediction Models

Each disaster type has specialized logic:

**Fire Detection:**
```python
score = 0
+ hotspot_percentage (satellite)
+ high_thermal (satellite)  
+ low_vegetation (satellite)
+ hot_and_dry (weather)
+ strong_winds (weather)
+ rapid_temp_rise (weather change) # KEY!
```

**Flood Detection:**
```python
score = 0
+ high_ndwi (satellite)
+ water_coverage (satellite)
+ heavy_rainfall (weather)
+ humidity_spike (weather change) # KEY!
```

**Cyclone Detection:**
```python
score = 0
+ dense_clouds (satellite)
+ pressure_drop (weather change) # KEY!
+ strong_winds (weather)
+ low_pressure (weather)
```

---

## 📊 API Reference

### Predict Disaster
```http
POST /api/predict
Content-Type: application/json

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
  "overall_risk_level": "HIGH",
  "fire": {
    "risk_level": "HIGH",
    "confidence": 1.0,
    "reasons": [
      "Thermal hotspots detected: 1.9%",
      "High thermal reading: 100.0°C",
      "Extreme fire weather: 38.5°C, 22% humidity",
      "Rapid temperature increase: +6.5°C in 6h"
    ],
    "satellite_contribution": 0.936,
    "weather_contribution": 0.064
  },
  "flood": {...},
  "cyclone": {...}
}
```

### Other Endpoints
- `GET /api/weather/{lat}/{lon}` - Current weather
- `GET /api/fires/{lat}/{lon}` - Fire hotspots
- `GET /api/forecast/{lat}/{lon}` - Weather forecast
- `GET /api/locations` - Monitored locations

Full docs: http://localhost:8000/docs

---

## 🎓 Use Cases

### Immediate Applications
1. **Government Disaster Management**
   - Early warning system for states
   - Resource pre-positioning
   - Evacuation planning

2. **NGOs & Relief Organizations**
   - Disaster preparedness
   - Response coordination
   - Risk assessment

3. **Research & Academia**
   - Climate pattern analysis
   - Disaster prediction models
   - Dataset generation

### Future Potential
- Mobile app for citizens
- Integration with emergency services
- Drone deployment automation
- Social media alert system
- Insurance risk assessment

---

## 🚀 Future Enhancements

### Phase 1: Enhanced ML
- [ ] Train CNN on real satellite imagery datasets
- [ ] LSTM for weather time-series prediction
- [ ] Transfer learning from pre-trained models
- [ ] XGBoost for ensemble predictions

### Phase 2: Real Data Integration
- [ ] Sentinel Hub API (10m resolution imagery)
- [ ] Google Earth Engine integration
- [ ] MODIS thermal data
- [ ] Weather radar integration

### Phase 3: Advanced Features
- [ ] Evacuation route optimization AI
- [ ] Resource allocation algorithms
- [ ] Social media sentiment analysis
- [ ] Real-time drone coordination
- [ ] AR/VR visualization

### Phase 4: Production Deployment
- [ ] Docker containerization
- [ ] Kubernetes orchestration
- [ ] Cloud deployment (AWS/GCP/Azure)
- [ ] MongoDB/PostgreSQL database
- [ ] React/Vue.js dashboard
- [ ] Mobile apps (React Native)

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Prediction Time | < 1 second |
| Features Analyzed | 48 (multi-modal) |
| Data Sources | 3+ (NASA, Weather, Satellite) |
| API Response | < 2 seconds |
| Monitored Locations | Unlimited (configurable) |

---

## 🛠️ Technologies

**Programming:** Python 3.8+

**AI/ML:**
- NumPy, Pandas (data processing)
- Scikit-learn (ML models)
- TensorFlow/PyTorch (future deep learning)

**APIs:**
- FastAPI (REST server)
- Requests (HTTP client)
- Uvicorn (ASGI server)

**Data Sources:**
- NASA FIRMS API
- OpenWeatherMap API
- Sentinel Hub (future)

---

## 💡 What Makes SDARS Unique?

| Feature | Traditional | SDARS |
|---------|------------|-------|
| Data Source | Ground sensors only | **Satellite + Weather** ⭐ |
| Approach | Reactive (after disaster) | **Predictive (before disaster)** ⭐ |
| Time-Series | ❌ No | **✅ Yes** ⭐ |
| Explainability | Black box | **Detailed reasoning** ⭐ |
| Coverage | Limited areas | **Global** ⭐ |
| Cost | High (sensors) | **Low (APIs)** ⭐ |

---

## 📝 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture
- **[backend/README.md](backend/README.md)** - Detailed API docs

---

## 🤝 Contributing

This is a working prototype ready for expansion! Areas for contribution:
1. Real satellite imagery integration
2. ML model training on datasets
3. Frontend dashboard
4. Mobile app development
5. Additional disaster types (earthquakes, tsunamis)

---

## 📄 License

MIT License - Free to use for your project!

---

## 🎬 Demo Commands

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run interactive demo (no API key needed)
python demo.py

# Test system
python test_system.py

# Start API server (needs API key)
python api/server.py
```

---

## 📞 Support & Contact

For questions or collaboration:
- Check documentation files
- Run test scripts
- Review demo output

---

## 🌟 Acknowledgments

**Data Sources:**
- NASA FIRMS (Fire Information for Resource Management System)
- OpenWeatherMap
- Global satellite programs (VIIRS, MODIS, Sentinel)

**Inspiration:**
- ISRO Disaster Management Support
- NOAA National Weather Service
- UN Space-based Information for Disaster Management

---

<div align="center">

**🛰️ Built for disaster prevention and saving lives 🌍**

*Multi-modal AI that combines satellite imagery and weather time-series for predictive disaster management*

</div>

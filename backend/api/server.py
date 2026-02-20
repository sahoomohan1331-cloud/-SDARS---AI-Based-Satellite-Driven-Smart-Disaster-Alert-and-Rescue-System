"""
FastAPI REST API Server - RELOAD BUMP
Provides endpoints for the frontend to access AI predictions
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sys
import os
import asyncio
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors.weather_collector import WeatherDataCollector
from data_collectors.satellite_collector import SatelliteDataCollector
from ai_models.multi_modal_predictor import MultiModalPredictor
from db.database import init_db, get_db, PredictionRecord, AlertRecord
from services.alert_manager import alert_manager
from services.geocoder import geocode_city, reverse_geocode
from services.real_shelters import real_shelter_finder
from services.route_optimizer import route_optimizer
from api.auth_routes import router as auth_router # New Auth Router
import config

# Initialize FastAPI
app = FastAPI(
    title="SDARS API",
    description="AI-Based Satellite-Driven Smart Disaster Alert and Rescue System",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Changed to False for wildcard compatibility
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"]) 

# Initialize services
weather_collector = WeatherDataCollector()
satellite_collector = SatelliteDataCollector()
predictor = MultiModalPredictor()

@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ System Startup: Database initialized.")

# Pydantic models
class Location(BaseModel):
    name: str
    lat: float
    lon: float

class PredictionRequest(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    name: str

class DisasterPrediction(BaseModel):
    risk_level: str
    confidence: float
    reasons: List[str]

class SettingsUpdate(BaseModel):
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    alert_email_to: Optional[str] = None

# ... existing code ...

@app.get("/api/settings")
async def get_settings(db: Session = Depends(get_db)):
    """Fetch current system configuration"""
    from db.database import SystemSettings
    settings = db.query(SystemSettings).all()
    return {s.key: s.value for s in settings}

@app.post("/api/settings/update")
async def update_settings(request: SettingsUpdate, db: Session = Depends(get_db)):
    """Update system configuration dynamically"""
    from db.database import SystemSettings
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = SystemSettings(key=key, value=value)
            db.add(setting)
    
    db.commit()
    # Refresh the advanced alert system instance
    advanced_alert_system.load_settings_from_db(db)
    return {"status": "success", "message": "Settings updated"}

# API Endpoints

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "SDARS API is running",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "weather_api": bool(config.OPENWEATHER_API_KEY),
            "satellite_api": bool(config.NASA_API_KEY),
            "ai_models": True,
        },
        "timestamp": datetime.now().isoformat()
    }

def _get_lite_risk(lat: float, lon: float) -> Dict:
    """
    EXTREMELY FAST risk check for autocomplete suggestions.
    Checks against active alert zones without hitting external APIs.
    """
    active_alerts = advanced_alert_system.get_active_alerts()
    
    # Simple proximity check (if within ~25km / 0.2 degrees)
    for alert in active_alerts:
        a_loc = alert.get('location', {})
        if a_loc.get('lat') and a_loc.get('lon'):
            dist = ((lat - a_loc['lat'])**2 + (lon - a_loc['lon'])**2)**0.5
            if dist < 0.2:
                return {
                    "level": alert['severity'],
                    "threat": alert['disaster_type'].upper()
                }
    
    return {"level": "NORMAL", "threat": "SAFE"}

@app.get("/api/locations")
async def get_monitored_locations():
    """Get list of monitored locations"""
    return {
        "locations": config.MONITORED_LOCATIONS,
        "count": len(config.MONITORED_LOCATIONS)
    }

# In-memory cache for predictions (Simple optimization for demo)
PREDICTION_CACHE = {}
CACHE_DURATION_MINUTES = 15

@app.post("/api/predict")
async def predict_disaster(request: PredictionRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Main prediction endpoint
    Collects satellite + weather data and runs AI prediction
    """
    try:
        lat, lon = request.lat, request.lon
        name = request.name

        # If coordinates not provided, resolve by name
        if lat is None or lon is None:
            coords = geocode_city(name)
            if coords:
                lat, lon = coords['lat'], coords['lon']
            else:
                # Use a fallback or raise
                print(f"⚠️ Geo-Resolution Failed for '{name}'. Using (0,0) fallback.")
                lat, lon = 0.0, 0.0
        
        # If name is generic, try to resolve a real location name
        if name and (name.startswith("Sector ") or name.startswith("Route Waypoint ")):
            try:
                from services.geocoder import reverse_geocode
                real_name = reverse_geocode(lat, lon)
                if real_name and not real_name.startswith("("):
                    print(f"✅ Resolved '{name}' -> '{real_name}'")
                    name = real_name
            except Exception as e:
                print(f"⚠️ Reverse geocode failed for generic name: {e}")
        
        # ⚡ CACHE CHECK
        cache_key = f"{round(lat, 3)}_{round(lon, 3)}"
        cached = PREDICTION_CACHE.get(cache_key)
        if cached:
            elapsed = (datetime.now() - cached['timestamp']).total_seconds() / 60
            if elapsed < CACHE_DURATION_MINUTES:
                print(f"🚀 Serving cached prediction for {name} ({elapsed:.1f}m old)")
                return cached['data']
        
        # COLLECT DATA IN PARALLEL! (Uses Python Threads for synchronous collector methods)
        print(f"📡 Launching Parallel Intelligence Gathering for {name}...")
        
        # Helper for timeouts
        async def run_safe(func, *args, timeout=5, **kwargs):
            try:
                # Run the synchronous function in a thread with timeout
                return await asyncio.wait_for(asyncio.to_thread(func, *args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                print(f"⚠️ TIMEOUT: {func.__name__} took >{timeout}s")
                return None
            except Exception as e:
                print(f"⚠️ ERROR: {func.__name__} failed: {e}")
                return None

        results = await asyncio.gather(
            run_safe(weather_collector.get_current_weather, lat, lon, timeout=10),
            run_safe(weather_collector.get_historical_weather, lat, lon, days_back=3, timeout=3),
            run_safe(satellite_collector.get_nasa_firms_data, lat, lon, radius_km=50, timeout=5),
            run_safe(satellite_collector.get_real_satellite_data, lat, lon, timeout=5),
            run_safe(real_shelter_finder.get_nearest_shelters, lat, lon, limit=5, timeout=4)
        )
        
        current_weather = results[0]
        import pandas as pd
        historical_weather = results[1] if results[1] is not None else pd.DataFrame()
        fire_hotspots = results[2] if results[2] is not None else []
        satellite_data = results[3]
        real_shelters = results[4] if results[4] is not None else []

        if not current_weather:
            print(f"⚠️ Weather API Timeout for {name}. Using fallback.")
            current_weather = {
                'temperature': 25.0, 'humidity': 50.0, 'pressure': 1013.0,
                'wind_speed': 10.0, 'weather_condition': 'Cloudy',
                'location': {'lat': lat, 'lon': lon}
            }
        
        # Calculate weather changes
        weather_changes = weather_collector.calculate_weather_changes(historical_weather)
        
        if not satellite_data:
            # Fallback to synthetic data if real data unavailable
            print("⚠️ Real satellite data unavailable, using synthetic data...")
            satellite_data = satellite_collector.generate_synthetic_satellite_image()
        else:
            print("✅ Successfully fused REAL Sentinel-2 & NASA MODIS data!")
        
        # 5. Run AI prediction
        try:
            predictions = predictor.predict_all_disasters(
                satellite_data=satellite_data,
                current_weather=current_weather,
                historical_weather=historical_weather,
                weather_changes=weather_changes
            )
        except Exception as e:
            print(f"❌ PREDICTION ENGINE CRASH: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"AI Prediction Engine Error: {str(e)}")
        
        # ⭐ INTEGRATE REAL NASA HOTSPOTS
        predictions['fire_hotspots_count'] = len(fire_hotspots)
        if fire_hotspots:
            # Overwrite with real space-borne detection
            predictions['fire']['confidence'] = 0.95
            predictions['fire']['risk_level'] = "HIGH"
            predictions['fire']['reasons'].insert(0, f"NASA VIIRS: {len(fire_hotspots)} REAL fire hotspots detected within 50km.")
            predictions['primary_threat'] = "fire"
            predictions['overall_risk_level'] = "HIGH"
        
        # Add location info
        predictions['location_name'] = name
        # Safely extract current weather telemetry
        temp = current_weather.get('temperature', 25)
        humid = current_weather.get('humidity', 50)
        press = current_weather.get('pressure', 1013)
        wind = current_weather.get('wind_speed', 10)
        cond = current_weather.get('weather_condition', 'Unknown')
        
        predictions['current_weather'] = {
            'temperature': temp,
            'humidity': humid,
            'pressure': press,
            'wind_speed': wind,
            'weather_condition': cond,
        }
        
        # 4. Determine Rescue Strategy (Alerts & Shelters)
        triggered_alerts = alert_manager.process_prediction(predictions)
        
        # 🏥 INTEGRATE PARALLEL SHELTER RESULTS
        if real_shelters:
            predictions['shelters'] = real_shelters
            predictions['shelters_source'] = 'OpenStreetMap (REAL)'
        else:
            predictions['shelters'] = alert_manager.get_nearest_shelters(name)
            predictions['shelters_source'] = 'Fallback (Demo)'
        
        predictions['active_alerts'] = triggered_alerts

        # ═══════════════════════════════════════════════════════════
        # 📧 ZONE-BASED EMAIL ALERT DISPATCH
        # Check if this prediction's location falls inside any custom
        # zone, and if the risk meets the zone's threshold → send email
        # to all recipient_emails registered for that zone.
        # ═══════════════════════════════════════════════════════════
        try:
            from db.database import Zone as ZoneModel
            from services.advanced_alert_system import advanced_alert_system
            
            RISK_ORDER = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRITICAL': 3}
            prediction_risk = predictions.get('overall_risk_level', 'LOW')
            
            active_zones = db.query(ZoneModel).filter(ZoneModel.is_active == 1).all()
            for zone in active_zones:
                # Skip zones with no email recipients
                if not zone.recipient_emails:
                    continue
                
                # Check if prediction point is inside this zone polygon
                if not advanced_alert_system._is_point_in_polygon(lat, lon, zone.coordinates):
                    continue
                
                # Check if prediction risk meets zone's severity threshold
                zone_threshold = zone.severity_threshold or 'MEDIUM'
                if RISK_ORDER.get(prediction_risk, 0) < RISK_ORDER.get(zone_threshold, 1):
                    print(f"📭 Zone '{zone.name}': risk {prediction_risk} below threshold {zone_threshold}, skipping email.")
                    continue
                
                # ✅ Risk meets threshold AND location is inside zone → send alert
                print(f"🚨 Zone '{zone.name}' MATCHED! Dispatching alert to: {zone.recipient_emails}")
                
                # Enrich prediction with location coords for the alert system
                zone_prediction = dict(predictions)
                zone_prediction['latitude'] = lat
                zone_prediction['longitude'] = lon
                zone_prediction['location_name'] = f"{name} (Zone: {zone.name})"
                
                alert_obj = advanced_alert_system.create_alert(
                    prediction=zone_prediction,
                    recipients=zone.recipient_emails
                )
                # Send notifications in background so the API response isn't delayed
                background_tasks.add_task(advanced_alert_system._send_notifications, alert_obj)
                
                triggered_alerts.append({
                    "type": "ZONE_EMAIL",
                    "zone": zone.name,
                    "recipients": zone.recipient_emails,
                    "severity": prediction_risk,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as zone_alert_err:
            print(f"⚠️ Zone alert dispatch error (non-critical): {zone_alert_err}")

        # ⭐ SAVE TO DATABASE (PERSISTENCE)
        try:
            record = PredictionRecord(
                location_name=name,
                latitude=lat,  # Use resolved coordinates
                longitude=lon, # Use resolved coordinates
                overall_risk=predictions["overall_risk_level"],
                primary_threat=predictions["primary_threat"],
                weather_data=predictions['current_weather'],
                risk_scores={
                    "fire": predictions["fire"]["confidence"],
                    "flood": predictions["flood"]["confidence"],
                    "cyclone": predictions["cyclone"]["confidence"]
                }
            )
            db.add(record)
            db.commit()
        except Exception as db_err:
            print(f"⚠️ DB Error (Prediction not saved): {db_err}")
            
        # ⚡ CACHE UPDATE
        cache_key = f"{round(lat, 3)}_{round(lon, 3)}"
        PREDICTION_CACHE[cache_key] = {
            'timestamp': datetime.now(),
            'data': predictions
        }
            
        return predictions
        
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        import traceback
        print(f"❌ CRITICAL PREDICTION ERROR: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/api/analytics/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """Fetch real historical summary for the analytics dashboard"""
    # Last 30 days
    total_predictions = db.query(PredictionRecord).count()
    high_risks = db.query(PredictionRecord).filter(PredictionRecord.overall_risk == "HIGH").count()
    
    # Get recent records for table
    recent_records = db.query(PredictionRecord).order_by(PredictionRecord.timestamp.desc()).limit(10).all()
    
    return {
        "status": "success",
        "total_count": total_predictions,
        "high_risk_count": high_risks,
        "recent_activity": [
            {
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M"),
                "location": r.location_name,
                "event": f"{r.primary_threat.capitalize()} Analysis",
                "risk": r.overall_risk,
                "confidence": f"{int(r.risk_scores.get(r.primary_threat, 0) * 100)}%"
            } for r in recent_records
        ]
    }

@app.get("/api/predictions/history")
async def get_all_predictions(limit: int = 50, db: Session = Depends(get_db)):
    """Fetch recent historical prediction records for map view/list"""
    records = db.query(PredictionRecord).order_by(PredictionRecord.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "name": r.location_name,
            "lat": r.latitude,
            "lon": r.longitude,
            "overall_risk": r.overall_risk,
            "primary_threat": r.primary_threat,
            "risk_scores": r.risk_scores,
            "weather": r.weather_data
        } for r in records
    ]

@app.get("/api/weather/{lat}/{lon}")
async def get_weather(lat: float, lon: float):
    """Get current weather for a location"""
    weather = weather_collector.get_current_weather(lat, lon)
    if not weather:
        raise HTTPException(status_code=503, detail="Failed to fetch weather data")
    return weather

@app.get("/api/fires/{lat}/{lon}")
async def get_fire_hotspots(lat: float, lon: float, radius: int = 50):
    """Get active fire hotspots from NASA FIRMS"""
    fires = satellite_collector.get_nasa_firms_data(lat, lon, radius_km=radius)
    return {
        "hotspots": fires,
        "count": len(fires),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/forecast/{lat}/{lon}")
async def get_forecast(lat: float, lon: float, days: int = 5):
    """Get weather forecast"""
    forecast = weather_collector.get_forecast_data(lat, lon, days=days)
    return {
        "forecast": forecast,
        "count": len(forecast),
        "days": days
    }

@app.post("/api/monitor/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start background monitoring (for production deployment)"""
    # This would start the real-time monitor in background
    return {
        "message": "Monitoring started",
        "status": "running",
        "interval": "30 minutes"
    }

@app.get("/api/search/{query}")
async def search_location(query: str):
    """Search for a location by name"""
    coords = geocode_city(query)
    if coords:
        return {
            "name": query.title(),
            "lat": coords['lat'],
            "lon": coords['lon'],
            "found": True
        }
    return {"found": False, "message": "Location not found in registry"}


@app.get("/api/autocomplete/{query}")
async def autocomplete_location(query: str, limit: int = 5):
    """
    Search for locations with autocomplete suggestions
    Uses OpenStreetMap Nominatim API for worldwide coverage
    """
    import requests
    
    if len(query) < 2:
        return {"suggestions": []}
    
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                'q': query,
                'format': 'json',
                'limit': limit,
                'addressdetails': 1
            },
            headers={
                'User-Agent': 'SDARS-DisasterAlertSystem/1.0 (College Project)'
            },
            timeout=5
        )
        
        if response.status_code == 200:
            results = response.json()
            suggestions = []
            
            for result in results:
                address = result.get('address', {})
                
                # Get a clean location name
                name = (
                    address.get('city') or 
                    address.get('town') or 
                    address.get('village') or 
                    address.get('municipality') or
                    address.get('county') or
                    result.get('name', query)
                )
                
                country = address.get('country', '')
                state = address.get('state', '')
                
                # ⭐ PRE-FLIGHT THREAT SCANNING
                risk_info = _get_lite_risk(float(result['lat']), float(result['lon']))
                
                suggestions.append({
                    "name": name,
                    "display_name": result.get('display_name', ''),
                    "lat": float(result['lat']),
                    "lon": float(result['lon']),
                    "country": country,
                    "state": state,
                    "type": result.get('type', 'place'),
                    "risk_level": risk_info['level'],
                    "primary_threat": risk_info['threat']
                })
            
            return {"suggestions": suggestions, "count": len(suggestions)}
        
        return {"suggestions": [], "error": "Nominatim API error"}
        
    except Exception as e:
        print(f"⚠️ Autocomplete error: {e}")
        return {"suggestions": [], "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# 🗺️ NAVIGATION & ROUTING ENDPOINTS
# ═══════════════════════════════════════════════════════════════

from pydantic import BaseModel
from typing import Optional, List, Dict

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    alternatives: Optional[int] = 3


class EvacuationRequest(BaseModel):
    current_lat: float
    current_lon: float
    disaster_type: str
    disaster_lat: float
    disaster_lon: float


@app.post("/api/routes/find")
async def find_routes(request: RouteRequest):
    """
    Find multiple route alternatives between two points
    Returns routes with basic information (no safety analysis)
    """
    try:
        routes = await route_optimizer.find_multiple_routes(
            request.start_lat,
            request.start_lon,
            request.end_lat,
            request.end_lon,
            alternatives=request.alternatives
        )
        
        return {
            "status": "success",
            "routes": routes,
            "count": len(routes),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route finding error: {str(e)}")


@app.post("/api/routes/analyze")
async def analyze_route_safety(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    route_points: List[Dict]
):
    """
    Analyze a specific route for safety
    Probes multiple waypoints along the route for disaster risks
    
    route_points: List of {lat, lon} coordinates along the route
    """
    try:
        # Probe waypoints for disaster risks
        predictions = []
        
        # Sample up to 10 points along the route for analysis
        sample_size = min(10, len(route_points))
        step = max(1, len(route_points) // sample_size)
        
        for i in range(0, len(route_points), step):
            point = route_points[i]
            
            try:
                # Get weather data
                current_weather = weather_collector.get_current_weather(
                    point['lat'], point['lon']
                )
                historical_weather = weather_collector.get_historical_weather(
                    point['lat'], point['lon'], days_back=3
                )
                weather_changes = weather_collector.calculate_weather_changes(historical_weather)
                
                # Get satellite data
                fire_hotspots = satellite_collector.get_nasa_firms_data(
                    point['lat'], point['lon'], radius_km=10
                )
                satellite_data = satellite_collector.generate_synthetic_satellite_image()
                
                # Run prediction
                prediction = predictor.predict_all_disasters(
                    satellite_data=satellite_data,
                    current_weather=current_weather,
                    historical_weather=historical_weather,
                    weather_changes=weather_changes
                )
                
                prediction['location'] = point
                predictions.append(prediction)
                
            except Exception as point_error:
                print(f"Error analyzing waypoint {i}: {point_error}")
                continue
        
        # Calculate overall route safety score
        safety_analysis = route_optimizer.calculate_route_safety_score(predictions)
        
        return {
            "status": "success",
            "safety_score": safety_analysis['overall_score'],
            "risk_level": safety_analysis['risk_level'],
            "hazard_segments": safety_analysis['hazard_segments'],
            "recommendations": safety_analysis['recommendations'],
            "safest_time": safety_analysis['safest_time'],
            "analysis_details": safety_analysis['analysis'],
            "waypoints_analyzed": len(predictions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route analysis error: {str(e)}")


@app.get("/api/shelters/nearby")
async def get_nearby_shelters(lat: float, lon: float, radius_km: int = 10, limit: int = 10):
    """
    Get nearby emergency shelters and facilities
    Uses OpenStreetMap data for real locations
    """
    try:
        facilities = real_shelter_finder.find_emergency_facilities(lat, lon, radius_km)
        
        # Get nearest shelters sorted by distance
        nearest_shelters = real_shelter_finder.get_nearest_shelters(lat, lon, limit=limit)
        
        return {
            "status": "success",
            "facilities": facilities,
            "nearest_shelters": nearest_shelters,
            "total_facilities": facilities['total_count'],
            "query_location": {"lat": lat, "lon": lon},
            "radius_km": radius_km,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shelter lookup error: {str(e)}")


@app.post("/api/evacuation/plan")
async def plan_evacuation_route(request: EvacuationRequest):
    """
    Plan optimal evacuation route away from disaster
    
    Finds safest shelters in direction away from disaster epicenter
    """
    try:
        # Get nearby shelters
        shelters = real_shelter_finder.get_nearest_shelters(
            request.current_lat,
            request.current_lon,
            limit=20
        )
        
        # Calculate evacuation route
        # (This logic would be more complex in real scenario)
        evacuation_plan = route_optimizer.calculate_evacuation_route(
            request.current_lat,
            request.current_lon,
            request.disaster_type,
            request.disaster_lat,
            request.disaster_lon,
            shelters
        )
        
        return {
            "status": "success",
            "evacuation_plan": evacuation_plan,
            "disaster_type": request.disaster_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evacuation planning error: {str(e)}")


@app.get("/api/route/hazards")
async def get_route_hazards(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float
):
    """
    Get all known hazards between two points
    Returns fire hotspots, weather warnings, and risk zones
    """
    try:
        # Calculate bounding box for the route
        min_lat = min(start_lat, end_lat)
        max_lat = max(start_lat, end_lat)
        min_lon = min(start_lon, end_lon)
        max_lon = max(start_lon, end_lon)
        
        # Get center point
        center_lat = (start_lat + end_lat) / 2
        center_lon = (start_lon + end_lon) / 2
        
        # Calculate dynamic radius to cover entire route (with 20% margin)
        import math
        dist_km = math.sqrt((start_lat - end_lat)**2 + (start_lon - end_lon)**2) * 111
        dynamic_radius = max(50, (dist_km / 2) * 1.2)
        
        # Limit radius to 400km to avoid API timeouts
        search_radius = min(400, dynamic_radius)
        
        # Get fire hotspots in the area covering the whole route
        fire_hotspots = satellite_collector.get_nasa_firms_data(
            center_lat, center_lon, radius_km=int(search_radius)
        )
        
        # Get weather for start and end points
        start_weather = weather_collector.get_current_weather(start_lat, start_lon)
        end_weather = weather_collector.get_current_weather(end_lat, end_lon)
        
        return {
            "status": "success",
            "bounding_box": {
                "min_lat": min_lat,
                "max_lat": max_lat,
                "min_lon": min_lon,
                "max_lon": max_lon
            },
            "fire_hotspots": fire_hotspots,
            "fire_count": len(fire_hotspots),
            "start_weather": start_weather,
            "end_weather": end_weather,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hazard lookup error: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# 🚨 ALERT SYSTEM ENDPOINTS
# ═══════════════════════════════════════════════════════════════

from services.advanced_alert_system import advanced_alert_system, AlertSeverity


class AlertRequest(BaseModel):
    prediction_data: Dict
    severity_override: Optional[str] = None


class AcknowledgeAlertRequest(BaseModel):
    alert_id: str
    user_id: Optional[str] = "system"
    email: Optional[str] = None


@app.post("/api/alerts/create")
async def create_alert(request: AlertRequest):
    """
    Create a new alert from prediction data
    
    Automatically determines severity and notification channels
    """
    try:
        severity = None
        if request.severity_override:
            severity = AlertSeverity[request.severity_override.upper()]
        
        alert = advanced_alert_system.create_alert(
            prediction=request.prediction_data,
            severity_override=severity
        )
        
        return {
            "status": "success",
            "alert": alert.to_dict(),
            "message": "Alert created and notifications sent"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert creation error: {str(e)}")


@app.get("/api/alerts/active")
async def get_active_alerts(severity: Optional[str] = None):
    """
    Get all active (unacknowledged) alerts
    
    Optional severity filter: LOW, MEDIUM, HIGH, CRITICAL
    """
    try:
        severity_filter = None
        if severity:
            severity_filter = AlertSeverity[severity.upper()]
        
        alerts = advanced_alert_system.get_active_alerts(severity_filter)
        
        return {
            "status": "success",
            "count": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")


@app.get("/api/alerts/history")
async def get_alert_history(limit: int = 50):
    """
    Get alert history
    
    Returns acknowledged and unacknowledged alerts, sorted by time
    """
    try:
        history = advanced_alert_system.get_alert_history(limit=limit)
        
        return {
            "status": "success",
            "count": len(history),
            "alerts": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@app.post("/api/alerts/acknowledge")
async def acknowledge_alert(request: AcknowledgeAlertRequest, background_tasks: BackgroundTasks):
    """
    Acknowledge an alert
    
    Moves alert from active to history and sends notifications in background
    """
    try:
        success, alert = advanced_alert_system.acknowledge_alert(
            alert_id=request.alert_id,
            user_id=request.user_id,
            email=request.email
        )
        
        if success and alert:
            # Send notifications in the background so the user doesn't wait for SMTP
            background_tasks.add_task(advanced_alert_system._send_notifications, alert)
            
            return {
                "status": "success",
                "message": f"Alert {request.alert_id} acknowledged. Notifications queued."
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error acknowledging alert: {str(e)}")


@app.post("/api/alerts/test")
async def test_alert_system(background_tasks: BackgroundTasks):
    """
    Test the alert system with a mock disaster prediction
    Useful for testing notification channels
    """
    try:
        # Mock high-risk fire prediction
        test_prediction = {
            'location_name': 'Tactical Test Sector',
            'latitude': 19.0760,
            'longitude': 72.8777,
            'overall_risk_level': 'HIGH',
            'primary_threat': 'fire',
            'fire': {
                'confidence': 0.85,
                'risk_level': 'HIGH',
                'reasons': [
                    'TEST: High temperature detected',
                    'TEST: Low humidity conditions',
                    'TEST: Strong winds present'
                ]
            },
            'shelters': [
                {'name': 'Test Emergency Center', 'distance_km': 2.5}
            ]
        }
        
        # This will now include matched_zones logic automatically
        alert = advanced_alert_system.create_alert(test_prediction)
        
        # ⭐ Trigger actual notification broadcast
        background_tasks.add_task(advanced_alert_system._send_notifications, alert)
        
        return {
            "status": "success",
            "message": "Test alert created and broadcast initiated",
            "alert_id": alert.alert_id,
            "note": "Notifications are being dispatched in the background"
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Test alert error: {str(e)}")


@app.get("/api/statistics")
async def get_statistics():
    """Get system statistics"""
    active_alerts = advanced_alert_system.get_active_alerts()
    
    return {
        "total_predictions": 0,  # Would query database
        "active_alerts": len(active_alerts),
        "monitored_locations": len(config.MONITORED_LOCATIONS),
        "uptime": "N/A",
        "last_update": datetime.now().isoformat()
    }


# ═══════════════════════════════════════════════════════════════
# 🛰️ SATELLITE VISUALIZATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

from services.satellite_visualization import satellite_viz


# ═══════════════════════════════════════════════════════════════
# 🗺️ CUSTOM ALERT ZONES
# ═══════════════════════════════════════════════════════════════

class ZoneRequest(BaseModel):
    name: str
    coordinates: List[List[float]]
    severity_threshold: str
    notification_channels: List[str]
    recipient_emails: Optional[List[str]] = []
    user_id: Optional[str] = "default_user"

@app.post("/api/zones/create")
async def create_zone(request: ZoneRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new persistent alert zone"""
    try:
        from db.database import Zone
        new_zone = Zone(
            name=request.name,
            coordinates=request.coordinates,
            severity_threshold=request.severity_threshold,
            notification_channels=request.notification_channels,
            recipient_emails=request.recipient_emails,
            user_id=request.user_id
        )
        db.add(new_zone)
        db.commit()
        db.refresh(new_zone)

        # ⭐ TRIGGER ACTIVE NOTIFICATION VERIFICATION
        verification_recipients = list(request.recipient_emails) or []
        # If user_email (user_id) is provided and not in list, add it
        if request.user_id and "@" in request.user_id:
            if request.user_id not in verification_recipients:
                verification_recipients.append(request.user_id)
        
        v_results = {"status": "skipped", "success_count": 0, "failure_count": 0}
        if verification_recipients:
            # We await this synchronously to ensure the user knows if the provides emails are valid/sent
            v_report = await advanced_alert_system.send_zone_verification(
                request.name, 
                verification_recipients
            )
            v_results = {
                "status": v_report.get("status"),
                "success_count": len(v_report.get("report", {}).get("successes", [])),
                "failure_count": len(v_report.get("report", {}).get("failures", [])),
                "message": v_report.get("message", "Verification dispatched")
            }

        return {
            "status": "success", 
            "zone_id": new_zone.id, 
            "verification": v_results
        }
    except Exception as e:
        print(f"Zone Error: {e}")
        raise HTTPException(status_code=500, detail=f"Zone creation error: {str(e)}")

@app.get("/api/zones")
async def get_zones(db: Session = Depends(get_db)):
    """Fetch all active monitoring zones"""
    from db.database import Zone
    zones = db.query(Zone).filter(Zone.is_active == 1).all()
    return {
        "status": "success",
        "zones": [{
            "zone_id": z.id,
            "name": z.name,
            "coordinates": z.coordinates,
            "severity_threshold": z.severity_threshold,
            "notification_channels": z.notification_channels,
            "recipient_emails": z.recipient_emails or [],
            "created_at": z.created_at.isoformat()
        } for z in zones]
    }

@app.delete("/api/zones/{zone_id}")
async def delete_zone_api(zone_id: int, db: Session = Depends(get_db)):
    """Deactivate a zone"""
    from db.database import Zone
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    zone.is_active = 0
    db.commit()
    return {"status": "success", "message": "Zone deactivated"}

class SatelliteRequest(BaseModel):
    lat: float
    lon: float
    date: Optional[str] = None
    layer_type: Optional[str] = 'TRUE_COLOR'
    bbox_size: Optional[float] = 0.1


class NDVIRequest(BaseModel):
    lat: float
    lon: float
    date: Optional[str] = None


class ThermalRequest(BaseModel):
    lat: float
    lon: float
    radius_km: Optional[int] = 50


class TimeSeriesRequest(BaseModel):
    lat: float
    lon: float
    start_date: str
    end_date: str
    metric: Optional[str] = 'NDVI'


class CompareRequest(BaseModel):
    lat: float
    lon: float
    date1: str
    date2: str
    layer_type: Optional[str] = 'TRUE_COLOR'


@app.post("/api/satellite/imagery")
async def get_satellite_imagery(request: SatelliteRequest):
    """
    Get Sentinel-2 satellite imagery for a location
    
    Layer types: TRUE_COLOR, FALSE_COLOR, NDVI, TEMPERATURE, etc.
    """
    try:
        imagery = satellite_viz.get_sentinel_imagery(
            lat=request.lat,
            lon=request.lon,
            date=request.date,
            layer_type=request.layer_type,
            bbox_size=request.bbox_size
        )
        
        return {
            "status": "success",
            "data": imagery
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Imagery error: {str(e)}")


@app.post("/api/satellite/ndvi")
async def calculate_ndvi(request: NDVIRequest):
    """
    Calculate NDVI (Normalized Difference Vegetation Index)
    
    Returns vegetation health analysis and color coding
    """
    try:
        ndvi_data = satellite_viz.calculate_ndvi(
            lat=request.lat,
            lon=request.lon,
            date=request.date
        )
        
        return {
            "status": "success",
            "data": ndvi_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NDVI error: {str(e)}")


@app.post("/api/satellite/thermal")
async def get_thermal_data(request: ThermalRequest):
    """
    Get thermal hotspot data (fire detection)
    
    Uses NASA FIRMS/VIIRS data
    """
    try:
        thermal = satellite_viz.get_thermal_data(
            lat=request.lat,
            lon=request.lon,
            radius_km=request.radius_km
        )
        
        return {
            "status": "success",
            "data": thermal
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Thermal data error: {str(e)}")


@app.post("/api/satellite/timeseries")
async def get_time_series(request: TimeSeriesRequest):
    """
    Get time-series satellite data
    
    Metrics: NDVI, TEMPERATURE, MOISTURE
    """
    try:
        timeseries = satellite_viz.get_time_series(
            lat=request.lat,
            lon=request.lon,
            start_date=request.start_date,
            end_date=request.end_date,
            metric=request.metric
        )
        
        return {
            "status": "success",
            "data": timeseries
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Time-series error: {str(e)}")


@app.post("/api/satellite/compare")
async def compare_imagery(request: CompareRequest):
    """
    Compare satellite imagery between two dates
    
    Useful for before/after disaster analysis
    """
    try:
        comparison = satellite_viz.compare_imagery(
            lat=request.lat,
            lon=request.lon,
            date1=request.date1,
            date2=request.date2,
            layer_type=request.layer_type
        )
        
        return {
            "status": "success",
            "data": comparison
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")


@app.get("/api/satellite/layers")
async def get_layer_options():
    """
    Get available satellite layer types
    
    Returns list of supported visualization layers
    """
    try:
        layers = satellite_viz.get_layer_options()
        
        return {
            "status": "success",
            "layers": layers,
            "count": len(layers)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Layers error: {str(e)}")


# Run server
if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   🛰️  SDARS API SERVER                                   ║
    ║   AI-Based Disaster Prediction System                   ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    
    Server starting on http://{config.API_HOST}:{config.API_PORT}
    API Documentation: http://{config.API_HOST}:{config.API_PORT}/docs
    
    Endpoints:
    • POST /api/predict - Run disaster prediction
    • GET  /api/weather/{{lat}}/{{lon}} - Get weather data
    • GET  /api/fires/{{lat}}/{{lon}} - Get fire hotspots
    • GET  /api/locations - Get monitored locations
    
    Press Ctrl+C to stop
    """)
    
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level="info"
    )

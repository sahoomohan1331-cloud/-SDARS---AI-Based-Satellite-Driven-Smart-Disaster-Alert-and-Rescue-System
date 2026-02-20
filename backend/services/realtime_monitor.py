"""
Real-Time Monitoring Service
Continuously monitors locations and triggers predictions
Combines satellite + weather data collection and analysis
"""
import time
import schedule
from datetime import datetime
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collectors.weather_collector import WeatherDataCollector
from data_collectors.satellite_collector import SatelliteDataCollector
from ai_models.multi_modal_predictor import MultiModalPredictor
import config

class RealTimeMonitor:
    """
    Real-time monitoring system that:
    1. Collects satellite imagery
    2. Collects weather data
    3. Analyzes both with AI
    4. Generates alerts
    """
    
    def __init__(self, locations: List[Dict] = None):
        self.locations = locations or config.MONITORED_LOCATIONS
        self.weather_collector = WeatherDataCollector()
        self.satellite_collector = SatelliteDataCollector()
        self.predictor = MultiModalPredictor()
        
        # Storage for historical data
        self.weather_history = {}
        
        print(f"🛰️  SDARS Real-Time Monitor initialized")
        print(f"📍 Monitoring {len(self.locations)} locations")
        
    def collect_data_for_location(self, location: Dict) -> Dict:
        """Collect all data for a single location"""
        lat, lon = location['lat'], location['lon']
        name = location['name']
        
        print(f"\n📡 Collecting data for {name} ({lat}, {lon})...")
        
        # 1. Collect current weather
        current_weather = self.weather_collector.get_current_weather(lat, lon)
        if not current_weather:
            print(f"  ❌ Failed to collect weather data for {name}")
            return None
        
        print(f"  ✓ Weather: {current_weather['temperature']}°C, "
              f"{current_weather['humidity']}% humidity, "
              f"{current_weather['pressure']} hPa")
        
        # 2. Get historical weather
        historical_weather = self.weather_collector.get_historical_weather(lat, lon, days_back=3)
        
        # Store in history
        if name not in self.weather_history:
            self.weather_history[name] = historical_weather
        else:
            # Append new data (in production, this would be more sophisticated)
            self.weather_history[name] = historical_weather
        
        # 3. Calculate weather changes
        weather_changes = self.weather_collector.calculate_weather_changes(
            self.weather_history[name]
        )
        
        print(f"  ✓ Weather changes: "
              f"temp Δ6h={weather_changes.get('temp_change_6h', 0):.1f}°C, "
              f"pressure Δ6h={weather_changes.get('pressure_change_6h', 0):.1f} hPa")
        
        # 4. Collect satellite data
        # Check for active fires from NASA FIRMS (VIIRS real-time)
        fire_data = self.satellite_collector.get_nasa_firms_data(lat, lon, radius_km=50)
        print(f"  ✓ NASA FIRMS: {len(fire_data)} active fire points detected")

        # 🛰️ REAL DATA: Fetch NASA MODIS thermal + EONET natural events
        real_sat_data = self.satellite_collector.get_real_satellite_data(lat, lon)
        print(f"  ✓ NASA Satellite: quality={real_sat_data.get('data_quality', 'UNKNOWN')}, "
              f"source={real_sat_data.get('source', 'N/A')}")

        # Bridge real NASA data into the format the AI predictor expects.
        # The predictor reads: analysis.thermal.{hotspot_percentage, mean_temperature, max_temperature}
        #                      indices.ndvi  (list/array)
        #                      indices.ndwi  (list/array)
        #                      data_quality  (string)
        satellite_image = self._bridge_nasa_to_predictor_format(
            real_sat_data, fire_data, lat, lon
        )
        print(f"  ✓ Satellite data bridged for AI predictor")

        return {
            'location': location,
            'current_weather': current_weather,
            'historical_weather': historical_weather,
            'weather_changes': weather_changes,
            'satellite_data': satellite_image,
            'fire_hotspots': fire_data,
        }
    
    def _bridge_nasa_to_predictor_format(self, nasa_data: dict, fire_data: list,
                                          lat: float, lon: float) -> dict:
        """
        Translates NASA MODIS/EONET data into the format expected by MultiModalPredictor.

        NASA gives us:
          - analysis.thermal.{mean_temperature, max_temperature, hotspot_percentage, fire_risk}
          - natural_events (list of EONET events)
          - data_quality (REAL_SATELLITE_DATA / ZERO_SIGNAL / etc.)

        Predictor expects:
          - analysis.thermal.{mean_temperature, max_temperature, std_temperature,
                              hotspot_count, hotspot_percentage}
          - indices.ndvi  (flat list of floats, -1..1)
          - indices.ndwi  (flat list of floats, -1..1)
          - data_quality  (string)
        """
        import numpy as np

        data_quality = nasa_data.get('data_quality', 'ZERO_SIGNAL')

        # ── Thermal block ────────────────────────────────────────────────────
        nasa_thermal = nasa_data.get('analysis', {}).get('thermal', {})
        mean_temp  = nasa_thermal.get('mean_temperature', 25.0)
        max_temp   = nasa_thermal.get('max_temperature', 30.0)
        hotspot_pct = nasa_thermal.get('hotspot_percentage', 0.0)

        # Incorporate real FIRMS fire count into hotspot percentage
        # Each confirmed FIRMS fire point adds ~0.5% to hotspot density
        firms_boost = min(len(fire_data) * 0.5, 20.0)
        hotspot_pct = min(hotspot_pct + firms_boost, 100.0)
        hotspot_count = len(fire_data)

        thermal = {
            'mean_temperature': mean_temp,
            'max_temperature':  max_temp,
            'std_temperature':  abs(max_temp - mean_temp) / 3.0,  # Estimated std
            'hotspot_count':    hotspot_count,
            'hotspot_percentage': round(hotspot_pct, 2),
            'fire_risk': nasa_thermal.get('fire_risk', 'LOW'),
        }

        # ── NDVI proxy ───────────────────────────────────────────────────────
        # NASA MODIS doesn't give raw NDVI arrays, so we derive a proxy from
        # the thermal fire_risk and any EONET vegetation events.
        fire_risk_str = nasa_thermal.get('fire_risk', 'LOW')
        # Low NDVI (dry/damaged vegetation) correlates with high fire risk
        ndvi_center = {'LOW': 0.55, 'MODERATE': 0.35, 'HIGH': 0.18}.get(fire_risk_str, 0.5)
        rng = np.random.default_rng(seed=int(abs(lat * 100) + abs(lon * 100)))
        ndvi_array = np.clip(rng.normal(ndvi_center, 0.08, 256), -1.0, 1.0).tolist()

        # ── NDWI proxy ───────────────────────────────────────────────────────
        # Check EONET events for flood/water events to raise NDWI
        natural_events = nasa_data.get('natural_events', [])
        water_event = any(
            'flood' in e.get('category', '').lower() or
            'water' in e.get('title', '').lower()
            for e in natural_events
        )
        ndwi_center = 0.45 if water_event else 0.05
        ndwi_array = np.clip(rng.normal(ndwi_center, 0.10, 256), -1.0, 1.0).tolist()

        # ── Assemble result ──────────────────────────────────────────────────
        bridged = {
            'source': nasa_data.get('source', 'NASA'),
            'data_quality': data_quality,
            'location': {'lat': lat, 'lon': lon},
            'timestamp': nasa_data.get('timestamp', ''),
            'analysis': {
                'thermal': thermal,
                'vegetation_health': 'Poor' if ndvi_center < 0.3 else
                                     'Fair' if ndvi_center < 0.5 else 'Good',
                'water_bodies_detected': water_event,
            },
            'indices': {
                'ndvi': ndvi_array,
                'ndwi': ndwi_array,
            },
            # Pass through EONET events for downstream use
            'natural_events': natural_events,
            'active_disasters': nasa_data.get('active_disasters', 0),
        }

        return bridged

    def analyze_location(self, data: Dict) -> Dict:
        """Run AI analysis on collected data"""
        if not data:
            return None
        
        location_name = data['location']['name']
        print(f"\n🤖 Running AI analysis for {location_name}...")
        
        # Run multi-modal prediction
        predictions = self.predictor.predict_all_disasters(
            satellite_data=data['satellite_data'],
            current_weather=data['current_weather'],
            historical_weather=data['historical_weather'],
            weather_changes=data['weather_changes']
        )
        
        # Add fire hotspot data
        predictions['fire_hotspots_count'] = len(data['fire_hotspots'])
        if data['fire_hotspots']:
            predictions['fire']['confidence'] = max(
                predictions['fire']['confidence'], 
                0.8  # High confidence if NASA detects fires
            )
            predictions['fire']['reasons'].append(
                f"NASA FIRMS: {len(data['fire_hotspots'])} active fires detected"
            )
        
        return predictions
    
    def generate_alert(self, location_name: str, predictions: Dict):
        """Generate alert if risk is significant"""
        primary_threat = predictions['primary_threat']
        risk_level = predictions['overall_risk_level']
        
        if risk_level in ['HIGH', 'MEDIUM']:
            print(f"\n🚨 ALERT for {location_name}!")
            print(f"   Primary Threat: {primary_threat.upper()}")
            print(f"   Risk Level: {risk_level}")
            print(f"   Confidence: {predictions[primary_threat]['confidence']:.1%}")
            print(f"   Reasons:")
            for reason in predictions[primary_threat]['reasons']:
                print(f"     • {reason}")
            
            # In production, send email/SMS/API alerts here
            # self.send_email_alert(location_name, predictions)
            # self.send_sms_alert(location_name, predictions)
            
            return True
        else:
            print(f"  ✓ No significant threats detected for {location_name}")
            return False
    
    def monitor_all_locations(self):
        """Monitor all configured locations AND custom database zones"""
        print(f"\n{'='*60}")
        print(f"🌍 SDARS Monitoring Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # 1. Start with static locations from config
        all_locations = self.locations.copy()
        
        # 2. Add custom zones from database
        try:
            from db.database import SessionLocal, Zone
            db = SessionLocal()
            active_zones = db.query(Zone).filter(Zone.is_active == 1).all()
            for zone in active_zones:
                # Calculate center for basic weather/satellite probes
                lats = [c[0] for c in zone.coordinates]
                lons = [c[1] for c in zone.coordinates]
                center_lat = sum(lats) / len(lats)
                center_lon = sum(lons) / len(lons)
                
                all_locations.append({
                    "name": f"ZONE: {zone.name}",
                    "lat": center_lat,
                    "lon": center_lon,
                    "is_custom_zone": True,
                    "zone_id": zone.id,
                    "severity_threshold": zone.severity_threshold
                })
            db.close()
        except Exception as db_err:
            print(f"⚠️ Could not load custom zones: {db_err}")

        alerts_generated = 0
        
        for location in all_locations:
            try:
                # Collect data
                data = self.collect_data_for_location(location)
                
                if data:
                    # Analyze with AI
                    predictions = self.analyze_location(data)
                    
                    if predictions:
                        # Add zone metadata if applicable
                        if "is_custom_zone" in location:
                            predictions["is_custom_zone"] = True
                            predictions["zone_id"] = location["zone_id"]
                        
                        # Generate alerts if needed
                        if self.generate_alert(location['name'], predictions):
                            alerts_generated += 1
                        
                        # Save predictions
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"prediction_{location['name'].replace(' ', '_')}_{timestamp}.json"
                        self.predictor.save_prediction(predictions, filename)
                
                # Small delay between locations
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error monitoring {location['name']}: {e}")
        
        print(f"\n📊 Monitoring cycle complete")
        print(f"   Locations checked: {len(all_locations)}")
        print(f"   Alerts generated: {alerts_generated}")
        print(f"{'='*60}\n")
    
    def start_continuous_monitoring(self, interval_minutes: int = 30):
        """
        Start continuous monitoring
        Runs every interval_minutes
        """
        print(f"\n🚀 Starting continuous monitoring...")
        print(f"   Check interval: every {interval_minutes} minutes")
        print(f"   Press Ctrl+C to stop\n")
        
        # Schedule monitoring
        schedule.every(interval_minutes).minutes.do(self.monitor_all_locations)
        
        # Run immediately
        self.monitor_all_locations()
        
        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")

# Main execution
if __name__ == "__main__":
    # Create monitor
    monitor = RealTimeMonitor()
    
    # For demo, just run one cycle
    print("=== RUNNING SINGLE MONITORING CYCLE (DEMO) ===")
    monitor.monitor_all_locations()
    
    # Uncomment to run continuous monitoring:
    # monitor.start_continuous_monitoring(interval_minutes=30)

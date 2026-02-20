"""
SDARS Demo - Full System Demonstration
Runs the complete AI pipeline without requiring API keys
Shows multi-modal disaster prediction in action
"""
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_collectors.satellite_collector import SatelliteDataCollector
from ai_models.multi_modal_predictor import MultiModalPredictor

def generate_demo_weather(scenario='normal'):
    """Generate realistic demo weather data"""
    
    if scenario == 'fire':
        return {
            'location': {'lat': 19.0760, 'lon': 72.8777},
            'temperature': 38.5,
            'pressure': 1008,
            'humidity': 22,
            'wind_speed': 25,
            'clouds': 10,
            'rain_1h': 0,
            'rain_3h': 0,
            'visibility': 7000,
            'weather_condition': 'Clear',
        }
    elif scenario == 'flood':
        return {
            'location': {'lat': 13.0827, 'lon': 80.2707},
            'temperature': 28.5,
            'pressure': 1005,
            'humidity': 95,
            'wind_speed': 35,
            'clouds': 95,
            'rain_1h': 75,
            'rain_3h': 180,
            'visibility': 2000,
            'weather_condition': 'Rain',
        }
    elif scenario == 'cyclone':
        return {
            'location': {'lat': 22.5726, 'lon': 88.3639},
            'temperature': 32.0,
            'pressure': 985,
            'humidity': 88,
            'wind_speed': 45,
            'clouds': 98,
            'rain_1h': 25,
            'rain_3h': 55,
            'visibility': 3000,
            'weather_condition': 'Storm',
        }
    else:  # normal
        return {
            'location': {'lat': 28.7041, 'lon': 77.1025},
            'temperature': 28.0,
            'pressure': 1012,
            'humidity': 65,
            'wind_speed': 12,
            'clouds': 40,
            'rain_1h': 0,
            'rain_3h': 0,
            'visibility': 10000,
            'weather_condition': 'Partly Cloudy',
        }

def generate_demo_historical(scenario='normal'):
    """Generate demo historical weather data"""
    
    if scenario == 'fire':
        # Show gradual temperature rise
        temps = [28, 29, 30, 32, 33, 35, 36, 37, 38, 38.5]
        pressures = [1012, 1011, 1011, 1010, 1009, 1009, 1008, 1008, 1008, 1008]
        humidities = [55, 50, 45, 40, 35, 30, 28, 25, 23, 22]
    elif scenario == 'flood':
        temps = [29, 29, 28.5, 28.5, 28, 28, 28.5, 28.5, 28.5, 28.5]
        pressures = [1010, 1009, 1008, 1007, 1006, 1005, 1005, 1005, 1005, 1005]
        humidities = [70, 75, 78, 82, 85, 88, 90, 92, 94, 95]
    elif scenario == 'cyclone':
        # Show rapid pressure drop
        temps = [30, 30, 31, 31.5, 32, 32, 32, 32, 32, 32]
        pressures = [1010, 1008, 1005, 1000, 995, 992, 990, 987, 985, 985]
        humidities = [65, 68, 72, 75, 78, 82, 84, 86, 88, 88]
    else:
        temps = [27, 27, 27.5, 28, 28, 28, 28, 28, 28, 28]
        pressures = [1012, 1012, 1012, 1012, 1012, 1012, 1012, 1012, 1012, 1012]
        humidities = [65, 64, 65, 66, 65, 65, 65, 65, 65, 65]
    
    df = pd.DataFrame({
        'temperature': temps,
        'pressure': pressures,
        'humidity': humidities,
        'wind_speed': np.abs(np.random.randn(10) * 3 + 12),
        'rainfall': [0] * 10 if scenario != 'flood' else [5, 8, 12, 18, 25, 35, 45, 55, 65, 75],
    })
    
    return df

def generate_demo_weather_changes(historical_df):
    """Calculate weather changes from historical data"""
    
    if len(historical_df) < 2:
        return {}
    
    recent = historical_df.iloc[-1]
    
    changes = {}
    for window in [1, 3, 6]:
        if len(historical_df) > window:
            past = historical_df.iloc[-(window+1)]
            changes[f'temp_change_{window}h'] = recent['temperature'] - past['temperature']
            changes[f'pressure_change_{window}h'] = recent['pressure'] - past['pressure']
            changes[f'humidity_change_{window}h'] = recent['humidity'] - past['humidity']
            changes[f'wind_change_{window}h'] = recent['wind_speed'] - past['wind_speed']
    
    return changes

def run_scenario_demo(scenario_name, scenario_type):
    """Run a complete prediction scenario"""
    
    print(f"\n{'='*70}")
    print(f"🎬 SCENARIO: {scenario_name}")
    print(f"{'='*70}\n")
    
    # Initialize components
    satellite_collector = SatelliteDataCollector()
    predictor = MultiModalPredictor()
    
    # Generate data
    print("📊 Generating scenario data...")
    current_weather = generate_demo_weather(scenario_type)
    historical_weather = generate_demo_historical(scenario_type)
    weather_changes = generate_demo_weather_changes(historical_weather)
    satellite_data = satellite_collector.generate_synthetic_satellite_image(
        disaster_type=scenario_type if scenario_type != 'normal' else 'normal'
    )
    
    print(f"   ✓ Location: {current_weather['location']}")
    print(f"   ✓ Current Weather: {current_weather['temperature']}°C, "
          f"{current_weather['humidity']}% humidity, {current_weather['pressure']} hPa")
    print(f"   ✓ Wind: {current_weather['wind_speed']} km/h")
    print(f"   ✓ Rainfall: {current_weather['rain_1h']} mm/h")
    
    # Show weather changes
    print(f"\n📈 Weather Changes:")
    for key, value in list(weather_changes.items())[:6]:
        print(f"   • {key}: {value:+.2f}")
    
    # Show satellite analysis
    thermal = satellite_data['analysis']['thermal']
    print(f"\n🛰️ Satellite Analysis:")
    print(f"   • Mean Temperature: {thermal['mean_temperature']:.1f}°C")
    print(f"   • Max Temperature: {thermal['max_temperature']:.1f}°C")
    print(f"   • Thermal Hotspots: {thermal['hotspot_percentage']:.2f}%")
    
    # Run AI prediction
    print(f"\n🤖 Running Multi-Modal AI Prediction...")
    predictions = predictor.predict_all_disasters(
        satellite_data=satellite_data,
        current_weather=current_weather,
        historical_weather=historical_weather,
        weather_changes=weather_changes
    )
    
    # Display results
    print(f"\n🚨 PREDICTION RESULTS:")
    print(f"   PRIMARY THREAT: {predictions['primary_threat'].upper()}")
    print(f"   OVERALL RISK LEVEL: {predictions['overall_risk_level']}")
    
    for disaster_type in ['fire', 'flood', 'cyclone']:
        pred = predictions[disaster_type]
        emoji = '🔥' if disaster_type == 'fire' else '🌊' if disaster_type == 'flood' else '🌪️'
        
        print(f"\n   {emoji} {disaster_type.upper()}:")
        print(f"      Risk Level: {pred['risk_level']}")
        print(f"      Confidence: {pred['confidence']:.1%}")
        print(f"      Satellite Contribution: {pred['satellite_contribution']:.1%}")
        print(f"      Weather Contribution: {pred['weather_contribution']:.1%}")
        print(f"      Reasons:")
        for reason in pred['reasons']:
            print(f"        • {reason}")
    
    print(f"\n{'='*70}\n")

def main():
    """Main demo function"""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🛰️  SDARS - AI DISASTER PREDICTION SYSTEM                      ║
║   Multi-Modal Analysis: Satellite + Weather Data                ║
║                                                                  ║
║   LIVE DEMONSTRATION                                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    print("This demo shows how SDARS combines:")
    print("  1️⃣  Satellite imagery (thermal, NDVI, NDWI)")
    print("  2️⃣  Current weather conditions")
    print("  3️⃣  Weather changes over time (KEY for prediction!)")
    print("  4️⃣  AI analysis to predict disasters\n")
    
    input("Press Enter to start the demonstration...")
    
    # Run different scenarios
    scenarios = [
        ("Normal Conditions - Delhi", "normal"),
        ("Fire Risk - Mumbai (Hot, Dry, Windy)", "fire"),
        ("Flood Risk - Chennai (Heavy Rainfall)", "flood"),
        ("Cyclone Risk - Kolkata (Pressure Drop)", "cyclone"),
    ]
    
    for scenario_name, scenario_type in scenarios:
        run_scenario_demo(scenario_name, scenario_type)
        if scenario_type != scenarios[-1][1]:
            input("\nPress Enter to continue to next scenario...")
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ✅ DEMO COMPLETE                                               ║
║                                                                  ║
║   The AI successfully analyzed:                                 ║
║   • Satellite thermal data                                      ║
║   • Weather conditions                                          ║
║   • Weather changes over time                                   ║
║                                                                  ║
║   And predicted disaster risks with detailed reasoning!        ║
║                                                                  ║
║   🚀 Next Steps:                                                 ║
║   1. Get free OpenWeather API key                               ║
║   2. Run python services/realtime_monitor.py                    ║
║   3. Run python api/server.py for REST API                      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    main()

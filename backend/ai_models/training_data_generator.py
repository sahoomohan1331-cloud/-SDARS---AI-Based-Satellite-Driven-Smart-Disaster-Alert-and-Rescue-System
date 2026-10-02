"""
SDARS Training Data Generator - High Precision Multi-Hazard Physics Engine
Generates realistic synthetic disaster data based on satellite telemetry & empirical physics
Covers ALL 8 Hazard Types:
  1. Cyclone
  2. Flood
  3. Drought
  4. Heatwave
  5. Lightning
  6. Landslide
  7. Storm Surge
  8. Wildfire
"""
import pandas as pd
import numpy as np
import os
import sys

# Add parent to path for config access
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure Windows UTF-8 stdout
try:
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import config

FEATURE_COLUMNS = [
    'temp', 'hum', 'wind', 'wind_gusts', 'press', 'dew_point',
    'soil_moisture', 'elevation', 'rain_1h', 'forecast_rain_24h',
    'ndvi', 'ndwi', 'hotspots'
]

TARGET_COLUMNS = [
    'cyclone_risk', 'flood_risk', 'drought_risk', 'heatwave_risk',
    'lightning_risk', 'landslide_risk', 'storm_surge_risk', 'fire_risk'
]

def generate_training_data(n_samples=16000):
    """
    Generates a comprehensive dataset calibrated with satellite & atmospheric physics.
    Simulates real-world physical constraints and correlation matrices across 8 hazards.
    """
    np.random.seed(42)
    print(f"🧪 Generating {n_samples} physics-calibrated multi-hazard samples...")
    
    samples_per_hazard = int(n_samples * 0.08)  # ~1,280 samples per specific hazard
    n_normal = int(n_samples * 0.28)             # ~4,480 safe baseline samples
    n_mixed = n_samples - (samples_per_hazard * 8) - n_normal  # Complex edge cases
    
    records = []

    def make_record(temp, hum, wind, wind_gusts, press, dew_point,
                    soil_moisture, elevation, rain_1h, forecast_rain_24h,
                    ndvi, ndwi, hotspots, targets):
        rec = {
            'temp': float(temp),
            'hum': float(np.clip(hum, 2, 100)),
            'wind': float(max(0, wind)),
            'wind_gusts': float(max(wind, wind_gusts)),
            'press': float(press),
            'dew_point': float(dew_point),
            'soil_moisture': float(np.clip(soil_moisture, 0.04, 0.55)),
            'elevation': float(max(0, elevation)),
            'rain_1h': float(max(0, rain_1h)),
            'forecast_rain_24h': float(max(0, forecast_rain_24h)),
            'ndvi': float(np.clip(ndvi, -0.2, 0.95)),
            'ndwi': float(np.clip(ndwi, -0.6, 0.95)),
            'hotspots': int(max(0, hotspots))
        }
        for t in TARGET_COLUMNS:
            rec[t] = int(targets.get(t, 0))
        return rec

    # 1. CYCLONE SCENARIO
    for _ in range(samples_per_hazard):
        temp = np.random.uniform(26, 33)
        hum = np.random.uniform(80, 98)
        wind = np.random.uniform(65, 160)
        gusts = wind + np.random.uniform(20, 55)
        press = np.random.uniform(915, 982)
        dew = temp - np.random.uniform(0.5, 3.0)
        sm = np.random.uniform(0.30, 0.48)
        elev = np.random.uniform(2, 80)
        rain = np.random.uniform(25, 90)
        fc_rain = np.random.uniform(80, 250)
        ndvi = np.random.uniform(0.2, 0.6)
        ndwi = np.random.uniform(0.2, 0.6)
        records.append(make_record(
            temp, hum, wind, gusts, press, dew, sm, elev, rain, fc_rain,
            ndvi, ndwi, 0, {'cyclone_risk': 1, 'storm_surge_risk': 1 if elev < 12 else 0}
        ))

    # 2. FLOOD SCENARIO
    for _ in range(samples_per_hazard):
        temp = np.random.uniform(20, 32)
        hum = np.random.uniform(82, 100)
        wind = np.random.uniform(10, 45)
        gusts = wind + np.random.uniform(5, 20)
        press = np.random.uniform(990, 1010)
        dew = temp - np.random.uniform(0.5, 2.5)
        sm = np.random.uniform(0.38, 0.52)  # Highly saturated ground
        elev = np.random.uniform(2, 60)      # Low alluvial basin
        rain = np.random.uniform(40, 130)    # Torrential rainfall
        fc_rain = np.random.uniform(70, 220)
        ndvi = np.random.uniform(0.4, 0.7)
        ndwi = np.random.uniform(0.35, 0.85) # High surface water
        records.append(make_record(
            temp, hum, wind, gusts, press, dew, sm, elev, rain, fc_rain,
            ndvi, ndwi, 0, {'flood_risk': 1}
        ))

    # 3. DROUGHT SCENARIO
    for _ in range(samples_per_hazard):
        temp = np.random.uniform(33, 46)
        hum = np.random.uniform(8, 28)
        wind = np.random.uniform(8, 30)
        gusts = wind + np.random.uniform(3, 15)
        press = np.random.uniform(1010, 1025)
        dew = np.random.uniform(2, 12)
        sm = np.random.uniform(0.04, 0.12)   # Critically dry root zone
        elev = np.random.uniform(50, 600)
        rain = 0.0
        fc_rain = np.random.uniform(0, 1.5)  # Extended aridity
        ndvi = np.random.uniform(0.06, 0.20) # Vegetation stress
        ndwi = np.random.uniform(-0.5, -0.1)
        records.append(make_record(
            temp, hum, wind, gusts, press, dew, sm, elev, rain, fc_rain,
            ndvi, ndwi, 0, {'drought_risk': 1}
        ))

    # 4. HEATWAVE SCENARIO
    for _ in range(samples_per_hazard):
        temp = np.random.uniform(40, 49)      # IMD Heatwave threshold
        hum = np.random.uniform(20, 65)
        wind = np.random.uniform(5, 25)
        gusts = wind + np.random.uniform(2, 12)
        press = np.random.uniform(1004, 1018)
        dew = np.random.uniform(18, 28)       # High heat index combo
        sm = np.random.uniform(0.08, 0.22)
        elev = np.random.uniform(20, 400)
        rain = 0.0
        fc_rain = np.random.uniform(0, 2)
        ndvi = np.random.uniform(0.15, 0.45)
        ndwi = np.random.uniform(-0.4, 0.05)
        records.append(make_record(
            temp, hum, wind, gusts, press, dew, sm, elev, rain, fc_rain,
            ndvi, ndwi, 0, {'heatwave_risk': 1}
        ))

    # 5. LIGHTNING / SEVERE CONVECTIVE STORM
    for _ in range(samples_per_hazard):
        temp = np.random.uniform(29, 38)
        hum = np.random.uniform(70, 95)
        wind = np.random.uniform(25, 60)
        gusts = np.random.uniform(50, 95)     # Squall gust front
        press = np.random.uniform(995, 1008)  # Sharp barometric drop
        dew = np.random.uniform(22, 28)       # Extreme CAPE instability
        sm = np.random.uniform(0.22, 0.40)
        elev = np.random.uniform(30, 800)
        rain = np.random.uniform(15, 65)
        fc_rain = np.random.uniform(30, 90)
        ndvi = np.random.uniform(0.3, 0.6)
        ndwi = np.random.uniform(0.0, 0.35)
        records.append(make_record(
            temp, hum, wind, gusts, press, dew, sm, elev, rain, fc_rain,
            ndvi, ndwi, 0, {'lightning_risk': 1}
        ))

    # 6. LANDSLIDE SCENARIO
    for _ in range(samples_per_hazard):
        temp = np.random.uniform(16, 28)
        hum = np.random.uniform(85, 100)
        wind = np.random.uniform(15, 50)
        gusts = wind + np.random.uniform(10, 25)
        press = np.random.uniform(992, 1012)
        dew = temp - np.random.uniform(0.5, 2.0)
        sm = np.random.uniform(0.37, 0.52)    # Regolith liquefied
        elev = np.random.uniform(120, 2200)   # Mountain relief
        rain = np.random.uniform(30, 110)     # Triggering burst
        fc_rain = np.random.uniform(60, 200)
        ndvi = np.random.uniform(0.4, 0.8)
        ndwi = np.random.uniform(0.1, 0.4)
        records.append(make_record(
            temp, hum, wind, gusts, press, dew, sm, elev, rain, fc_rain,
            ndvi, ndwi, 0, {'landslide_risk': 1}
        ))

    # 7. STORM SURGE SCENARIO
    for _ in range(samples_per_hazard):
        temp = np.random.uniform(25, 32)
        hum = np.random.uniform(80, 98)
        wind = np.random.uniform(55, 130)     # Force pushing sea water
        gusts = wind + np.random.uniform(20, 50)
        press = np.random.uniform(925, 985)   # Deep barometric suction
        dew = temp - np.random.uniform(1, 3)
        sm = np.random.uniform(0.30, 0.50)
        elev = np.random.uniform(0.5, 9.0)    # Sea-level coastline (<10m)
        rain = np.random.uniform(20, 80)
        fc_rain = np.random.uniform(50, 180)
        ndvi = np.random.uniform(0.1, 0.4)
        ndwi = np.random.uniform(0.3, 0.7)
        records.append(make_record(
            temp, hum, wind, gusts, press, dew, sm, elev, rain, fc_rain,
            ndvi, ndwi, 0, {'storm_surge_risk': 1, 'cyclone_risk': 1}
        ))

    # 8. WILDFIRE SCENARIO
    for _ in range(samples_per_hazard):
        temp = np.random.uniform(35, 48)
        hum = np.random.uniform(6, 22)        # Parched air
        wind = np.random.uniform(25, 60)      # High ember-spreading wind
        gusts = wind + np.random.uniform(15, 35)
        press = np.random.uniform(1005, 1022)
        dew = np.random.uniform(1, 10)
        sm = np.random.uniform(0.04, 0.12)    # Bone-dry topsoil
        elev = np.random.uniform(80, 1200)
        rain = 0.0
        fc_rain = 0.0
        ndvi = np.random.uniform(0.08, 0.25)  # Dead dry vegetation fuel
        ndwi = np.random.uniform(-0.5, -0.15)
        hotspots = np.random.randint(2, 18)   # Thermal anomalies
        records.append(make_record(
            temp, hum, wind, gusts, press, dew, sm, elev, rain, fc_rain,
            ndvi, ndwi, hotspots, {'fire_risk': 1}
        ))

    # 9. NORMAL / SAFE CONDITIONS
    for _ in range(n_normal):
        temp = np.random.uniform(18, 31)
        hum = np.random.uniform(40, 68)
        wind = np.random.uniform(3, 22)
        gusts = wind + np.random.uniform(1, 8)
        press = np.random.uniform(1010, 1022)
        dew = np.random.uniform(10, 18)
        sm = np.random.uniform(0.20, 0.32)
        elev = np.random.uniform(15, 600)
        rain = np.random.uniform(0, 4)
        fc_rain = np.random.uniform(0, 10)
        ndvi = np.random.uniform(0.40, 0.75)
        ndwi = np.random.uniform(-0.25, 0.15)
        records.append(make_record(
            temp, hum, wind, gusts, press, dew, sm, elev, rain, fc_rain,
            ndvi, ndwi, 0, {}
        ))

    # 10. MIXED & EDGE CASES
    for _ in range(n_mixed):
        temp = np.random.uniform(12, 42)
        hum = np.random.uniform(15, 88)
        wind = np.random.uniform(5, 55)
        gusts = wind + np.random.uniform(3, 18)
        press = np.random.uniform(980, 1025)
        dew = np.random.uniform(5, 24)
        sm = np.random.uniform(0.10, 0.40)
        elev = np.random.uniform(5, 1200)
        rain = np.random.uniform(0, 30)
        fc_rain = np.random.uniform(0, 50)
        ndvi = np.random.uniform(0.15, 0.70)
        ndwi = np.random.uniform(-0.30, 0.30)
        hotspots = 1 if np.random.rand() < 0.05 else 0
        records.append(make_record(
            temp, hum, wind, gusts, press, dew, sm, elev, rain, fc_rain,
            ndvi, ndwi, hotspots, {}
        ))

    df = pd.DataFrame(records)
    
    # Add realistic 3% label noise for generalization
    noise_indices = np.random.choice(len(df), int(len(df) * 0.03), replace=False)
    for idx in noise_indices:
        target = np.random.choice(TARGET_COLUMNS)
        df.loc[idx, target] = 1 - df.loc[idx, target]

    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"   ✓ Generated {len(df)} calibrated records across {len(FEATURE_COLUMNS)} features.")
    for t in TARGET_COLUMNS:
        print(f"   • {t:18}: {df[t].sum()} positive cases ({df[t].mean()*100:.1f}%)")

    return df

def save_training_data(df: pd.DataFrame, filename='disaster_data.csv'):
    training_dir = os.path.join(config.DATA_DIR, 'training')
    os.makedirs(training_dir, exist_ok=True)
    filepath = os.path.join(training_dir, filename)
    df.to_csv(filepath, index=False)
    print(f"   ✓ Saved training data to: {filepath}")
    return filepath

if __name__ == "__main__":
    df = generate_training_data(16000)
    save_training_data(df)

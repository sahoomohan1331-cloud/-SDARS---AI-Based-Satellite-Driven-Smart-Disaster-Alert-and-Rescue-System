"""
SDARS Training Data Generator
Generates realistic synthetic disaster data based on real-world physics
"""
import pandas as pd
import numpy as np
import os
import sys

# Add parent to path for config access
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def generate_training_data(n_samples=10000):
    """
    Generates a comprehensive synthetic dataset for disaster prediction.
    
    Features (7):
        - temp: Temperature (°C)
        - hum: Humidity (%)
        - wind: Wind Speed (km/h)
        - press: Atmospheric Pressure (hPa)
        - ndvi: Normalized Difference Vegetation Index (0-1)
        - ndwi: Normalized Difference Water Index (-1 to 1)
        - hotspots: Thermal hotspot count
    
    Labels (3 binary):
        - fire_risk: 0/1
        - flood_risk: 0/1
        - cyclone_risk: 0/1
    
    The data simulates realistic correlations:
        - Fire: High temp + Low humidity + Hotspots + Dry vegetation
        - Flood: High rainfall + High NDWI (water) + Low pressure
        - Cyclone: Extreme low pressure + High wind + High humidity
    """
    np.random.seed(42)
    
    print(f"🧪 Generating {n_samples} synthetic disaster samples...")
    
    # ======================
    # SCENARIO 1: FIRE CONDITIONS (20% of data)
    # ======================
    n_fire = int(n_samples * 0.20)
    fire_data = {
        'temp': np.random.uniform(35, 50, n_fire),  # Hot
        'hum': np.random.uniform(5, 25, n_fire),     # Dry
        'wind': np.random.uniform(15, 60, n_fire),   # Moderate to high
        'press': np.random.uniform(1005, 1025, n_fire),  # Normal
        'ndvi': np.random.uniform(0.05, 0.25, n_fire),   # Dry vegetation
        'ndwi': np.random.uniform(-0.5, 0.1, n_fire),    # No water
        'hotspots': np.random.poisson(3, n_fire),        # Active hotspots
        'fire_risk': 1,
        'flood_risk': 0,
        'cyclone_risk': 0
    }
    
    # ======================
    # SCENARIO 2: FLOOD CONDITIONS (20% of data)
    # ======================
    n_flood = int(n_samples * 0.20)
    flood_data = {
        'temp': np.random.uniform(15, 30, n_flood),      # Moderate temp
        'hum': np.random.uniform(80, 100, n_flood),      # Very humid
        'wind': np.random.uniform(5, 30, n_flood),       # Low to moderate
        'press': np.random.uniform(990, 1010, n_flood),  # Lower pressure (rain)
        'ndvi': np.random.uniform(0.4, 0.8, n_flood),    # Healthy vegetation
        'ndwi': np.random.uniform(0.4, 0.9, n_flood),    # High water presence
        'hotspots': np.zeros(n_flood, dtype=int),        # No hotspots
        'fire_risk': 0,
        'flood_risk': 1,
        'cyclone_risk': 0
    }
    
    # ======================
    # SCENARIO 3: CYCLONE CONDITIONS (15% of data)
    # ======================
    n_cyclone = int(n_samples * 0.15)
    cyclone_data = {
        'temp': np.random.uniform(25, 35, n_cyclone),    # Warm (tropical)
        'hum': np.random.uniform(75, 95, n_cyclone),     # High humidity
        'wind': np.random.uniform(65, 150, n_cyclone),   # Extreme wind
        'press': np.random.uniform(920, 985, n_cyclone), # Very low pressure
        'ndvi': np.random.uniform(0.2, 0.5, n_cyclone),  # Mixed vegetation
        'ndwi': np.random.uniform(0.1, 0.5, n_cyclone),  # Moderate water
        'hotspots': np.zeros(n_cyclone, dtype=int),      # No hotspots
        'fire_risk': 0,
        'flood_risk': 0,
        'cyclone_risk': 1
    }
    
    # ======================
    # SCENARIO 4: NORMAL CONDITIONS (35% of data)
    # ======================
    n_normal = int(n_samples * 0.35)
    normal_data = {
        'temp': np.random.uniform(15, 32, n_normal),     # Pleasant
        'hum': np.random.uniform(40, 70, n_normal),      # Normal humidity
        'wind': np.random.uniform(0, 25, n_normal),      # Calm
        'press': np.random.uniform(1010, 1025, n_normal),# Normal pressure
        'ndvi': np.random.uniform(0.4, 0.8, n_normal),   # Healthy vegetation
        'ndwi': np.random.uniform(-0.2, 0.3, n_normal),  # Normal water
        'hotspots': np.zeros(n_normal, dtype=int),       # No hotspots
        'fire_risk': 0,
        'flood_risk': 0,
        'cyclone_risk': 0
    }
    
    # ======================
    # SCENARIO 5: EDGE CASES / MIXED (10% of data)
    # ======================
    n_edge = n_samples - n_fire - n_flood - n_cyclone - n_normal
    edge_data = {
        'temp': np.random.uniform(10, 45, n_edge),
        'hum': np.random.uniform(20, 90, n_edge),
        'wind': np.random.uniform(5, 80, n_edge),
        'press': np.random.uniform(970, 1030, n_edge),
        'ndvi': np.random.uniform(0.1, 0.7, n_edge),
        'ndwi': np.random.uniform(-0.3, 0.5, n_edge),
        'hotspots': np.random.poisson(0.3, n_edge),
        'fire_risk': 0,
        'flood_risk': 0,
        'cyclone_risk': 0
    }
    
    # Combine all scenarios
    all_data = []
    for scenario in [fire_data, flood_data, cyclone_data, normal_data, edge_data]:
        n = len(scenario['temp'])
        df = pd.DataFrame({
            'temp': scenario['temp'],
            'hum': scenario['hum'],
            'wind': scenario['wind'],
            'press': scenario['press'],
            'ndvi': scenario['ndvi'],
            'ndwi': scenario['ndwi'],
            'hotspots': scenario['hotspots'],
            'fire_risk': [scenario['fire_risk']] * n if isinstance(scenario['fire_risk'], int) else scenario['fire_risk'],
            'flood_risk': [scenario['flood_risk']] * n if isinstance(scenario['flood_risk'], int) else scenario['flood_risk'],
            'cyclone_risk': [scenario['cyclone_risk']] * n if isinstance(scenario['cyclone_risk'], int) else scenario['cyclone_risk'],
        })
        all_data.append(df)
    
    data = pd.concat(all_data, ignore_index=True)
    
    # Add realistic noise (5% label noise for robustness)
    noise_indices = np.random.choice(len(data), int(len(data) * 0.05), replace=False)
    for idx in noise_indices:
        # Flip one random label
        label = np.random.choice(['fire_risk', 'flood_risk', 'cyclone_risk'])
        data.loc[idx, label] = 1 - data.loc[idx, label]
    
    # Shuffle the data
    data = data.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"   ✓ Generated {len(data)} samples")
    print(f"   ✓ Fire events: {data['fire_risk'].sum()} ({data['fire_risk'].mean()*100:.1f}%)")
    print(f"   ✓ Flood events: {data['flood_risk'].sum()} ({data['flood_risk'].mean()*100:.1f}%)")
    print(f"   ✓ Cyclone events: {data['cyclone_risk'].sum()} ({data['cyclone_risk'].mean()*100:.1f}%)")
    
    return data


def save_training_data(df: pd.DataFrame, filename='disaster_data.csv'):
    """Save generated data to CSV"""
    training_dir = os.path.join(config.DATA_DIR, 'training')
    os.makedirs(training_dir, exist_ok=True)
    
    filepath = os.path.join(training_dir, filename)
    df.to_csv(filepath, index=False)
    print(f"   ✓ Dataset saved to: {filepath}")
    return filepath


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🧪 SDARS TRAINING DATA GENERATOR                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    df = generate_training_data(n_samples=10000)
    save_training_data(df)
    
    print("\n📊 Sample Data Preview:")
    print(df.head(10).to_string())
    
    print("\n✅ Training data generation complete!")

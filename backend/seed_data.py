from db.database import SessionLocal, PredictionRecord, init_db
from datetime import datetime, timedelta
import random

def populate_demo_data():
    init_db()
    db = SessionLocal()
    
    # Check if we already have data
    count = db.query(PredictionRecord).count()
    if count > 5:
        print(f"✅ Database already has {count} records. Skipping population.")
        return

    print("🌱 Seeding database with demo data...")
    
    locations = [
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "risk": "LOW", "threat": "flood"},
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "risk": "HIGH", "threat": "fire"},
        {"name": "New York", "lat": 40.7128, "lon": -74.0060, "risk": "MEDIUM", "threat": "cyclone"},
        {"name": "London", "lat": 51.5074, "lon": -0.1278, "risk": "LOW", "threat": "flood"},
        {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "risk": "HIGH", "threat": "fire"}
    ]
    
    for i, loc in enumerate(locations):
        # Create records with timestamps staggered over the last few hours
        timestamp = datetime.utcnow() - timedelta(minutes=i*15)
        
        record = PredictionRecord(
            location_name=loc["name"],
            latitude=loc["lat"],
            longitude=loc["lon"],
            overall_risk=loc["risk"],
            primary_threat=loc["threat"],
            timestamp=timestamp,
            weather_data={
                "temperature": random.randint(20, 35),
                "humidity": random.randint(40, 90),
                "pressure": 1012
            },
            risk_scores={
                "fire": 0.8 if loc["threat"] == "fire" else 0.1,
                "flood": 0.5 if loc["threat"] == "flood" else 0.1,
                "cyclone": 0.6 if loc["threat"] == "cyclone" else 0.1
            }
        )
        db.add(record)
        print(f"  + Added record for {loc['name']}")
        
    db.commit()
    db.close()
    print("✅ Database seeding complete!")

if __name__ == "__main__":
    populate_demo_data()

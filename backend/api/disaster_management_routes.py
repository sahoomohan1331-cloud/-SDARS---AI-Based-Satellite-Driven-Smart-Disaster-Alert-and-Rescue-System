"""
SDARS Disaster Management Routes
Implements:
- Sprint 3: Crowdsourced citizen reports & river level gauge sensors
- Sprint 4: Resource planning inventory, impact-based allocation, road status, vehicle GPS tracking
- Sprint 5: Historical disaster benchmarks & records
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import math
import random

from db.database import get_db, CrowdReport, RiverGauge, Resource, HistoricalDisaster

router = APIRouter(prefix="/api", tags=["Disaster Management"])

# ═══════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class CrowdReportCreate(BaseModel):
    latitude: float
    longitude: float
    location_name: Optional[str] = "Current Location"
    report_type: str = Field(..., description="smoke, flooding, tremor, blocked_road, storm_damage, heat_distress")
    description: str
    severity: str = Field(default="MODERATE", description="LOW, MODERATE, HIGH, CRITICAL")
    reporter_id: Optional[str] = "Citizen Reporter"
    photo_url: Optional[str] = None

class ResourceCreate(BaseModel):
    name: str
    resource_type: str = Field(..., description="shelter, hospital, fire_station, vehicle, warehouse")
    latitude: float
    longitude: float
    capacity: int = 100
    current_occupancy: int = 0
    status: str = "AVAILABLE"
    contact_info: Optional[str] = None

class AllocationRequest(BaseModel):
    disaster_type: str
    target_latitude: float
    target_longitude: float
    severity: str = "HIGH"
    required_shelter_capacity: int = 200
    required_vehicles: int = 3

class RoadBlockReport(BaseModel):
    road_name: str
    latitude: float
    longitude: float
    status: str = Field(default="BLOCKED", description="BLOCKED, WATERLOGGED, LANDSLIDE, PASSABLE")
    severity: str = "HIGH"
    description: str

class GaugeSimulateRequest(BaseModel):
    station_id: int = 1
    delta_meters: float = 0.5

# ═══════════════════════════════════════════════════════════════════════
# HELPER: DISTANCE CALCULATION (Haversine km)
# ═══════════════════════════════════════════════════════════════════════

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

# ═══════════════════════════════════════════════════════════════════════
# SEEDING HELPERS FOR REALISTIC DEMO
# ═══════════════════════════════════════════════════════════════════════

def seed_default_data_if_empty(db: Session):
    from db.database import init_db
    init_db()
    
    # 1. Seed River Gauges
    if db.query(RiverGauge).count() == 0:
        gauges = [
            RiverGauge(station_name="Yamuna - Old Railway Bridge (Delhi)", latitude=28.6650, longitude=77.2490, water_level_m=205.33, danger_level_m=205.33, flow_rate=1250.0, status="ALERT"),
            RiverGauge(station_name="Mithi River - Kurla (Mumbai)", latitude=19.0720, longitude=72.8790, water_level_m=3.85, danger_level_m=4.20, flow_rate=320.0, status="NORMAL"),
            RiverGauge(station_name="Hooghly River - Howrah (Kolkata)", latitude=22.5850, longitude=88.3450, water_level_m=6.40, danger_level_m=7.00, flow_rate=2100.0, status="NORMAL"),
            RiverGauge(station_name="Brahmaputra - Guwahati (Assam)", latitude=26.1850, longitude=91.7500, water_level_m=49.80, danger_level_m=49.68, flow_rate=14200.0, status="DANGER"),
            RiverGauge(station_name="Godavari - Rajahmundry (AP)", latitude=17.0000, longitude=81.7800, water_level_m=14.20, danger_level_m=16.50, flow_rate=4500.0, status="NORMAL"),
            RiverGauge(station_name="Mahanadi - Cuttack (Odisha)", latitude=20.4625, longitude=85.8828, water_level_m=25.60, danger_level_m=26.41, flow_rate=5800.0, status="ALERT")
        ]
        db.add_all(gauges)
        db.commit()

    # 2. Seed Resources
    if db.query(Resource).count() == 0:
        resources = [
            Resource(name="Central Flood Evacuation Shelter", resource_type="shelter", latitude=28.6300, longitude=77.2200, capacity=800, current_occupancy=250, status="AVAILABLE", contact_info="+91 11 2345 6789"),
            Resource(name="AIIMS Emergency Trauma Response Hub", resource_type="hospital", latitude=28.5672, longitude=77.2100, capacity=350, current_occupancy=280, status="AVAILABLE", contact_info="+91 11 2658 8500"),
            Resource(name="NDRF 8th Battalion Mobile Fleet", resource_type="vehicle", latitude=28.6000, longitude=77.2500, capacity=50, current_occupancy=15, status="AVAILABLE", contact_info="+91 120 276 6013"),
            Resource(name="Bandra Cyclone Relief Center", resource_type="shelter", latitude=19.0596, longitude=72.8295, capacity=600, current_occupancy=120, status="AVAILABLE", contact_info="+91 22 2642 1234"),
            Resource(name="Mumbai Fire Brigade Heavy Rescue Unit", resource_type="vehicle", latitude=18.9600, longitude=72.8300, capacity=30, current_occupancy=5, status="AVAILABLE", contact_info="101 / +91 22 2307 6111"),
            Resource(name="Odisha Disaster Rapid Action Force (ODRAF)", resource_type="vehicle", latitude=20.2961, longitude=85.8245, capacity=120, current_occupancy=40, status="AVAILABLE", contact_info="+91 674 253 4177"),
            Resource(name="Red Cross Emergency Medical Warehouse", resource_type="warehouse", latitude=22.5726, longitude=88.3639, capacity=5000, current_occupancy=1200, status="AVAILABLE", contact_info="+91 33 2286 1234")
        ]
        db.add_all(resources)
        db.commit()

    # 3. Seed Historical Disasters
    if db.query(HistoricalDisaster).count() == 0:
        events = [
            HistoricalDisaster(disaster_name="Cyclone Fani", disaster_type="cyclone", location_name="Odisha Coast", country="India", latitude=19.8135, longitude=85.8312, year=2019, severity="CRITICAL", casualties=89, economic_loss_usd_m=8100.0, description="Category 5 equivalent tropical cyclone with peak winds of 280 km/h; massive evacuation saved tens of thousands."),
            HistoricalDisaster(disaster_name="Great Kerala Floods", disaster_type="flood", location_name="Kerala State", country="India", latitude=9.9312, longitude=76.2673, year=2018, severity="CRITICAL", casualties=483, economic_loss_usd_m=4200.0, description="Severe flooding caused by unusually heavy monsoon rainfall; worst flood in Kerala in nearly a century."),
            HistoricalDisaster(disaster_name="Wayanad Landslides", disaster_type="landslide", location_name="Meppadi, Wayanad", country="India", latitude=11.5540, longitude=76.1265, year=2024, severity="CRITICAL", casualties=420, economic_loss_usd_m=280.0, description="Torrential rainfall triggered massive multiple landslides sweeping away settlements in Punjirimattom and Mundakkai."),
            HistoricalDisaster(disaster_name="Maharashtra Heatwave", disaster_type="heatwave", location_name="Vidarbha & Marathwada", country="India", latitude=21.1458, longitude=79.0882, year=2022, severity="HIGH", casualties=25, economic_loss_usd_m=450.0, description="Prolonged temperature wave exceeding 46°C affecting agriculture and water security."),
            HistoricalDisaster(disaster_name="Cyclone Amphan", disaster_type="cyclone", location_name="West Bengal & Bangladesh", country="India", latitude=21.7000, longitude=88.2000, year=2020, severity="CRITICAL", casualties=128, economic_loss_usd_m=13000.0, description="Super Cyclonic Storm causing storm surge and flooding across Kolkata and Sundarbans."),
            HistoricalDisaster(disaster_name="Chennai Floods", disaster_type="flood", location_name="Chennai", country="India", latitude=13.0827, longitude=80.2707, year=2015, severity="CRITICAL", casualties=500, economic_loss_usd_m=3000.0, description="Record 494 mm rainfall in 24 hours led to complete urban submergence and airport shutdown.")
        ]
        db.add_all(events)
        db.commit()

    # 4. Seed initial Crowd Reports
    if db.query(CrowdReport).count() == 0:
        reports = [
            CrowdReport(latitude=28.6700, longitude=77.2400, location_name="Kashmere Gate Lowlands", report_type="flooding", description="Water level rising rapidly over the embankment near ring road. 2 ft water logged.", severity="HIGH", reporter_id="Local Commuter", is_verified=1),
            CrowdReport(latitude=19.0600, longitude=72.8400, location_name="BKC Junction", report_type="blocked_road", description="Tree fallen across 2 lanes following severe squalls. Traffic completely halted.", severity="MODERATE", reporter_id="Traffic Marshal", is_verified=1),
            CrowdReport(latitude=22.5600, longitude=88.3500, location_name="Park Street Outskirts", report_type="smoke", description="Dense smoke observed near electrical transformer following power line snap.", severity="MODERATE", reporter_id="Resident Society", is_verified=0)
        ]
        db.add_all(reports)
        db.commit()

# Simulated live vehicle tracking database
MOCK_LIVE_VEHICLES = [
    {"vehicle_id": "NDRF-V101", "team": "8th Battalion NDRF Alpha", "type": "Amphibious Rescue Boat", "latitude": 28.6600, "longitude": 77.2450, "speed_kmh": 22.5, "status": "EN_ROUTE", "mission": "Evacuation assistance at Yamuna floodplains"},
    {"vehicle_id": "SDRF-AMB-04", "team": "Emergency Medical Corps 4", "type": "Advanced Life Support Ambulance", "latitude": 28.5800, "longitude": 77.2150, "speed_kmh": 45.0, "status": "STANDBY", "mission": "AIIMS Trauma Corridor Standby"},
    {"vehicle_id": "FIRE-HT-12", "team": "Delhi Fire Service HazMat", "type": "Heavy Fire Tender", "latitude": 28.6350, "longitude": 77.2250, "speed_kmh": 0.0, "status": "DEPLOYED", "mission": "Structure cooling & clearing"},
    {"vehicle_id": "ODRAF-BOAT-02", "team": "Odisha Rapid Action Fleet", "type": "Flood Inflatable Rescue", "latitude": 20.2900, "longitude": 85.8200, "speed_kmh": 18.0, "status": "PATROL", "mission": "Mahanadi basin patrol"}
]

# Simulated live road status network
MOCK_ROAD_STATUSES = [
    {"road_id": "RD-001", "name": "Yamuna Ring Road Bypass", "latitude": 28.6650, "longitude": 77.2420, "status": "BLOCKED", "reason": "River overflow & 0.8m waterlogging", "detour": "Use Vikas Marg Flyover"},
    {"road_id": "RD-002", "name": "Western Express Highway (Near Airport)", "latitude": 19.0950, "longitude": 72.8520, "status": "OPEN", "reason": "Clear, moderate traffic", "detour": None},
    {"road_id": "RD-003", "name": "Ghatkopar Link Road", "latitude": 19.0850, "longitude": 72.9050, "status": "WATERLOGGED", "reason": "Slow moving 1.5ft water on curb lanes", "detour": "Proceed via Eastern Freeway"},
    {"road_id": "RD-004", "name": "Mundakkai Ghat Access Road", "latitude": 11.5510, "longitude": 76.1280, "status": "LANDSLIDE", "reason": "Debris flow obstruction, emergency clearance in progress", "detour": "Alternate bypass through Meppadi North"}
]

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 3: CROWDSOURCED CITIZEN REPORTS & SENSORS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/crowd/report")
async def submit_crowd_report(report: CrowdReportCreate, db: Session = Depends(get_db)):
    """
    Sprint 3: Citizen Ground-Truth Submission
    Allows citizens or field responders to submit verified/unverified ground observations.
    """
    seed_default_data_if_empty(db)
    
    new_report = CrowdReport(
        latitude=report.latitude,
        longitude=report.longitude,
        location_name=report.location_name,
        report_type=report.report_type.lower(),
        description=report.description,
        severity=report.severity.upper(),
        reporter_id=report.reporter_id,
        is_verified=0,  # Requires authority verification
        photo_url=report.photo_url,
        timestamp=datetime.utcnow()
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return {
        "status": "success",
        "message": "Ground-truth citizen report submitted successfully. Queued for verification.",
        "report_id": new_report.id,
        "is_verified": bool(new_report.is_verified)
    }

@router.get("/crowd/reports")
async def list_crowd_reports(
    verified_only: Optional[bool] = False,
    severity: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Sprint 3: Retrieve crowd reports for authority map overlay
    """
    seed_default_data_if_empty(db)
    
    query = db.query(CrowdReport)
    if verified_only:
        query = query.filter(CrowdReport.is_verified == 1)
    if severity:
        query = query.filter(CrowdReport.severity == severity.upper())
        
    reports = query.order_by(CrowdReport.timestamp.desc()).limit(limit).all()
    
    return {
        "status": "success",
        "count": len(reports),
        "reports": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "location_name": r.location_name,
                "report_type": r.report_type,
                "description": r.description,
                "severity": r.severity,
                "reporter_id": r.reporter_id,
                "is_verified": r.is_verified,
                "photo_url": r.photo_url
            }
            for r in reports
        ]
    }

@router.post("/crowd/verify/{report_id}")
async def verify_crowd_report(report_id: int, action: str = Body(embed=True), db: Session = Depends(get_db)):
    """
    Sprint 3: Authority verification workflow
    action: 'verify' (1) or 'reject' (-1)
    """
    report = db.query(CrowdReport).filter(CrowdReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Crowd report not found")
        
    if action == "verify":
        report.is_verified = 1
    elif action == "reject":
        report.is_verified = -1
    else:
        raise HTTPException(status_code=400, detail="Action must be 'verify' or 'reject'")
        
    db.commit()
    return {"status": "success", "report_id": report_id, "new_verification_status": report.is_verified}

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 3 & 5: RIVER-LEVEL GAUGE SENSORS & TELEMETRY
# ═══════════════════════════════════════════════════════════════════════

@router.get("/gauges")
async def get_river_gauges(db: Session = Depends(get_db)):
    """
    Sprint 3 & 5: River level telemetry feeds (Central Water Commission simulation)
    Provides real-time stream with danger thresholds, water level meters, and discharge rates.
    """
    seed_default_data_if_empty(db)
    
    gauges = db.query(RiverGauge).all()
    results = []
    
    for g in gauges:
        # Calculate headroom to danger
        headroom = round(g.danger_level_m - g.water_level_m, 2)
        pct_of_danger = round((g.water_level_m / g.danger_level_m) * 100, 1) if g.danger_level_m else 0
        
        status = g.status
        if g.water_level_m >= g.danger_level_m:
            status = "DANGER"
        elif g.water_level_m >= g.danger_level_m * 0.92:
            status = "ALERT"
        else:
            status = "NORMAL"

        results.append({
            "id": g.id,
            "station_name": g.station_name,
            "latitude": g.latitude,
            "longitude": g.longitude,
            "water_level_m": g.water_level_m,
            "danger_level_m": g.danger_level_m,
            "headroom_m": headroom,
            "pct_of_danger": pct_of_danger,
            "flow_rate_cumecs": g.flow_rate,
            "status": status,
            "timestamp": g.timestamp.isoformat() if g.timestamp else None
        })
        
    return {
        "status": "success",
        "count": len(results),
        "gauges": results
    }

@router.post("/gauges/simulate_reading")
async def simulate_gauge_reading(req: GaugeSimulateRequest, db: Session = Depends(get_db)):
    """
    Simulate real-time sensor fluctuation for demonstration/testing
    """
    gauge = db.query(RiverGauge).filter(RiverGauge.id == req.station_id).first()
    if not gauge:
        raise HTTPException(status_code=404, detail="Gauge not found")
        
    gauge.water_level_m = round(gauge.water_level_m + req.delta_meters, 2)
    gauge.timestamp = datetime.utcnow()
    
    if gauge.water_level_m >= gauge.danger_level_m:
        gauge.status = "DANGER"
    elif gauge.water_level_m >= gauge.danger_level_m * 0.92:
        gauge.status = "ALERT"
    else:
        gauge.status = "NORMAL"
        
    db.commit()
    db.refresh(gauge)
    
    return {
        "status": "success",
        "station_name": gauge.station_name,
        "new_water_level_m": gauge.water_level_m,
        "new_status": gauge.status
    }

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 4: RESOURCE PLANNING & DISPATCH MODULE
# ═══════════════════════════════════════════════════════════════════════

@router.get("/resources")
async def get_emergency_resources(resource_type: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Sprint 4: Resource planning inventory
    Tracks shelters, medical units, ambulances, rescue boats, fire tenders with live capacity.
    """
    seed_default_data_if_empty(db)
    
    query = db.query(Resource)
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type.lower())
    if status:
        query = query.filter(Resource.status == status.upper())
        
    items = query.all()
    total_capacity = sum(r.capacity for r in items if r.capacity)
    total_occupancy = sum(r.current_occupancy for r in items if r.current_occupancy)
    
    return {
        "status": "success",
        "count": len(items),
        "capacity_metrics": {
            "total_capacity": total_capacity,
            "total_occupancy": total_occupancy,
            "utilization_pct": round((total_occupancy / total_capacity * 100), 1) if total_capacity > 0 else 0
        },
        "resources": [
            {
                "id": r.id,
                "name": r.name,
                "type": r.resource_type,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "capacity": r.capacity,
                "current_occupancy": r.current_occupancy,
                "available_capacity": max(0, r.capacity - r.current_occupancy),
                "status": r.status,
                "contact_info": r.contact_info,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None
            }
            for r in items
        ]
    }

@router.post("/resources/allocate")
async def allocate_emergency_resources(request: AllocationRequest, db: Session = Depends(get_db)):
    """
    Sprint 4: Impact-Based Automated Resource Allocation Algorithm
    Matches emergency assets (shelters, medical, mobile rescue fleets) to predicted impact coordinates
    based on proximity, remaining capacity, and disaster severity tier.
    """
    seed_default_data_if_empty(db)
    
    all_resources = db.query(Resource).filter(Resource.status == "AVAILABLE").all()
    
    shelters = []
    vehicles = []
    hospitals = []
    
    for r in all_resources:
        dist_km = haversine_km(request.target_latitude, request.target_longitude, r.latitude, r.longitude)
        available_cap = max(0, r.capacity - r.current_occupancy)
        
        item_data = {
            "id": r.id,
            "name": r.name,
            "type": r.resource_type,
            "distance_km": round(dist_km, 2),
            "available_capacity": available_cap,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "contact_info": r.contact_info
        }
        
        if r.resource_type == "shelter":
            shelters.append(item_data)
        elif r.resource_type == "vehicle":
            vehicles.append(item_data)
        elif r.resource_type == "hospital":
            hospitals.append(item_data)
            
    # Sort by distance
    shelters.sort(key=lambda x: x["distance_km"])
    vehicles.sort(key=lambda x: x["distance_km"])
    hospitals.sort(key=lambda x: x["distance_km"])
    
    # Allocate shelters to fulfill capacity requirement
    allocated_shelters = []
    capacity_fulfilled = 0
    for s in shelters:
        if capacity_fulfilled >= request.required_shelter_capacity:
            break
        allocated_shelters.append(s)
        capacity_fulfilled += s["available_capacity"]
        
    # Allocate vehicles
    allocated_vehicles = vehicles[:request.required_vehicles]
    
    return {
        "status": "success",
        "incident_target": {
            "latitude": request.target_latitude,
            "longitude": request.target_longitude,
            "disaster_type": request.disaster_type,
            "severity": request.severity
        },
        "allocation_plan": {
            "shelters_dispatched": allocated_shelters,
            "capacity_fulfilled": capacity_fulfilled,
            "capacity_target": request.required_shelter_capacity,
            "vehicles_dispatched": allocated_vehicles,
            "nearest_hospitals": hospitals[:2]
        },
        "recommendation": (
            f"DISPATCH ORDER ISSUED: {len(allocated_shelters)} shelter hubs reserved for {capacity_fulfilled} evacuees. "
            f"{len(allocated_vehicles)} rescue units rerouted to incident zone."
        )
    }

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 4: REAL-TIME ROAD STATUS & RESCUE VEHICLE GPS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/roads/status")
async def get_road_statuses():
    """
    Sprint 4: Real-time road status layer (Open vs Blocked vs Waterlogged)
    Essential for hazard-aware evacuation pathing.
    """
    return {
        "status": "success",
        "roads": MOCK_ROAD_STATUSES,
        "count": len(MOCK_ROAD_STATUSES)
    }

@router.post("/roads/report_block")
async def report_road_block(block: RoadBlockReport):
    """
    Sprint 4: Report dynamically blocked road
    """
    new_entry = {
        "road_id": f"RD-{len(MOCK_ROAD_STATUSES) + 1:03d}",
        "name": block.road_name,
        "latitude": block.latitude,
        "longitude": block.longitude,
        "status": block.status,
        "reason": block.description,
        "detour": "Local detour advised by traffic control"
    }
    MOCK_ROAD_STATUSES.append(new_entry)
    return {"status": "success", "message": "Road blockage recorded and broadcast to route planner", "data": new_entry}

@router.get("/vehicles/live")
async def get_live_vehicles():
    """
    Sprint 4: Emergency vehicle real-time GPS telemetry stream
    Tracks NDRF boats, ambulances, fire tenders, and rescue vans.
    Adds slight random drift to simulate real movement during demo.
    """
    for v in MOCK_LIVE_VEHICLES:
        if v["status"] in ("EN_ROUTE", "PATROL"):
            # Subtle random walk (approx 10-20 meters per poll)
            v["latitude"] += (random.random() - 0.5) * 0.0004
            v["longitude"] += (random.random() - 0.5) * 0.0004
            v["speed_kmh"] = round(max(5.0, v["speed_kmh"] + (random.random() - 0.5) * 2.0), 1)

    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(MOCK_LIVE_VEHICLES),
        "vehicles": MOCK_LIVE_VEHICLES
    }

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 5: HISTORICAL DISASTER BENCHMARKS & RECORDS
# ═══════════════════════════════════════════════════════════════════════

@router.get("/disasters/historical")
async def get_historical_disasters(disaster_type: Optional[str] = None, country: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Sprint 5: Historical Disaster Database
    Records of past events for benchmarking model predictions and understanding regional vulnerability.
    """
    seed_default_data_if_empty(db)
    
    query = db.query(HistoricalDisaster)
    if disaster_type:
        query = query.filter(HistoricalDisaster.disaster_type == disaster_type.lower())
    if country:
        query = query.filter(HistoricalDisaster.country.ilike(f"%{country}%"))
        
    records = query.order_by(HistoricalDisaster.year.desc()).all()
    
    return {
        "status": "success",
        "count": len(records),
        "records": [
            {
                "id": r.id,
                "name": r.disaster_name,
                "type": r.disaster_type,
                "location": r.location_name,
                "country": r.country,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "year": r.year,
                "severity": r.severity,
                "casualties": r.casualties,
                "economic_loss_usd_m": r.economic_loss_usd_m,
                "description": r.description
            }
            for r in records
        ]
    }

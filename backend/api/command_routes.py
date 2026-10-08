"""
SDARS Emergency Command & Action Dispatch Router
Japan-Inspired Command & Control Decision Support System
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import os
import json

router = APIRouter(prefix="/api/command", tags=["Command & Dispatch"])

# In-memory live response state for real-time dashboard tracking
LIVE_COMMAND_STATE = {
    "active_dispatches": [],
    "counters": {
        "broadcast_alerts": 3,
        "rescue_teams_deployed": 8,
        "total_rescue_teams": 12,
        "ambulances_deployed": 6,
        "total_ambulances": 10,
        "open_shelters": 4,
        "total_shelters": 8,
        "roads_blocked": 2
    },
    "history": []
}

class DispatchRequest(BaseModel):
    action_type: str = Field(..., example="BROADCAST_L4_ALERT")
    target_zone: str = Field(..., example="Bhubaneswar Coastal Sector 4")
    latitude: float = Field(..., example=20.2961)
    longitude: float = Field(..., example=85.8245)
    commander_id: Optional[str] = Field("CMD-ALPHA-01", example="CMD-ALPHA-01")
    notes: Optional[str] = Field("Immediate Level 4 Evacuation Broadcast", example="Deploy 2 units")

class ImpactAssessmentRequest(BaseModel):
    latitude: float = Field(..., example=20.2961)
    longitude: float = Field(..., example=85.8245)
    hazard_type: str = Field(..., example="flood")
    risk_score: float = Field(..., example=0.82)
    radius_km: Optional[float] = Field(5.0, example=5.0)

@router.get("/status")
async def get_command_status():
    """
    Returns live response state, active dispatches, and emergency resource availability counters
    """
    return {
        "status": "OPERATIONAL",
        "system_mode": "JAPAN_LEVEL_4_ACTIVE",
        "timestamp": datetime.now().isoformat(),
        "resource_counters": LIVE_COMMAND_STATE["counters"],
        "active_dispatches_count": len(LIVE_COMMAND_STATE["active_dispatches"]),
        "recent_dispatches": LIVE_COMMAND_STATE["active_dispatches"][-5:],
        "dispatch_history": LIVE_COMMAND_STATE["history"][-10:]
    }

@router.post("/dispatch")
async def execute_dispatch_action(req: DispatchRequest, background_tasks: BackgroundTasks):
    """
    Executes a tactical command action:
    - BROADCAST_L4_ALERT
    - DEPLOY_RESCUE_TEAM
    - ACTIVATE_SHELTER
    - BLOCK_ROAD
    """
    dispatch_id = f"DSP-{int(datetime.now().timestamp() * 1000)}"
    timestamp = datetime.now().isoformat()

    record = {
        "dispatch_id": dispatch_id,
        "action_type": req.action_type,
        "target_zone": req.target_zone,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "commander_id": req.commander_id,
        "timestamp": timestamp,
        "notes": req.notes,
        "status": "EXECUTING"
    }

    # Update resource counters dynamically
    counters = LIVE_COMMAND_STATE["counters"]
    if req.action_type == "BROADCAST_L4_ALERT":
        counters["broadcast_alerts"] += 1
    elif req.action_type == "DEPLOY_RESCUE_TEAM":
        if counters["rescue_teams_deployed"] < counters["total_rescue_teams"]:
            counters["rescue_teams_deployed"] += 1
    elif req.action_type == "ACTIVATE_SHELTER":
        if counters["open_shelters"] < counters["total_shelters"]:
            counters["open_shelters"] += 1
    elif req.action_type == "BLOCK_ROAD":
        counters["roads_blocked"] += 1

    LIVE_COMMAND_STATE["active_dispatches"].insert(0, record)
    LIVE_COMMAND_STATE["history"].insert(0, record)

    return {
        "status": "DISPATCH_EXECUTED",
        "dispatch_id": dispatch_id,
        "message": f"Action [{req.action_type}] initialized for sector {req.target_zone}",
        "timestamp": timestamp,
        "updated_counters": counters
    }

@router.post("/impact")
async def calculate_impact_assessment(req: ImpactAssessmentRequest):
    """
    Calculates estimated population affected, infrastructure at risk, and shelter needs
    """
    # Formula calibrated against typical population density (e.g. 850 people / km²)
    area_sq_km = 3.14159 * (req.radius_km ** 2) * req.risk_score
    pop_density = 750 + int(req.risk_score * 400)
    affected_population = int(area_sq_km * pop_density)

    hospitals_affected = max(1, int(req.risk_score * 4))
    schools_affected = max(2, int(req.risk_score * 9))
    roads_blocked = max(1, int(req.risk_score * 12))
    shelters_needed = max(1, int(affected_population / 1500))

    return {
        "target_coords": {"lat": req.latitude, "lon": req.longitude},
        "hazard_type": req.hazard_type,
        "risk_score": req.risk_score,
        "estimated_affected_area_sq_km": round(area_sq_km, 2),
        "estimated_affected_population": affected_population,
        "infrastructure_at_risk": {
            "hospitals": hospitals_affected,
            "schools": schools_affected,
            "roads_blocked": roads_blocked,
            "power_substations": max(1, int(req.risk_score * 2))
        },
        "evacuation_plan": {
            "recommended_shelters_count": shelters_needed,
            "estimated_evacuation_time_mins": int(15 + req.risk_score * 35),
            "priority": "HIGH" if req.risk_score > 0.7 else "MEDIUM"
        }
    }

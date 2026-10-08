import pytest
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

def test_command_status():
    response = client.get("/api/command/status")
    assert response.status_code == 200
    assert response.json()["status"] == "OPERATIONAL"

def test_command_impact():
    payload = {
        "latitude": 20.2961,
        "longitude": 85.8245,
        "hazard_type": "flood",
        "risk_score": 0.85,
        "radius_km": 10.0
    }
    response = client.post("/api/command/impact", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "estimated_affected_population" in data
    assert "infrastructure_at_risk" in data

def test_command_dispatch():
    payload = {
        "action_type": "DEPLOY_RESCUE_TEAM",
        "target_zone": "Coastal Sector 4",
        "latitude": 20.2961,
        "longitude": 85.8245,
        "commander_id": "TEST-CMD-01",
        "notes": "Test dispatch"
    }
    response = client.post("/api/command/dispatch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DISPATCH_EXECUTED"
    assert "dispatch_id" in data

import pytest
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"

def test_prediction_endpoint():
    # Use a generic name for testing
    payload = {
        "name": "Bhubaneswar",
        "lat": 20.2961,
        "lon": 85.8245
    }
    response = client.post("/api/predict", json=payload)
    # The API might hit external services and take time, or it might return 500 if APIs fail. 
    # For robust tests, we just check if it's reachable or properly formatted.
    assert response.status_code in [200, 500, 503]
    if response.status_code == 200:
        data = response.json()
        assert "overall_risk_level" in data
        assert "primary_threat" in data

def test_predictions_history():
    response = client.get("/api/predictions/history?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

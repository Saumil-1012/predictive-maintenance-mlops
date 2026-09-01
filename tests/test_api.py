import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_predict_normal():
    response = client.post("/predict", json={
        "device_id": "machine-001",
        "temperature_c": 82.5,
        "vibration_g": 0.3,
        "pressure_bar": 104.2,
        "rpm": 2980.0
    })
    assert response.status_code == 200
    data = response.json()
    assert "is_anomaly" in data
    assert "anomaly_score" in data
    assert "alert_level" in data
    assert data["is_anomaly"] == False
    assert data["alert_level"] == "OK"


def test_predict_anomaly():
    response = client.post("/predict", json={
        "device_id": "machine-001",
        "temperature_c": 142.0,
        "vibration_g": 3.8,
        "pressure_bar": 104.2,
        "rpm": 2980.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["is_anomaly"] == True
    assert data["alert_level"] == "CRITICAL"


def test_predict_missing_field():
    response = client.post("/predict", json={
        "device_id": "machine-001",
        "temperature_c": 82.5
        # missing vibration_g, pressure_bar, rpm
    })
    assert response.status_code == 422  # validation error
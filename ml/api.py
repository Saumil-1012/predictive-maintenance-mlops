import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

# ─────────────────────────────────────────────
# LOAD MODEL + SCALER ON STARTUP
# ─────────────────────────────────────────────
model       = joblib.load("model/model.pkl")
scaler      = joblib.load("model/scaler.pkl")
feature_cols = joblib.load("model/feature_cols.pkl")

app = FastAPI(title="Predictive Maintenance API")

# ─────────────────────────────────────────────
# REQUEST SCHEMA
# Defines exactly what JSON the API expects
# ─────────────────────────────────────────────
class SensorReading(BaseModel):
    device_id:        str
    temperature_c:    float
    vibration_g:      float
    pressure_bar:     float
    rpm:              float
    temp_rolling_avg: float = None
    vib_rolling_avg:  float = None
    temp_delta:       float = 0.0
    vib_delta:        float = 0.0

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "service": "predictive-maintenance-api"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
def predict(reading: SensorReading):
    # Fill rolling averages with raw values if not provided
    temp_rolling = reading.temp_rolling_avg or reading.temperature_c
    vib_rolling  = reading.vib_rolling_avg  or reading.vibration_g

    # Build feature array in the exact order the model was trained on
    features = np.array([[
        reading.temperature_c,
        reading.vibration_g,
        reading.pressure_bar,
        reading.rpm,
        temp_rolling,
        vib_rolling,
        reading.temp_delta,
        reading.vib_delta,
    ]])

    # Scale and predict
    features_scaled = scaler.transform(features)
    prediction      = model.predict(features_scaled)       # -1 or 1
    anomaly_score   = model.decision_function(features_scaled)  # lower = worse

    is_anomaly = bool(prediction[0] == -1)

    return {
        "device_id":     reading.device_id,
        "is_anomaly":    is_anomaly,
        "anomaly_score": round(float(anomaly_score[0]), 4),
        "alert_level":   "CRITICAL" if is_anomaly else "OK",
        "input": {
            "temperature_c": reading.temperature_c,
            "vibration_g":   reading.vibration_g,
            "pressure_bar":  reading.pressure_bar,
            "rpm":           reading.rpm,
        }
    }


@app.get("/status")
def status():
    """Returns a live simulated reading with prediction — used by the dashboard"""
    import random, time

    is_anomaly_sim = random.random() < 0.05
    temp  = round(random.uniform(120, 150) if is_anomaly_sim else random.uniform(70, 95), 2)
    vib   = round(random.uniform(2.0, 5.0) if is_anomaly_sim else random.uniform(0.1, 0.5), 3)
    press = round(random.uniform(100, 110), 2)
    rpm   = round(random.uniform(2900, 3100), 1)

    features = np.array([[temp, vib, press, rpm, temp, vib, 0.0, 0.0]])
    features_scaled = scaler.transform(features)
    prediction      = model.predict(features_scaled)
    anomaly_score   = model.decision_function(features_scaled)
    is_anomaly      = bool(prediction[0] == -1)

    return {
        "timestamp":     time.time(),
        "device_id":     "machine-001",
        "temperature_c": temp,
        "vibration_g":   vib,
        "pressure_bar":  press,
        "rpm":           rpm,
        "is_anomaly":    is_anomaly,
        "anomaly_score": round(float(anomaly_score[0]), 4),
        "alert_level":   "CRITICAL" if is_anomaly else "OK",
    }
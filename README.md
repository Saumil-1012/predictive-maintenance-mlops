# Predictive Maintenance MLOps Pipeline

An enterprise-grade predictive maintenance system that detects machine anomalies in real time using IoT sensors, machine learning, and a full MLOps pipeline on Azure.

![Dashboard](docs/dashboard-live.png)

---

## Architecture

IoT Sensors → Azure IoT Hub → Stream Analytics → Data Lake
→ Azure Databricks → Azure ML → Docker → AKS → React Dashboard
↑
CI/CD (GitHub Actions)
Drift Monitor (Evidently)


---

## Tech Stack

| Layer | Technology |
|---|---|
| IoT Simulation | Python, Azure IoT Device SDK |
| Cloud Ingestion | Azure IoT Hub, Stream Analytics |
| Data Engineering | Azure Databricks, Delta Lake, PySpark |
| ML Model | Isolation Forest (scikit-learn), MLflow |
| Inference API | FastAPI, Uvicorn |
| Containerization | Docker |
| Orchestration | Azure Kubernetes Service (AKS) |
| CI/CD | GitHub Actions |
| Drift Monitoring | SciPy KS-test, Evidently AI |
| Dashboard | React, Recharts, Vite |

---

## Project Structure

predictive-maintenance-mlops/
├── iot_simulator/
│ └── device_simulator.py # Simulates factory floor sensors
├── ml/
│ ├── train.py # Trains Isolation Forest model
│ ├── api.py # FastAPI inference microservice
│ └── score.py # Scoring script for AzureML
├── monitoring/
│ ├── drift_monitor.py # KS-test drift detection
│ └── reports/ # Auto-generated drift reports
├── dashboard/
│ └── src/
│ └── App.jsx # React real-time dashboard
├── k8s/
│ └── deployment.yaml # Kubernetes deployment manifest
├── docker/
│ └── Dockerfile # Container definition
├── tests/
│ └── test_api.py # API unit tests (pytest)
├── docs/
│ └── screenshots/
│ └── dashboard-live.png # Live dashboard screenshot
├── .github/
│ └── workflows/
│ └── deploy.yml # CI/CD pipeline
├── Dockerfile
├── requirements.txt
└── README.md


---

## Pipeline Layers

### Layer 1 — IoT Simulator
Simulates a factory machine with realistic sensor data:
- **Normal operation**: Temperature 70–95°C, Vibration 0.1–0.5g
- **Anomaly (5% chance)**: Temperature 120–150°C, Vibration 2.0–5.0g
- Sends JSON telemetry every 3 seconds
- Saves locally to `sensor_data.json` or streams to Azure IoT Hub

### Layer 2 — Cloud Ingestion *(Azure)*
- Azure IoT Hub receives MQTT/HTTPS telemetry from devices
- Stream Analytics routes data to Azure Blob Storage / Data Lake
- Partitioned by `year/month/day` for efficient querying

### Layer 3 — Data Engineering *(Azure Databricks)*
- PySpark cleans raw JSON, handles nulls
- Feature engineering: rolling averages, rate of change (delta)
- MinMax normalization
- Writes clean features to Delta Lake

### Layer 4 — ML Training
**Model**: Isolation Forest
- Unsupervised anomaly detection — no labeled data needed
- `contamination=0.05` — expects 5% anomaly rate
- Features: `temperature_c`, `vibration_g`, `pressure_bar`, `rpm`, rolling averages, deltas
- Tracked with MLflow, registered in Azure ML Model Registry

**Results on 49 readings:**
- ✅ True Positives: 2/2 anomalies caught
- ❌ False Positives: 1 (normal with 49 samples — improves with more data)
- ⚠️ False Negatives: 0 — no dangerous events missed

### Layer 5 — Deployment *(Azure Kubernetes Service)*
- Model served as FastAPI REST microservice
- Dockerized with Python 3.11-slim base image
- Deployed to AKS with 2 replicas for high availability
- Auto-scaling via Horizontal Pod Autoscaler

**API Endpoints:**
| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/predict` | POST | Run anomaly detection on sensor reading |
| `/status` | GET | Live simulated reading with prediction |

### Layer 6 — CI/CD + Drift Monitoring

**GitHub Actions pipeline** (3 jobs):
1. `test` — runs pytest suite, trains model, validates API
2. `build` — builds Docker image, verifies container starts
3. `deploy` — pushes to Azure Container Registry, updates AKS

**Drift monitoring** uses Kolmogorov-Smirnov statistical test:
- Compares production data distribution vs training data
- Flags drift when p-value < 0.05 on 2+ columns
- Triggers automatic retraining pipeline when drift detected

**Example drift detection:**

Scenario 1 — Normal: ✅ No drift (p>0.05 on all columns)
Scenario 2 — Drifted: 🚨 DRIFT DETECTED
temperature_c p=0.0000 shift=+28.76°C
vibration_g p=0.0000 shift=+0.78g
pressure_bar p=0.0000 shift=+8.87 bar
rpm p=0.0000 shift=+263 rpm


### Layer 7 — React Dashboard
Real-time dashboard polling the API every 3 seconds:
- Live metric cards (Temperature, Vibration, Pressure, RPM)
- Temperature chart with anomaly threshold line
- Vibration chart with threshold line
- Alert log showing anomaly timestamps, values, and scores
- Live/Disconnected status indicator

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop

### 1. Clone and set up Python environment
```bash
git clone https://github.com/Saumil-1012/predictive-maintenance-mlops.git
cd predictive-maintenance-mlops

python3.11 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. Generate sensor data
```bash
python iot_simulator/device_simulator.py
# Let it run for 1 minute, then Ctrl+C
```

### 3. Train the model
```bash
python ml/train.py
```

### 4. Start the API
```bash
uvicorn ml.api:app --reload --port 8000
```

### 5. Start the dashboard
```bash
cd dashboard
npm install
npm run dev
# Open http://localhost:5173
```

### 6. Run drift monitoring
```bash
python monitoring/drift_monitor.py
```

### 7. Run tests
```bash
pytest tests/ -v
```

### 8. Build Docker image
```bash
docker build -t pred-maint:latest .
docker run -p 8000:8000 pred-maint:latest
```

---

## API Usage

**Health check:**
```bash
curl http://localhost:8000/health
```

**Predict normal reading:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "machine-001",
    "temperature_c": 82.5,
    "vibration_g": 0.3,
    "pressure_bar": 104.2,
    "rpm": 2980.0
  }'
```

**Response:**
```json
{
  "device_id": "machine-001",
  "is_anomaly": false,
  "anomaly_score": 0.2442,
  "alert_level": "OK",
  "input": {
    "temperature_c": 82.5,
    "vibration_g": 0.3,
    "pressure_bar": 104.2,
    "rpm": 2980.0
  }
}
```

**Predict anomaly:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "machine-001",
    "temperature_c": 142.0,
    "vibration_g": 3.8,
    "pressure_bar": 104.2,
    "rpm": 2980.0
  }'
```

**Response:**
```json
{
  "device_id": "machine-001",
  "is_anomaly": true,
  "anomaly_score": -0.0019,
  "alert_level": "CRITICAL"
}
```

---

## CI/CD Pipeline

Every push to `main` triggers:

Push to main
│
▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ test │────▶│ build │────▶│ deploy │
│ 28s │ │ 1m13s │ │ 6s │
└─────────┘ └─────────┘ └─────────┘
pytest docker kubectl
train model build + set image
API tests verify health


---

## Azure Deployment *(activates when account is ready)*

```bash
# Set up Azure resources
az group create --name pred-maint-rg --location eastus
az iot hub create --name pred-maint-hub --resource-group pred-maint-rg --sku F1
az acr create --name predmaintacr --resource-group pred-maint-rg --sku Basic
az aks create --name pred-maint-aks --resource-group pred-maint-rg --node-count 2

# Deploy to AKS
kubectl apply -f k8s/deployment.yaml
```

---

## Status

| Layer | Local | Azure |
|---|---|---|
| IoT Simulator | ✅ Complete | ⏳ Pending |
| Cloud Ingestion | — | ⏳ Pending |
| Data Engineering | — | ⏳ Pending |
| ML Model + API | ✅ Complete | ⏳ Pending |
| Kubernetes | ✅ Docker ready | ⏳ Pending |
| CI/CD Pipeline | ✅ Complete | ✅ GitHub Actions live |
| Drift Monitoring | ✅ Complete | ⏳ Pending |
| React Dashboard | ✅ Complete | ⏳ Pending |

---

## Author
Saumil — TU Munich  
Advanced ML Project — Azure MLOps Predictive Maintenance
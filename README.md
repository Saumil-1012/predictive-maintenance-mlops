# Predictive Maintenance MLOps Pipeline

An enterprise-grade predictive maintenance system built on Azure, Kubernetes, and Python.

## Architecture
IoT Sensors → Azure IoT Hub → Stream Analytics → Data Lake → Databricks → Azure ML → AKS → React Dashboard

## Live Dashboard
![Dashboard](docs/screenshots/dashboard-live.png)

## Stack
- **IoT Layer**: Python simulator with Azure IoT Device SDK
- **ML Model**: Isolation Forest (scikit-learn) for anomaly detection
- **API**: FastAPI served with Uvicorn
- **Deployment**: Docker + Azure Kubernetes Service
- **CI/CD**: GitHub Actions + Azure DevOps
- **Monitoring**: Evidently AI for data drift detection
- **Dashboard**: React + Recharts

## Layers
| Layer | Technology | Status |
|-------|-----------|--------|
| IoT Simulator | Python, Azure IoT SDK | ✅ Complete |
| Cloud Ingestion | Azure IoT Hub, Stream Analytics | ✅ Complete |
| Data Engineering | Azure Databricks, Delta Lake | ✅ Complete |
| ML Training | Azure ML, Isolation Forest, MLflow | ✅ Complete |
| Deployment | Docker, AKS | ✅ Complete |
| CI/CD + Drift | Azure DevOps, Evidently AI | ✅ Complete |
| Dashboard | React, Recharts | ✅ Complete |

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python iot_simulator/device_simulator.py  # start simulator
uvicorn ml.api:app --reload --port 8000   # start API
cd dashboard && npm run dev               # start dashboard
```
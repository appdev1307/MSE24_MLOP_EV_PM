
---

# 🚗 Predictive Maintenance MLOps – Example Project

This repository contains a **fully runnable local MLOps prototype** for **EV Predictive Maintenance**, built using **MLflow Model Registry**, **Docker**, and **FastAPI**.

It demonstrates an **end-to-end MLOps lifecycle**:

* Model training
* Model versioning & promotion
* Registry-based inference
* Monitoring & alerting

---

## 🧠 Architecture & Flow

```text
┌──────────────┐
│   Trainer    │
│ (Batch Job)  │
└──────┬───────┘
       │ Train + Evaluate + Register
       ▼
┌──────────────────────────┐
│ MLflow Tracking Server   │
│ + Model Registry         │
│                          │
│ ev-anomaly               │
│ ev-classifier            │
│ ev-rul                   │
│  ├─ v1 (Staging)         │
│  └─ v2 (Production)      │
└─────────┬────────────────┘
          │ Load by name + stage
          ▼
┌──────────────────────────┐
│ FastAPI Inference API    │
│                          │
│ models:/ev-rul/Prod      │
│ models:/ev-classifier    │
└──────────────────────────┘
```

✔ No hardcoded model paths
✔ Safe rollback via MLflow stages
✔ Production-ready inference loading

---

## 📁 Project Structure

```text
project/
├── models/              # Model artifacts (.joblib)
├── src/                 # Training & feature engineering
├── monitoring/          # Prometheus & alert rules
├── alert_service/       # Alerting microservice
├── scripts/             # Setup utilities
└── docker-compose.yml   # Local MLOps stack
```

---

## 🚀 Quick Start (Local Development)

### 1️⃣ Prerequisites

* Docker
* Docker Compose
* Colima (macOS)

---

### 2️⃣ Start the MLOps Stack

```bash
colima start
docker compose down -v
docker compose pull
docker compose up --build -d
docker compose ps
```

---

### 3️⃣ Service Endpoints

| Service       | URL                                            |
| ------------- | ---------------------------------------------- |
| MLflow        | [http://localhost:5000](http://localhost:5000) |
| MinIO Console | [http://localhost:9001](http://localhost:9001) |
| Prometheus    | [http://localhost:9090](http://localhost:9090) |
| Grafana       | [http://localhost:3000](http://localhost:3000) |

**MinIO credentials**

```text
User: minioadmin
Pass: minioadmin
```

---

## 🪣 MinIO & Kafka Setup (Local)

### Manual Setup

```bash
docker exec -it minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec -it minio mc mb local/mlflow-artifacts
docker exec -it minio mc ls local
```

### Scripted Setup

```bash
chmod +x scripts/setup_minio_kafka.sh
./scripts/setup_minio_kafka.sh
```

---

## 🧪 Testing & Validation

### 🔔 Alert Testing

```bash
python test_alerts.py
```

---

### 📖 API Documentation

Open in browser:

```text
http://localhost:8000/docs
```

---

## 🔮 Prediction API Examples

### Example 1 – Full Telemetry Payload

```bash
curl -X POST "http://localhost:8000/predict" \
-H "Content-Type: application/json" \
-d '{
  "data": {
    "SoC": 0.10,
    "SoH": 0.50,
    "Battery_Voltage": 200,
    "Battery_Current": 350,
    "Battery_Temperature": 95,
    "Charge_Cycles": 2000,
    "Motor_Temperature": 150,
    "Motor_Vibration": 0.6,
    "Power_Consumption": 50,
    "Brake_Pressure": 10,
    "Tire_Pressure": 10,
    "Ambient_Temperature": 80,
    "Ambient_Humidity": 0.95,
    "Load_Weight": 3000,
    "Driving_Speed": 200,
    "Distance_Traveled": 700000,
    "Idle_Time": 60,
    "Route_Roughness": 0.9,
    "Component_Health_Score": 0.1,
    "Failure_Probability": 0.95,
    "TTF": 50
  }
}'
```

---

### Example 2 – Simplified Payload

```bash
curl -X POST "http://localhost:8000/predict" \
-H "Content-Type: application/json" \
-d '{
  "data": {
    "State_of_Charge": 80,
    "Battery_Temperature": 30,
    "Motor_Temperature": 60,
    "Ambient_Temperature": 25,
    "Odometer": 12000,
    "Speed": 60,
    "Current": 120,
    "Voltage": 350,
    "Health_Index": 85,
    "Vehicle_ID": "EV-1"
  }
}'
```

---

## ✅ What This Project Demonstrates

* MLflow **Model Registry** (Staging → Production)
* Registry-based inference loading (`models:/name/Production`)
* Dockerized local MLOps stack
* Monitoring with Prometheus & Grafana
* Alert-driven predictive maintenance

---
```md
# Predictive Maintenance MLOps – Example Project

A runnable **local MLOps prototype** for EV Predictive Maintenance using MLflow, FastAPI, Kafka, Prometheus, and Grafana.

---

## 🔁 System Flow

```text
┌──────────────┐
│   Trainer    │
│ (batch job)  │
└──────┬───────┘
       │ register + evaluate
       ▼
┌──────────────────────────────┐
│ MLflow Tracking + Registry   │
│                              │
│   ev-anomaly                 │
│   ev-classifier              │
│   ev-rul                     │
│   ├─ v1 (Staging)            │
│   └─ v2 (Production)         │
└─────────┬────────────────────┘
          │ load by name + stage
          ▼
┌──────────────────────────────┐
│   FastAPI Inference Service  │
│                              │
│   models:/ev-rul/Production  │
│   models:/ev-classifier/Prod │
└──────────────────────────────┘
```

---

## 📁 Project Layout

```text
project/
├── models/              # Local model artifacts (.joblib)
├── src/                 # Training scripts
├── monitoring/          # Prometheus config
├── alert_service/       # Alert service
├── scripts/             # Setup scripts
└── docker-compose.yml
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites

- Docker
- Docker Compose
- Colima (recommended for macOS)

### 2. Start the stack

```bash
colima start
docker compose down -v
docker compose pull
docker compose up --build -d
docker compose ps
```

### 3. Access services

- **MLflow** → [http://localhost:5000](http://localhost:5000)
- **MinIO Console** → [http://localhost:9001](http://localhost:9001)  
  - User: `minioadmin`  
  - Password: `minioadmin`
- **Prometheus** → [http://localhost:9090](http://localhost:9090)
- **Grafana** → [http://localhost:3000](http://localhost:3000)

### 4. Create MinIO bucket (required for MLflow)

```bash
docker exec -it minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec -it minio mc mb local/mlflow-artifacts
docker exec -it minio mc ls local
```

Or use the helper script:

```bash
chmod +x scripts/setup_minio_kafka.sh
./scripts/setup_minio_kafka.sh
```

---

## 🧪 Testing

### FastAPI Swagger UI

[http://localhost:8000/docs](http://localhost:8000/docs)

### Sample prediction request

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
      "Ambient_Temperature": 80,
      "Distance_Traveled": 700000
    }
  }'
```

---

## ✅ Key Design Highlights

- MLflow Model Registry with Staging and Production stages
- FastAPI loads models directly via `models:/<name>/Production`
- Kafka-based alerting system
- Prometheus metrics collection + Grafana dashboards for monitoring
- MinIO as S3-compatible artifact storage for MLflow
```

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
docker compose up trainer
docker compose ps
```

### 3. Create MinIO bucket (required for MLflow)

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

### 4. Run docker to train the models
```bash
docker compose build --no-cache trainer
docker compose up trainer
```

### 5. Access services
- **MLflow** → [http://localhost:5000](http://localhost:5000)
- **MinIO Console** → [http://localhost:9001](http://localhost:9001)  
  - User: `minioadmin`  
  - Password: `minioadmin`
- **Prometheus** → [http://localhost:9090](http://localhost:9090)
- **Grafana** → [http://localhost:3000](http://localhost:3000)
- **Fast API Server** → [http://localhost:8000/docs] (http://localhost:8000/docs)

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

```bash
python test_inference_api.py
```

```bash
python test_alerts.py
```

---

## ✅ Key Design Highlights (Level-2 MLOps maturity)
- Dockerized training & inference
- FastAPI inference service
- MLflow tracking + artifacts
- Kafka event streaming
- Prometheus + Grafana monitoring
- Alertmanager
- Synthetic test cases
- Offline training pipeline
- Feature-rich EV dataset


## Limitation
- Model Registry Lifecycle Control (CRITICAL): Train → Register → Validate → Promote → Serve → Rollback
- Inference Model Version Pinning
  classifier: Production v3
  rul: Production v2
  anomaly: Production v5
- Data & Prediction Drift Detection
  Feature drift
  Prediction drift
  Label drift (offline)
- Ground Truth Feedback Loop: Prediction → Real failure → Label → Retraining
- Automated Retraining Trigger: Drift → Kafka event → Training job → Validation → Registry
- Pre-deployment Model Validation (Gatekeeper)
- Explainability (XAI)
- Security & Access Control
- CI/CD for ML (Not Just Docker): Git push → Train → Validate → Register → Deploy
- Reproducibility & Lineage


```

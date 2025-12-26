# 🐳 Docker Workflow Guide - Predictive Maintenance

Hướng dẫn thực hiện workflow hoàn chỉnh sử dụng Docker.

## 🎯 Tổng Quan

Với Docker, bạn có thể thực hiện toàn bộ workflow mà **không cần cài đặt dependencies trên máy local**. Tất cả chạy trong containers.

## 🔄 Workflow với Docker

```
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: Data (Kaggle)                                    │
│  ✅ Local: Download dataset                                 │
│  ✅ Docker: Copy vào container                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2-4: Processing → Preparation → Training             │
│  ✅ Docker: Chạy trong trainer container                    │
│  ✅ MLflow: Track experiments (container)                   │
│  ✅ MinIO: Store artifacts (container)                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 5-6: Experiments → Metrics                          │
│  ✅ MLflow UI: Xem trên browser (http://localhost:6969)    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 7-8: Select Best → Register                          │
│  ✅ MLflow UI: Manual selection và registration             │
│  ✅ Hoặc: Python script trong container                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 9: Production                                        │
│  ✅ Docker: FastAPI inference service (container)            │
│  ✅ Monitoring: Prometheus + Grafana (containers)           │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Chi Tiết Workflow

### Stage 1: Download Dataset (Local)

**Tại sao local?** Dataset cần download từ Kaggle, sau đó copy vào Docker volume.

```powershell
# Option 1: Download local (nếu có Kaggle API)
.\scripts\download_dataset.ps1

# Option 2: Download manual từ Kaggle
# https://www.kaggle.com/datasets/datasetengineer/eviot-predictivemaint-dataset/data
# Đặt vào: src/data/EV_Predictive_Maintenance_Dataset_15min.csv
```

**Sau khi download**, dataset sẽ được mount vào container qua volume trong `docker-compose.yml`.

### Stage 2-4: Processing → Training (Docker)

**Tất cả chạy trong Docker container:**

```bash
# 1. Start infrastructure services
docker compose up -d minio mlflow

# 2. Setup MinIO bucket (nếu chưa có)
docker compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker compose exec minio mc mb local/mlflow-artifacts || true

# 3. Build và train models
docker compose build trainer
docker compose up trainer
```

**Hoặc chạy từng script riêng:**

```bash
# Processing
docker compose run --rm trainer python src/preprocessing.py

# Train anomaly model
docker compose run --rm trainer python src/anomaly.py

# Train classifier
docker compose run --rm trainer python src/classifier.py

# Train RUL model
docker compose run --rm trainer python src/rul.py
```

**Kết quả:**

- Models được lưu trong `models/` (local, qua volume mount)
- Experiments được log vào MLflow (container)
- Artifacts được lưu vào MinIO (container)

### Stage 5-6: View Experiments & Metrics (Browser)

**Xem trên MLflow UI:**

```
http://localhost:6969
```

**Hoặc query qua Python trong container:**

```bash
# Chạy Python script trong container
docker compose run --rm trainer python -c "
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient('http://mlflow:6969')
experiment = client.get_experiment_by_name('predictive-maintenance')
runs = client.search_runs([experiment.experiment_id], order_by=['metrics.f1_score DESC'])

for run in runs[:5]:
    print(f'Run: {run.info.run_name}')
    print(f'F1: {run.data.metrics.get(\"f1_score\", 0):.4f}')
    print('---')
"
```

### Stage 7-8: Select Best & Register (MLflow UI hoặc Script)

**Option 1: Qua MLflow UI (Khuyến nghị)**

1. Mở http://localhost:6969
2. Vào experiment "predictive-maintenance"
3. So sánh các runs
4. Click vào run tốt nhất
5. Click "Register Model"
6. Tạo model name mới hoặc add vào existing
7. Transition stage: None → Staging → Production

**Option 2: Qua Python Script trong Container**

```bash
# Tạo script register_model.py
docker compose run --rm trainer python scripts/register_best_model.py
```

### Stage 9: Production Deployment (Docker)

**Deploy inference service:**

```bash
# Build và start inference service
docker compose build fastapi-inference
docker compose up -d fastapi-inference

# Kiểm tra
curl http://localhost:8000/docs
```

**Monitoring:**

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## 🚀 Complete Docker Workflow Script

Tạo file `scripts/docker_workflow.sh` hoặc `.ps1`:

```bash
#!/bin/bash
# Complete workflow với Docker

echo "🚀 Starting Docker Workflow..."

# 1. Start services
echo "📦 Starting infrastructure..."
docker compose up -d minio mlflow

# 2. Setup MinIO
echo "🔧 Setting up MinIO..."
sleep 5
docker compose exec -T minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker compose exec -T minio mc mb local/mlflow-artifacts || true

# 3. Train models
echo "🚂 Training models..."
docker compose build trainer
docker compose up trainer

# 4. Show results
echo "✅ Training completed!"
echo "📊 View experiments at: http://localhost:6969"
echo "📦 Models saved in: ./models/"
```

## 📊 So Sánh: Docker vs Local

| Stage                   | Local     | Docker    | Khuyến nghị               |
| ----------------------- | --------- | --------- | ------------------------- |
| **1. Download Dataset** | ✅        | ❌        | Local (cần Kaggle API)    |
| **2. Processing**       | ✅        | ✅        | Docker (isolated)         |
| **3. Preparation**      | ✅        | ✅        | Docker (isolated)         |
| **4. Training**         | ✅        | ✅        | Docker (isolated)         |
| **5. Experiments**      | ✅        | ✅        | Docker (MLflow container) |
| **6. Metrics**          | Browser   | Browser   | Browser (MLflow UI)       |
| **7. Select Best**      | MLflow UI | MLflow UI | MLflow UI                 |
| **8. Register**         | MLflow UI | MLflow UI | MLflow UI                 |
| **9. Production**       | ✅        | ✅        | Docker (production-ready) |

## 🎯 Best Practice

### ✅ Nên dùng Docker cho:

1. **Training** - Đảm bảo môi trường nhất quán
2. **Processing** - Isolated environment
3. **Production** - Containerized deployment
4. **Services** - MLflow, MinIO, Prometheus, Grafana

### ✅ Nên dùng Local cho:

1. **Download Dataset** - Cần Kaggle API credentials
2. **Development** - Test code nhanh
3. **Viewing Results** - MLflow UI qua browser

## 🔧 Troubleshooting

### Dataset không tìm thấy trong container

```bash
# Kiểm tra volume mount
docker compose config | grep volumes

# Copy dataset vào container
docker compose cp src/data/EV_Predictive_Maintenance_Dataset_15min.csv trainer:/workspace/src/data/
```

### MLflow không kết nối được

```bash
# Kiểm tra MLflow service
docker compose ps mlflow

# Xem logs
docker compose logs mlflow
```

### Models không được lưu

```bash
# Kiểm tra volume mount
docker compose exec trainer ls -la /workspace/models/

# Kiểm tra local
ls -la models/
```

## 📝 Quick Commands

```bash
# Start all services
docker compose up -d

# Train models
docker compose up trainer

# View logs
docker compose logs -f trainer

# Stop all
docker compose down

# Rebuild và restart
docker compose build --no-cache trainer
docker compose up trainer
```

## 🔗 Related

- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Chi tiết workflow
- [QUICK_WORKFLOW.md](QUICK_WORKFLOW.md) - Quick reference
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Hướng dẫn sử dụng

---

**Kết luận**: Với Docker, bạn chỉ cần download dataset local, còn lại tất cả chạy trong containers. Điều này đảm bảo môi trường nhất quán và dễ deploy.

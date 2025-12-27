# ⚡ Quick Workflow Reference

Quick reference cho workflow: **Data → Processing → Training → Registry → Production**

## 🎯 Đề Tài

**Predictive Maintenance on Vehicle Telemetry Data**

**Dataset**: [Kaggle - EVIoT Predictive Maintenance Dataset](https://www.kaggle.com/datasets/datasetengineer/eviot-predictivemaint-dataset/data)

## 🔄 Workflow Steps

```
1. Data (Kaggle)
   ↓
2. Processing Data
   ↓
3. Preparation
   ↓
4. Training
   ↓
5. Run Experiments (Models)
   ↓
6. Metrics/Params
   ↓
7. Select Best Model
   ↓
8. Register Version 1
   ↓
9. Production
```

## 🚀 Quick Commands

### Option 1: Docker Workflow (Khuyến nghị)

```powershell
# Complete workflow với Docker
.\scripts\docker_workflow.ps1

# Hoặc từng bước:
# 1. Download dataset (local)
.\scripts\download_dataset.ps1

# 2. Start services & train (Docker)
docker compose up -d minio mlflow
docker compose build trainer
docker compose up trainer

# 3. View experiments
# Mở http://localhost:6969

# 4. Register best model (MLflow UI)
# http://localhost:6969 → Register Model

# 5. Deploy production (Docker)
docker compose up -d fastapi-inference
```

### Option 2: Local Workflow

```bash
# 1. Download Dataset
.\scripts\download_dataset.ps1

# 2. Process & Prepare Data
python src/preprocessing.py

# 3. Train Models
python src/train_wrapper.py

# 4. View Experiments
# http://localhost:6969 (MLflow phải chạy)

# 5. Register Best Model
# Via MLflow UI hoặc script
python scripts/complete_workflow.py

# 6. Deploy Production
docker compose up -d fastapi-inference
```

## 📊 Components Mapping

| Stage          | Component           | Technology             |
| -------------- | ------------------- | ---------------------- |
| 1. Data        | Dataset             | Kaggle                 |
| 2. Processing  | Data Processing     | Python (pandas, numpy) |
| 3. Preparation | Data Prep           | Python (scikit-learn)  |
| 4. Training    | Model Training      | XGBoost + MLflow       |
| 5. Experiments | Experiment Tracking | MLflow                 |
| 6. Metrics     | Analysis            | MLflow UI              |
| 7. Selection   | Model Selection     | MLflow                 |
| 8. Registry    | Model Registry      | MLflow + MinIO         |
| 9. Production  | API Deployment      | FastAPI + Docker       |

## 🐳 Docker vs Local

**Khuyến nghị**: Sử dụng **Docker workflow** để đảm bảo môi trường nhất quán.

| Stage               | Docker | Local |
| ------------------- | ------ | ----- |
| Download Dataset    | ❌     | ✅    |
| Processing/Training | ✅     | ✅    |
| Experiments         | ✅     | ✅    |
| Production          | ✅     | ✅    |

Xem [DOCKER_WORKFLOW.md](DOCKER_WORKFLOW.md) để biết chi tiết về Docker workflow.

## 🔗 Full Guide

- [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) - Chi tiết đầy đủ workflow
- [DOCKER_WORKFLOW.md](DOCKER_WORKFLOW.md) - Docker workflow guide

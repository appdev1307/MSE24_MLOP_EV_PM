# 🔄 Workflow Guide - Predictive Maintenance on Vehicle Telemetry Data

Hướng dẫn chi tiết về workflow xử lý từ data đến production model.

## 📋 Tổng Quan

**Đề tài**: Predictive Maintenance on Vehicle Telemetry Data

**Dataset**: [EVIoT Predictive Maintenance Dataset](https://www.kaggle.com/datasets/datasetengineer/eviot-predictivemaint-dataset/data)

**Workflow**:

```
Data (Kaggle)
  → Processing Data
  → Preparation
  → Training
  → Run Experiments (Models)
  → Metrics/Params
  → Select Best Model
  → Register Version 1
  → Production
```

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                         │
│                         (Kafka)                                 │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DATA PROCESSING LAYER                          │
│                      (Python)                                   │
│  - Preprocessing                                                │
│  - Feature Engineering                                          │
│  - Data Validation                                              │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DATA PREPARATION LAYER                         │
│                      (Python)                                   │
│  - Train/Test Split                                             │
│  - Data Normalization                                            │
│  - Feature Selection                                            │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MODEL TRAINING LAYER                           │
│              (XGBoost + MLflow)                                 │
│  - Train Multiple Models                                        │
│  - Hyperparameter Tuning                                        │
│  - Cross Validation                                             │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EXPERIMENT TRACKING                            │
│                      (MLflow)                                   │
│  - Log Metrics                                                   │
│  - Log Parameters                                               │
│  - Log Artifacts                                                 │
│  - Compare Experiments                                          │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MODEL SELECTION                                │
│                      (MLflow)                                   │
│  - Compare Metrics                                              │
│  - Select Best Model                                            │
│  - Register Version 1                                           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MODEL REGISTRY                                 │
│                      (MLflow)                                   │
│  - Version Control                                               │
│  - Stage Management (Staging → Production)                      │
│  - Artifact Storage (MinIO)                                     │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PRODUCTION DEPLOYMENT                          │
│                    (FastAPI)                                    │
│  - Load Model from Registry                                     │
│  - Serve Inference API                                          │
│  - Monitoring (Prometheus + Grafana)                            │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Chi Tiết Workflow

### Stage 1: Data Ingestion (Kafka)

**Mục đích**: Nhận dữ liệu telemetry từ vehicles real-time

**Components**:

- **Kafka**: Event streaming platform
- **Zookeeper**: Kafka coordination

**Workflow**:

```python
# Producer: Vehicle sensors → Kafka
producer = KafkaProducer(bootstrap_servers='kafka:9092')
producer.send('vehicle-telemetry', json.dumps(telemetry_data))
```

**Setup**:

```bash
# Start Kafka services
docker compose up -d zookeeper kafka
```

**Output**: Raw telemetry data stream trong Kafka topics

---

### Stage 2: Data Processing (Python)

**Mục đích**: Xử lý và làm sạch dữ liệu

**Components**:

- **Python**: pandas, numpy
- **Scripts**: `src/preprocessing.py`

**Workflow**:

```python
# 1. Load data từ Kafka hoặc CSV
df = pd.read_csv("src/data/EV_Predictive_Maintenance_Dataset_15min.csv")

# 2. Data cleaning
df = df.dropna()
df = df.drop_duplicates()

# 3. Feature engineering
df['Battery_Health_Ratio'] = df['SoH'] / df['SoC']
df['Temperature_Diff'] = df['Battery_Temperature'] - df['Ambient_Temperature']

# 4. Data validation
assert df['SoC'].between(0, 1).all()
assert df['SoH'].between(0, 1).all()
```

**Script**: `src/preprocessing.py`

**Output**: Cleaned và processed dataset

---

### Stage 3: Data Preparation (Python)

**Mục đích**: Chuẩn bị dữ liệu cho training

**Components**:

- **Python**: scikit-learn
- **Scripts**: `src/anomaly.py`, `src/classifier.py`, `src/rul.py`

**Workflow**:

```python
# 1. Feature selection
features = [
    'SoC', 'SoH', 'Battery_Voltage', 'Battery_Current',
    'Battery_Temperature', 'Motor_Temperature', ...
]

# 2. Train/Test split
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 3. Data normalization
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 4. Save preprocessing artifacts
joblib.dump(scaler, 'models/scaler.joblib')
joblib.dump(features, 'models/features.joblib')
```

**Output**: Prepared training data và preprocessing artifacts

---

### Stage 4: Training (XGBoost + MLflow)

**Mục đích**: Train multiple models và track experiments

**Components**:

- **XGBoost**: Gradient boosting models
- **LightGBM**: RUL prediction
- **Isolation Forest**: Anomaly detection
- **MLflow**: Experiment tracking

**Workflow**:

```python
import mlflow
import mlflow.xgboost
from xgboost import XGBClassifier

# 1. Start MLflow experiment
mlflow.set_experiment("predictive-maintenance")
mlflow.set_tracking_uri("http://mlflow:6969")

with mlflow.start_run(run_name="classifier-v1"):
    # 2. Train model
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1
    )
    model.fit(X_train_scaled, y_train)

    # 3. Evaluate
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')

    # 4. Log to MLflow
    mlflow.log_params({
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1
    })

    mlflow.log_metrics({
        "accuracy": accuracy,
        "f1_score": f1
    })

    # 5. Log model
    mlflow.xgboost.log_model(model, "model")

    # 6. Log artifacts
    mlflow.log_artifacts("models/", "artifacts")
```

**Scripts**:

- `src/anomaly.py` - Train anomaly detection model
- `src/classifier.py` - Train fault classifier
- `src/rul.py` - Train RUL predictor
- `src/train_wrapper.py` - Orchestrate all training

**Run Training**:

```bash
# Local
python src/train_wrapper.py

# Docker
docker compose up trainer
```

**Output**: Trained models và MLflow experiments

---

### Stage 5: Run Experiments (Models)

**Mục đích**: Chạy nhiều experiments với different hyperparameters

**Components**:

- **MLflow**: Track all experiments
- **Python**: Hyperparameter tuning

**Workflow**:

```python
# Experiment 1: Baseline
with mlflow.start_run(run_name="baseline"):
    model = XGBClassifier(n_estimators=50, max_depth=3)
    # ... train and log

# Experiment 2: Tuned hyperparameters
with mlflow.start_run(run_name="tuned-v1"):
    model = XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.05)
    # ... train and log

# Experiment 3: Different algorithm
with mlflow.start_run(run_name="lightgbm-v1"):
    from lightgbm import LGBMClassifier
    model = LGBMClassifier(n_estimators=150)
    # ... train and log
```

**View Experiments**:

```
http://localhost:6969
```

**Output**: Multiple experiment runs với different metrics

---

### Stage 6: Metrics/Params Analysis

**Mục đích**: Phân tích và so sánh experiments

**Components**:

- **MLflow UI**: Visualize experiments
- **Python**: Compare metrics

**Workflow**:

```python
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()

# 1. Get all runs
experiment = client.get_experiment_by_name("predictive-maintenance")
runs = client.search_runs(experiment.experiment_id)

# 2. Compare metrics
for run in runs:
    print(f"Run: {run.info.run_name}")
    print(f"Accuracy: {run.data.metrics.get('accuracy', 'N/A')}")
    print(f"F1 Score: {run.data.metrics.get('f1_score', 'N/A')}")
    print("---")

# 3. Find best run
best_run = max(runs, key=lambda r: r.data.metrics.get('f1_score', 0))
print(f"Best run: {best_run.info.run_name}")
```

**MLflow UI**:

1. Mở http://localhost:6969
2. Vào experiment "predictive-maintenance"
3. So sánh metrics của các runs
4. Xem parameters và artifacts

**Output**: Best model được xác định

---

### Stage 7: Select Best Model

**Mục đích**: Chọn model tốt nhất dựa trên metrics

**Components**:

- **MLflow**: Model comparison
- **Python**: Selection logic

**Workflow**:

```python
# Criteria for best model:
# 1. Highest F1 score
# 2. Good accuracy (> 0.85)
# 3. Low overfitting (train/test gap < 0.1)

best_run_id = "abc123def456"  # From Stage 6
best_model_uri = f"runs:/{best_run_id}/model"
```

**Manual Selection**:

1. Vào MLflow UI
2. So sánh các runs
3. Chọn run có metrics tốt nhất
4. Copy run_id

**Output**: Best model URI

---

### Stage 8: Register Version 1

**Mục đích**: Đăng ký model vào Model Registry

**Components**:

- **MLflow Model Registry**: Version control
- **MinIO**: Artifact storage

**Workflow**:

```python
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()

# 1. Register model
model_name = "ev-classifier"
model_version = client.create_model_version(
    name=model_name,
    source=f"runs:/{best_run_id}/model",
    run_id=best_run_id
)

print(f"Registered: {model_name} v{model_version.version}")

# 2. Add description
client.update_model_version(
    name=model_name,
    version=model_version.version,
    description="Best model from experiment v1 - F1: 0.92, Accuracy: 0.89"
)

# 3. Transition to Staging
client.transition_model_version_stage(
    name=model_name,
    version=model_version.version,
    stage="Staging"
)
```

**Via MLflow UI**:

1. Vào run details
2. Click "Register Model"
3. Tạo model name mới hoặc add vào existing model
4. Model được register với version 1
5. Transition stage: None → Staging → Production

**Output**: Model registered với version 1 trong Staging

---

### Stage 9: Production Deployment

**Mục đích**: Deploy model vào production

**Components**:

- **FastAPI**: Inference API
- **MLflow**: Load model from registry
- **Docker**: Containerization
- **Prometheus + Grafana**: Monitoring

**Workflow**:

```python
# inference_server.py
import mlflow
from mlflow.tracking import MlflowClient

# 1. Load model from registry
client = MlflowClient()
model_name = "ev-classifier"
model_version = client.get_latest_versions(
    model_name,
    stages=["Production"]
)[0]

model_uri = f"models:/{model_name}/Production"
model = mlflow.pyfunc.load_model(model_uri)

# 2. Serve with FastAPI
from fastapi import FastAPI
app = FastAPI()

@app.post("/predict")
def predict(data: dict):
    prediction = model.predict([data])
    return {"prediction": prediction[0]}
```

**Deploy**:

```bash
# Build và start inference service
docker compose build fastapi-inference
docker compose up -d fastapi-inference
```

**Monitor**:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

**Output**: Production API serving predictions

---

## 📊 Complete Workflow Diagram

```
┌─────────────┐
│   Kaggle    │
│   Dataset   │
└──────┬──────┘
       │ Download
       ▼
┌─────────────────┐
│  Data Processing│  ← Python (pandas, numpy)
│  - Cleaning     │
│  - Validation   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Preparation    │  ← Python (scikit-learn)
│  - Split        │
│  - Normalize    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│    Training     │  ← XGBoost + MLflow
│  - Train models │
│  - Experiments  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Experiments   │  ← MLflow Tracking
│  - Log metrics  │
│  - Log params   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Select Best    │  ← MLflow UI
│  - Compare      │
│  - Choose       │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Register v1    │  ← MLflow Registry
│  - Version      │
│  - Stage        │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   Production    │  ← FastAPI + Docker
│  - Deploy       │
│  - Monitor      │  ← Prometheus + Grafana
└─────────────────┘
```

## 🚀 Quick Start Commands

### 1. Download Dataset

```bash
# Script
bash scripts/download_dataset.sh
# hoặc
.\scripts\download_dataset.ps1
```

### 2. Process Data

```bash
python src/preprocessing.py
```

### 3. Train Models

```bash
# Local
python src/train_wrapper.py

# Docker
docker compose up trainer
```

### 4. View Experiments

```
http://localhost:6969
```

### 5. Register Best Model

```python
# Via Python script hoặc MLflow UI
```

### 6. Deploy to Production

```bash
docker compose up -d fastapi-inference
```

## 📝 Best Practices

1. **Version Control**: Luôn commit code trước khi train
2. **Experiment Naming**: Dùng naming convention rõ ràng
3. **Metrics Tracking**: Log đầy đủ metrics quan trọng
4. **Model Registry**: Luôn register models trước khi deploy
5. **Staging First**: Test model trong Staging trước khi Production
6. **Monitoring**: Setup monitoring ngay sau khi deploy

## 🔗 Related Documentation

- [PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md) - Chi tiết về dự án
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Hướng dẫn sử dụng
- [TECH_STACK.md](TECH_STACK.md) - Tech stack chi tiết

---

**Lưu ý**: Workflow này có thể được automate hoàn toàn qua GitHub Actions workflows.

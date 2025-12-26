## EV Predictive Maintenance – Hướng dẫn chạy nhanh

**Đề tài**: Predictive Maintenance on Vehicle Telemetry Data  
**Mục tiêu**: Xây dựng prototype MLOps cho bảo trì dự đoán xe điện với:

- **Data**: Dataset Kaggle (telemetry EV)
- **Training**: Python, XGBoost, LightGBM, MLflow
- **Inference**: FastAPI
- **Streaming & Alert**: Kafka + Alert Service + Prometheus + Grafana

---

## 🔁 Flow tổng quan

## Predictice Maintenaince Flow

```text
  ┌──────────────────────────────────────────────┐
  │              EV / Fleet Clients              │
  │  - Vehicle ECU                               │
  │  - Edge gateway                              │
  │  - Simulator / Test tool                     │
  └───────────────────────┬──────────────────────┘
                          │  REST / JSON
                          ▼
  ┌──────────────────────────────────────────────┐
  │        Inference API Layer (FastAPI)         │
  │  - /predict                                  │
  │  - Input validation (Pydantic)               │
  │  - Request tracing & timing                  │
  └───────────────────────┬──────────────────────┘
                          │
                          ▼
  ┌──────────────────────────────────────────────┐
  │          Feature Assembly Layer              │
  │  - Align input with model feature contracts  │
  │  - Default missing values                    │
  │  - Numeric normalization                     │
  └───────────────────────┬──────────────────────┘
                          │
                          ▼
  ┌──────────────────────────────────────────────┐
  │     Stage 1: Anomaly Detection               │
  │  - Isolation Forest                          │
  │  - Scaler reuse                              │
  │  - Rule-based override (Battery aging)       │
  └───────────────────────┬──────────────────────┘
                          │
             Normal ──────┴──────► Early Exit
                          │
                          ▼
  ┌──────────────────────────────────────────────┐
  │     Stage 2: Fault Classification            │
  │  - XGBoost classifier                        │
  │  - Fault category mapping                    │
  └───────────────────────┬──────────────────────┘
                          │
                          ▼
  ┌──────────────────────────────────────────────┐
  │     Stage 3: RUL Prediction                  │
  │  - LightGBM regression                       │
  │  - Remaining Useful Life estimate            │
  └───────────────────────┬──────────────────────┘
                          │
                          ▼
  ┌──────────────────────────────────────────────┐
  │     Decision & Alerting Logic                │
  │  - Anomaly / Fault gating                    │
  │  - Alert payload construction                │
  └───────────────┬───────────────┬──────────────┘
                  │               │
                  ▼               ▼
  ┌──────────────────────┐  ┌────────────────────┐
  │  API Response        │  │   Kafka Producer   │
  │  - JSON prediction   │  │  (Async alerts)    │
  └──────────────────────┘  └──────────┬─────────┘
                                        ▼
                             ┌────────────────────┐
                             │  Downstream Systems│
                             │  - Monitoring      │
                             │  - Alerting        │
                             │  - Fleet analytics │
                             └────────────────────┘
```

```text
Data (Kaggle CSV)
   ↓
Training Pipeline (anomaly.py → classifier.py → rul.py)
   ├── Anomaly Detection (Isolation Forest)
   ├── Fault Classification (XGBoost với class weights)
   └── RUL Prediction (LightGBM)
   ↓
MLflow (Tracking + Artifacts + Metrics)
   ↓
FastAPI Inference API
   ├── /predict → Anomaly → Classifier → RUL
   ├── /health → Service status check
   ├── /metrics → Prometheus metrics
   └── /api/train → Trigger training
   ↓
Kafka (topic: ev_predictions) → Alert Service → Prometheus / Grafana
```

**Training Pipeline Features**:

- Reproducible với fixed random seeds
- Class imbalance handling với class weights
- Comprehensive metrics logging (accuracy, F1, RMSE, MAE, R²)
- MLflow integration cho tất cả models

Chi tiết workflow xem thêm trong `docs/WORKFLOW_GUIDE.md` và `docs/QUICK_WORKFLOW.md`.

---

## 📦 Chuẩn bị môi trường (cho người mới)

- Đã cài **Git**, **Docker Desktop** (Windows) hoặc Docker Engine.
- Python 3.10+ đã cài sẵn (chỉ cần nếu muốn chạy local ngoài Docker).
- Đã clone repo này về máy.

Dataset chính đã được giữ trong repo tại `src/data/EV_Predictive_Maintenance_Dataset_15min.csv`  
(nếu chưa có, xem script `scripts/download_dataset.ps1` và hướng dẫn trong `docs/DOCKER_WORKFLOW.md`).

---

## 🚀 Cách chạy bằng Docker (khuyến nghị)

### 1. Khởi động toàn bộ stack

Tại thư mục dự án:

```powershell
cd D:\code\MSE24_MLOP_EV_PM
docker compose up -d
```

Lệnh này sẽ chạy: MinIO, MLflow, Kafka, Zookeeper, Prometheus, Grafana, Alert Service và FastAPI (chưa train model).

### 2. Huấn luyện toàn bộ mô hình

**Option 1: Sử dụng Training Service UI (Khuyến nghị - Dễ nhất)**

```powershell
# Khởi động Training Service
docker compose up -d training-service

# Mở browser: http://localhost:8080
# Click "Start Training" để chạy training tự động
# UI sẽ hiển thị log real-time và status
```

**Option 2: Chạy trực tiếp qua Docker**

```powershell
docker compose build trainer         # build image trainer (nếu lần đầu hoặc mới sửa code)
docker compose run --rm trainer       # chạy train_wrapper, train anomaly + classifier + RUL
```

**Training Pipeline**:

1. `anomaly.py` - Train Isolation Forest, tạo parquet với IF_Anomaly labels
2. `classifier.py` - Train XGBoost với class weights cho imbalanced data
3. `rul.py` - Train LightGBM RUL model với encoded Maintenance_Type feature

Sau khi chạy xong:

- Thư mục `models/` sẽ được tạo với tất cả artifacts
- MLflow sẽ log các runs riêng biệt cho từng model với metrics đầy đủ
- Xem runs tại: http://localhost:5000/#/experiments/1

### 3. Khởi động / reload dịch vụ FastAPI Inference

```powershell
docker compose up -d fastapi-inference   # nếu chưa chạy
docker compose restart fastapi-inference # nếu đã chạy từ trước, cần nạp lại model
```

### 4. Truy cập các service

#### API Endpoints

- **FastAPI Root**: [http://localhost:8000/](http://localhost:8000/)
  - Thông tin API và danh sách endpoints
- **FastAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
  - Swagger UI để test API
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
  - Kiểm tra trạng thái models và services
- **Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
  - Prometheus metrics endpoint

#### Training & MLflow

- **Training Service UI**: [http://localhost:8080](http://localhost:8080) (nếu có)
  - Web UI để trigger và monitor training jobs
- **MLflow UI**: [http://localhost:5000](http://localhost:5000)
  - Xem training runs, metrics, và artifacts
  - Experiment: `predictive-maintenance`

#### Monitoring & Storage

- **Prometheus**: [http://localhost:9090](http://localhost:9090)
  - Query metrics và xem alerts
- **Grafana**: [http://localhost:3000](http://localhost:3000)
  - Username: `admin`, Password: `admin` (lần đầu đăng nhập)
  - Prometheus datasource đã được tự động cấu hình
- **Alertmanager**: [http://localhost:9093](http://localhost:9093)
  - Quản lý alerts và notifications
- **MinIO Console**: [http://localhost:9001](http://localhost:9001)
  - User: `minioadmin`, Password: `minioadmin`

**Khuyến nghị cho người mới**: Bắt đầu với **Training Service UI** hoặc `docker compose up trainer` để train models, sau đó mở **FastAPI docs** và **MLflow UI** để test và xem kết quả.

---

## 🔌 API Endpoints

### Core Endpoints

- **GET `/`** - Root endpoint với thông tin API và danh sách endpoints
- **GET `/health`** - Health check endpoint
  - Trả về status của models và services
  - Status codes: `200` (healthy), `503` (degraded)
- **GET `/metrics`** - Prometheus metrics endpoint
  - Format: Prometheus text format
  - Metrics: `inference_requests_total`, `inference_request_latency_seconds`, `anomaly_predictions_total`
- **POST `/predict`** - Inference endpoint (xem chi tiết bên dưới)

### Training Endpoints

- **POST `/api/train`** - Trigger training pipeline
  - Body: `{"force": false, "rebuild": true}`
- **GET `/api/training/status`** - Lấy training status
- **GET `/api/training/logs`** - Lấy training logs
- **POST `/api/models/reload`** - Reload models từ disk

### Documentation

- **GET `/docs`** - Swagger UI documentation
- **GET `/redoc`** - ReDoc documentation

## 🧪 Gửi request test tới API `/predict`

1. Mở [http://localhost:8000/docs](http://localhost:8000/docs) → chọn **POST /predict** → **Try it out**.
2. Dán payload mẫu sau (có thể chỉnh số liệu):

```json
{
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

    "SoC": 0.8,
    "SoH": 0.9,
    "Battery_Voltage": 350,
    "Battery_Current": 120,
    "Charge_Cycles": 1500,
    "Motor_Vibration": 0.02,
    "Power_Consumption": 20,
    "Brake_Pressure": 7,
    "Tire_Pressure": 2.3,
    "Ambient_Humidity": 60,
    "Load_Weight": 200,
    "Driving_Speed": 60,
    "Distance_Traveled": 200,
    "Idle_Time": 5,
    "Route_Roughness": 0.2,
    "Component_Health_Score": 0.8,
    "Failure_Probability": 0.1,
    "TTF": 1200
  }
}
```

Kết quả trả về sẽ gồm:

- `IF_Anomaly`: 0/1 – có bất thường hay không (từ Isolation Forest + rule-based override)
- `classifier_label`: loại lỗi dự đoán (fault type từ XGBoost classifier)
- `is_fault`: boolean – có phải lỗi hay không (dựa trên normal_label)
- `RUL_estimated`: ước lượng tuổi thọ còn lại (từ LightGBM, chỉ khi có fault)
- `status`: "Normal - no fault detected" (nếu không có anomaly)

**Lưu ý**:

- Mỗi request được track trong Prometheus metrics (`/metrics` endpoint)
- Các anomaly/fault predictions được gửi vào Kafka topic `ev_predictions` → Alert Service → Prometheus
- Bạn có thể xem metrics trong Prometheus/Grafana và alerts trong Alertmanager

---

## 🧑‍💻 Chạy local không dùng Docker (tùy chọn cho dev)

Nếu bạn muốn chạy mọi thứ thuần Python trên máy local (không Docker), xem file `README_RUN.md`:

- Tạo venv, `pip install -r requirements.txt`
- Chạy lần lượt:
  - `python src/anomaly.py`
  - `python src/classifier.py`
  - `python src/rul.py`
  - `python -m src.inference_server`
- Sau đó test API tại [http://localhost:8000/docs](http://localhost:8000/docs).

Docker vẫn được khuyến nghị cho người mới vì:

- Không cần tự cài Kafka, Prometheus, Grafana, MinIO.
- Môi trường đồng nhất với CI/CD.

---

## 📊 Monitoring & Metrics

### Prometheus Metrics

FastAPI expose các metrics sau tại `/metrics`:

- `inference_requests_total` - Tổng số requests
- `inference_request_latency_seconds` - Histogram latency (có thể tính p50, p95, p99)
- `anomaly_predictions_total` - Tổng số anomaly predictions

### Grafana Dashboards

Grafana đã được tự động cấu hình với:

- Prometheus datasource (tự động connect)
- Dashboard provisioning (tự động load dashboards từ `monitoring/grafana/dashboards/`)

Sau khi đăng nhập Grafana, bạn có thể:

- Tạo dashboard mới với các queries từ Prometheus
- Sử dụng dashboard mẫu: "EV Predictive Maintenance - Inference Metrics"
- Query ví dụ:
  ```promql
  rate(inference_requests_total[1m])
  histogram_quantile(0.95, rate(inference_request_latency_seconds_bucket[5m]))
  rate(anomaly_predictions_total[5m])
  ```

### Alerts

Prometheus alerts được cấu hình trong `monitoring/alerts.yml`:

- `FastAPIInferenceDown` - Service down detection
- `HighInferenceLatency` - p95 latency > 500ms
- `HighAnomalyRate` - 5+ anomalies trong 2 phút
- `NoInferenceTraffic` - Không có traffic trong 5 phút

Xem alerts tại: http://localhost:9090/alerts

## 📚 Tài liệu chi tiết

- **`docs/HIEU_HE_THONG.md`** ⭐ – **Giải thích chi tiết hệ thống cho người non-tech**
  - Workflow từng bước dễ hiểu
  - Giải thích tất cả thuật ngữ chuyên môn
  - Ví dụ thực tế và minh họa
  - **Khuyến nghị đọc đầu tiên nếu bạn mới bắt đầu!**
- `docs/README.md` – Mục lục tài liệu.
- `docs/WORKFLOW_GUIDE.md` – Giải thích workflow 9 bước chi tiết (kỹ thuật).
- `docs/QUICK_WORKFLOW.md` – Tóm tắt workflow và lệnh nhanh.
- `docs/DOCKER_WORKFLOW.md` – Hướng dẫn Docker workflow đầy đủ.
- `docs/PROMETHEUS_DEBUG.md` – Debug guide cho Prometheus và alerts.

Nếu bạn là người mới, lộ trình đề xuất:

1. Đọc phần **"Cách chạy bằng Docker"** ở trên và chạy thử.
2. Mở MLflow/Grafana để quan sát kết quả.
3. Test API qua `/docs` và kiểm tra metrics tại `/metrics`.
4. Khi đã quen flow, đọc sâu hơn `docs/WORKFLOW_GUIDE.md` để hiểu kiến trúc MLOps.

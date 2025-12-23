## EV Predictive Maintenance – Hướng dẫn chạy nhanh

**Đề tài**: Predictive Maintenance on Vehicle Telemetry Data  
**Mục tiêu**: Xây dựng prototype MLOps cho bảo trì dự đoán xe điện với:
- **Data**: Dataset Kaggle (telemetry EV)
- **Training**: Python, XGBoost, LightGBM, MLflow
- **Inference**: FastAPI
- **Streaming & Alert**: Kafka + Alert Service + Prometheus + Grafana

---

## 🔁 Flow tổng quan

```text
Data (Kaggle CSV)
   ↓
Processing + Feature Engineering
   ↓
Anomaly (Isolation Forest) + Classifier (XGBoost) + RUL (LightGBM)
   ↓
MLflow (Tracking + Artifacts)
   ↓
FastAPI Inference API  →  Kafka  →  Alert Service  →  Prometheus / Grafana
```

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

```powershell
docker compose build trainer         # build image trainer (nếu lần đầu hoặc mới sửa code)
docker compose up trainer            # chạy train_wrapper, train anomaly + classifier + RUL
```

Sau khi chạy xong, thư mục `models/` sẽ được tạo, MLflow sẽ log các run và artifacts.

### 3. Khởi động / reload dịch vụ FastAPI Inference

```powershell
docker compose up -d fastapi-inference   # nếu chưa chạy
docker compose restart fastapi-inference # nếu đã chạy từ trước, cần nạp lại model
```

### 4. Truy cập các service

- **FastAPI Inference**: [http://localhost:8000/docs](http://localhost:8000/docs)  
- **MLflow UI**: [http://localhost:5000](http://localhost:5000)  
- **MinIO Console**: [http://localhost:9001](http://localhost:9001)  
  - User: `minioadmin`, Password: `minioadmin`
- **Prometheus**: [http://localhost:9090](http://localhost:9090)  
- **Grafana**: [http://localhost:3000](http://localhost:3000)  
- **Alertmanager**: [http://localhost:9093](http://localhost:9093)

Với người mới, chỉ cần: mở **FastAPI docs**, **MLflow UI**, và (tuỳ chọn) **Grafana** để “vừa chạy vừa xem”.

---

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
- `IF_Anomaly`: 0/1 – có bất thường hay không.
- `classifier_label`: loại lỗi dự đoán (fault type).
- `RUL_estimated`: ước lượng tuổi thọ còn lại.

Mỗi request cũng sẽ được đẩy vào Kafka → Alert Service → Prometheus (bạn có thể xem metric trong Prometheus/Grafana).

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

## 📚 Tài liệu chi tiết

- `docs/README.md` – Mục lục tài liệu.
- `docs/WORKFLOW_GUIDE.md` – Giải thích workflow 9 bước chi tiết.
- `docs/QUICK_WORKFLOW.md` – Tóm tắt workflow và lệnh nhanh.
- `docs/DOCKER_WORKFLOW.md` – Hướng dẫn Docker workflow đầy đủ.

Nếu bạn là người mới, lộ trình đề xuất:
1. Đọc phần **“Cách chạy bằng Docker”** ở trên và chạy thử.  
2. Mở MLflow/Grafana để quan sát kết quả.  
3. Khi đã quen flow, đọc sâu hơn `docs/WORKFLOW_GUIDE.md` để hiểu kiến trúc MLOps.  

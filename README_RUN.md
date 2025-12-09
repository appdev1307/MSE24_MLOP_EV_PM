# EV Predictive Maintenance (Local + Docker) - Run Instructions

This package contains a runnable local MLOps prototype for Predictive Maintenance
using your EV telemetry CSV.

## Structure
- `src/` : training and inference scripts
- `data/features/` : features will be created here by preprocessing step
- `models/` : trained model artifacts will be saved here

## Prerequisites
- Linux / macOS (or WSL on Windows)
- Python 3.10+
- Docker (optional)

## Local run

1. Create virtualenv and install dependencies
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   -- if venv exists, ""

2. Prepare data and features
   ```bash
   #python src/preprocessing.py
   ```

3. Train anomaly detector
   ```bash
   python src/anomaly.py
   ```

4. Train classifier (on anomalies)
   ```bash
   python src/classifier.py
   ```

5. Train RUL regression
   ```bash
   python src/rul.py
   ```

6. Run the inference server locally
   ```bash
   python -m src.inference_server
   ```

7. Test
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



## Docker

colima start
docker compose down -v
docker compose pull
docker compose up --build -d


docker compose ps


MLflow → http://localhost:5000
MinIO → http://localhost:9000 (console: 9001)
Prometheus → http://localhost:9090
Grafana → http://localhost:3000

## docker

## Create MinIO buckets and Kafka topics (local):
```bash
chmod +x scripts/setup_minio_kafka.sh
./scripts/setup_minio_kafka.sh
```
## Trigger a training run (inside the trainer container):
```bash
# run the train_wrapper inside the trainer service
docker compose run --rm trainer


docker compose build fastapi-inference
docker compose run --rm fastapi-inference


## no docker
python src/create_minio_bucket.py
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin
export AWS_DEFAULT_REGION=us-east-1
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
python src/train_wrapper.py

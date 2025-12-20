# Predictive Maintenance MLOps - Example Project

This package contains a runnable local MLOps prototype for Predictive Maintenance
using your EV telemetry CSV.

## Project layout

```
project/
├── models/           # model artifacts written by your training scripts (.joblib)
├── src/              # training scripts ()
├── monitoring/       # prometheus config
├── alert_service/    # Alert services
└── docker-compose.yml
```

## Quick start (local, development)

1. Make sure Docker and Docker Compose are installed.
2. From the project root, run:
   ```bash
  colima start
  docker compose down -v
  docker compose pull
  docker compose up --build -d
  docker compose ps
  ```

  MLflow → http://localhost:5000
  MinIO → http://localhost:9001.   (User: minioadmin, Pass: minioadmin)
  Prometheus → http://localhost:9090
  Grafana → http://localhost:3000

   
3. Create MinIO buckets and Kafka topics (local):
# Create MinIO buckets and Kafka topics (local):
docker exec -it minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec -it minio mc mb local/mlflow-artifacts
docker exec -it minio mc ls local
   ```bash
   chmod +x scripts/setup_minio_kafka.sh
   ./scripts/setup_minio_kafka.sh
   ```

4. Testing
python test_alerts.py
curl http://localhost:8000/docs
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


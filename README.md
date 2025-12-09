# Predictive Maintenance MLOps - Example Project

## Project layout

```
project/
├── data/             # raw and processed datasets
├── models/           # model artifacts written by your training scripts (.joblib)
├── src/              # training scripts (your original scripts + wrapper)
├── inference/        # inference server + related files
├── monitoring/       # prometheus config
├── scripts/          # helper scripts: setup MinIO/Kafka, event -> GitLab
└── docker-compose.yml
```

## Quick start (local, development)

1. Make sure Docker and Docker Compose are installed.
2. From the project root, run:
   ```bash
   docker-compose up --build -d
   ```
3. Create MinIO buckets and Kafka topics (local):
   ```bash
   chmod +x scripts/setup_minio_kafka.sh
   ./scripts/setup_minio_kafka.sh
   ```
4. Trigger a training run (inside the trainer container):
   ```bash
   # run the train_wrapper inside the trainer service
   docker-compose run --rm trainer
   ```
5. Check MLflow UI: http://localhost:5000
6. Start inference (FastAPI is started by compose at :8000):
   ```bash
   # health check
   curl http://localhost:8000/health
   # predict
   curl -X POST http://localhost:8000/predict -H 'Content-Type: application/json' -d '{"data": {"feature1": 1.0}}'
   ```

## CI/CD
This project includes a `.gitlab-ci.yml` with stages for lint, test, build, train, deploy. Configure GitLab CI variables for MinIO credentials and Docker registry access.

## Notes
- Your original training scripts were included under `src/` unchanged.
- The wrapper `src/train_wrapper.py` executes your scripts and logs any `.joblib`/`.pkl` artifacts found under `models/` to MLflow.
- The inference service `inference/mlflow_inference.py` downloads artifacts from MLflow and loads the first joblib/pkl it finds.

# Runbook - Predictive Maintenance MLOps

## Prerequisites
- Docker
- Docker Compose

## Steps
1. Start stack:
   - `docker-compose up --build -d`
2. Create buckets & topics:
   - `chmod +x scripts/setup_minio_kafka.sh`
   - `./scripts/setup_minio_kafka.sh`
3. Place your dataset under `data/processed/` (or your training scripts' expected path)
4. Run training (local):
   - `docker-compose run --rm trainer`
5. View MLflow: http://localhost:5000
6. Test inference:
   - `curl http://localhost:8000/health`
   - `curl -X POST http://localhost:8000/predict -H 'Content-Type: application/json' -d '{"data": {"feature1": 1.0}}'`

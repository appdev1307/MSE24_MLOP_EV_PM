#!/bin/bash
# Quick script to create MinIO bucket for MLflow artifacts

echo "🔧 Setting up MinIO bucket..."

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
sleep 5

# Create bucket using MinIO client
docker compose exec -T minio mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null || true
docker compose exec -T minio mc mb local/mlflow-artifacts 2>/dev/null || echo "Bucket may already exist"

echo "✅ MinIO bucket setup complete!"
echo "You can now run: docker compose run --rm trainer"


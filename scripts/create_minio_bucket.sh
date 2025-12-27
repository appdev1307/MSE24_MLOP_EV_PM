#!/bin/bash

# Script to create MinIO bucket for MLflow artifacts
# This should be run after MinIO service is started

set -e

BUCKET_NAME="mlflow-artifacts"
MINIO_ALIAS="local"
MINIO_ENDPOINT="http://localhost:9000"
MINIO_USER="minioadmin"
MINIO_PASSWORD="minioadmin"

echo "Creating MinIO bucket: $BUCKET_NAME"

# Check if MinIO container is running
if ! docker compose ps minio | grep -q "Up"; then
    echo "❌ MinIO container is not running. Please start it first:"
    echo "   docker compose up -d minio"
    exit 1
fi

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO to be ready..."
sleep 3

# Set MinIO alias
echo "📝 Setting MinIO alias..."
docker compose exec -T minio mc alias set $MINIO_ALIAS $MINIO_ENDPOINT $MINIO_USER $MINIO_PASSWORD

# Create bucket if it doesn't exist
echo "📦 Creating bucket: $BUCKET_NAME"
if docker compose exec -T minio mc mb $MINIO_ALIAS/$BUCKET_NAME 2>/dev/null; then
    echo "✅ Bucket '$BUCKET_NAME' created successfully"
else
    # Check if bucket already exists
    if docker compose exec -T minio mc ls $MINIO_ALIAS | grep -q "$BUCKET_NAME"; then
        echo "ℹ️  Bucket '$BUCKET_NAME' already exists"
    else
        echo "❌ Failed to create bucket. Please check MinIO logs:"
        echo "   docker compose logs minio"
        exit 1
    fi
fi

# List buckets to verify
echo ""
echo "📋 Current buckets:"
docker compose exec -T minio mc ls $MINIO_ALIAS

echo ""
echo "✅ Done!"






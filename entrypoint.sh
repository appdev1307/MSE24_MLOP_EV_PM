#!/usr/bin/env bash
set -euo pipefail

# Wait helper (optional)
wait_for() {
  host=$1
  port=$2
  echo "Waiting for $host:$port ..."
  while ! nc -z "$host" "$port"; do
    sleep 1
  done
}

# Optionally wait for Postgres/MinIO/MLflow if configured
if [ -n "${POSTGRES_HOST:-}" ]; then
  wait_for "${POSTGRES_HOST:-}" "${POSTGRES_PORT:-5432}"
fi

if [ -n "${MINIO_HOST:-}" ]; then
  wait_for "${MINIO_HOST:-}" "${MINIO_PORT:-9000}"
fi

echo "Starting inference server (uvicorn)..."
exec uvicorn src.inference_server:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-2} --log-level info

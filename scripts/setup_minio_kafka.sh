#!/usr/bin/env bash
set -euo pipefail

MINIO_ENDPOINT=${MINIO_ENDPOINT:-http://localhost:9000}
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-minioadmin}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-minioadmin}
BUCKETS=(mlflow-artifacts datasets models logs)

KAFKA_BOOTSTRAP=${KAFKA_BOOTSTRAP:-localhost:9092}
TOPICS=(raw_sensor_data preprocessed_data predictions)

echo "Creating MinIO buckets: ${BUCKETS[*]}"

for b in "${BUCKETS[@]}"; do
  echo "Creating bucket: ${b}"
  docker run --rm -e AWS_ACCESS_KEY_ID=${MINIO_ACCESS_KEY} -e AWS_SECRET_ACCESS_KEY=${MINIO_SECRET_KEY} \
    amazon/aws-cli --endpoint-url ${MINIO_ENDPOINT} s3 mb s3://${b} || true
done

echo "Creating Kafka topics: ${TOPICS[*]}"

for t in "${TOPICS[@]}"; do
  echo "Creating topic: ${t}"
  docker run --rm --network host bitnami/kafka:latest kafka-topics.sh --create --topic ${t} --bootstrap-server ${KAFKA_BOOTSTRAP} --partitions 3 --replication-factor 1 || true
done

echo "Setup complete."

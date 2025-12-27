.PHONY: help init init-venv train build-trainer setup-bucket up down restart logs clean clean-venv train-local

# Default target
help:
	@echo "EV Predictive Maintenance - MLOps Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make init            - Create Python virtual environment and install dependencies"
	@echo "  make train           - Build and run training pipeline"
	@echo "  make build-trainer   - Build trainer Docker image"
	@echo "  make setup-bucket    - Create MinIO bucket for MLflow artifacts"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make logs            - Show logs from all services"
	@echo "  make clean           - Remove containers, volumes, and images"
	@echo "  make train-local     - Run training locally (without Docker)"
	@echo "  make setup           - Initial setup (start services + create bucket)"
	@echo ""

# Virtual environment setup
init: init-venv
	@echo "✅ Virtual environment initialized!"
	@echo ""
	@echo "To activate the virtual environment, run:"
	@echo "  source .venv/bin/activate"
	@echo ""
	@echo "Or on Windows:"
	@echo "  .venv\\Scripts\\activate"

init-venv:
	@echo "🐍 Setting up Python virtual environment..."
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv .venv; \
	fi
	@echo "📦 Installing dependencies from requirements.txt..."
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

# Training operations
train: build-trainer setup-bucket
	@echo "🚂 Starting training pipeline..."
	docker compose run --rm trainer

build-trainer:
	@echo "🔨 Building trainer image..."
	docker compose build trainer

# Setup operations
setup: up setup-bucket
	@echo "✅ Setup complete! Services are running and bucket is created."

setup-bucket:
	@echo "🔧 Setting up MinIO bucket..."
	@docker compose up -d minio || true
	@sleep 5
	@docker compose exec -T minio mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null || true
	@docker compose exec -T minio mc mb local/mlflow-artifacts 2>/dev/null || echo "Bucket may already exist"
	@echo "✅ MinIO bucket setup complete!"

# Service management
up:
	@echo "🚀 Starting all services..."
	docker compose up -d

down:
	@echo "🛑 Stopping all services..."
	docker compose down

restart: down up
	@echo "🔄 Services restarted"

logs:
	@echo "📋 Showing logs from all services..."
	docker compose logs -f

# Individual service logs
logs-trainer:
	docker compose logs -f trainer

logs-mlflow:
	docker compose logs -f mlflow

logs-inference:
	docker compose logs -f fastapi-inference

logs-minio:
	docker compose logs -f minio

# Clean operations
clean:
	@echo "🧹 Cleaning up containers, volumes, and images..."
	docker compose down -v
	@echo "✅ Cleanup complete!"

clean-models:
	@echo "🧹 Cleaning local models directory..."
	rm -rf models/
	@echo "✅ Models directory cleaned!"

clean-venv:
	@echo "🧹 Removing virtual environment..."
	rm -rf .venv
	@echo "✅ Virtual environment removed!"

# Local training (without Docker)
train-local:
	@echo "🚂 Running training locally..."
	@if [ ! -d ".venv" ]; then \
		echo "⚠️  Virtual environment not found. Run 'make init' first."; \
		exit 1; \
	fi
	@.venv/bin/python src/train.py

# Individual model training
train-anomaly:
	@echo "🚂 Training anomaly detection model..."
	docker compose run --rm trainer python src/anomaly.py

train-classifier:
	@echo "🚂 Training classifier model..."
	docker compose run --rm trainer python src/classifier.py

train-rul:
	@echo "🚂 Training RUL prediction model..."
	docker compose run --rm trainer python src/rul.py

# Service status
status:
	@echo "📊 Service status:"
	@docker compose ps

# Quick access URLs
urls:
	@echo "🌐 Service URLs:"
	@echo "  FastAPI Docs:     http://localhost:8000/docs"
	@echo "  MLflow UI:        http://localhost:6969"
	@echo "  Prometheus:       http://localhost:9090"
	@echo "  Grafana:          http://localhost:3000"
	@echo "  Alertmanager:     http://localhost:9093"
	@echo "  MinIO Console:    http://localhost:9001"

# Development helpers
shell-trainer:
	@echo "🐚 Opening shell in trainer container..."
	docker compose run --rm trainer /bin/bash

shell-inference:
	@echo "🐚 Opening shell in inference container..."
	docker compose exec fastapi-inference /bin/bash

# Rebuild everything
rebuild: down
	@echo "🔨 Rebuilding all images..."
	docker compose build --no-cache
	@echo "✅ Rebuild complete!"

# Full workflow
workflow: setup build-trainer train
	@echo "✅ Complete workflow finished!"
	@echo "📊 View results at: http://localhost:6969"


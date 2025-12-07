# Production stack - EV Predictive Maintenance

## Prerequisites
- Docker & Docker Compose
- Ports: 5000, 9000, 9001, 8000 available
- Set sensible secrets in `.env` from `.env.example`

## Quick start
1. Copy `.env` and edit secrets.
2. Build & run:
   ```bash
   docker compose up --build -d

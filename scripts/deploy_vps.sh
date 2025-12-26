#!/bin/bash

# ============================================
# Script deploy MLOps EV Predictive Maintenance lên VPS Ubuntu
# ============================================

set -e  # Exit on error

echo "=========================================="
echo "🚀 Deploy MLOps EV Predictive Maintenance"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${YELLOW}⚠️  Warning: Running as root. Consider using a non-root user with sudo.${NC}"
fi

# ============================================
# 1. Check prerequisites
# ============================================
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo "   Run: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi
echo -e "${GREEN}✅ Docker installed: $(docker --version)${NC}"

# Check Docker Compose
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose installed${NC}"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running. Please start Docker.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker daemon is running${NC}"

# Check if user is in docker group (optional but recommended)
if ! groups | grep -q docker; then
    echo -e "${YELLOW}⚠️  Current user is not in docker group.${NC}"
    echo "   You may need to run commands with sudo or add user to docker group:"
    echo "   sudo usermod -aG docker $USER"
    echo "   (Then logout and login again)"
fi

# ============================================
# 2. Check dataset
# ============================================
echo ""
echo "📊 Checking dataset..."

DATASET_PATH="src/data/EV_Predictive_Maintenance_Dataset_15min.csv"

if [ ! -f "$DATASET_PATH" ]; then
    echo -e "${YELLOW}⚠️  Dataset not found at $DATASET_PATH${NC}"
    echo "   You need to download the dataset first."
    echo "   Option 1: Download manually from Kaggle"
    echo "   Option 2: Use the download script (if available)"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Dataset found: $DATASET_PATH${NC}"
    DATASET_SIZE=$(du -h "$DATASET_PATH" | cut -f1)
    echo "   Size: $DATASET_SIZE"
fi

# ============================================
# 3. Check ports availability
# ============================================
echo ""
echo "🔌 Checking port availability..."

PORTS=(2181 9092 9000 9001 5000 8000 9101 9093 9090 3000)
PORTS_IN_USE=()

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$port "; then
        PORTS_IN_USE+=($port)
    fi
done

if [ ${#PORTS_IN_USE[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: The following ports are already in use:${NC}"
    for port in "${PORTS_IN_USE[@]}"; do
        echo "   - Port $port"
    done
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ All required ports are available${NC}"
fi

# ============================================
# 4. Configure firewall (optional)
# ============================================
echo ""
echo "🔥 Firewall configuration..."

if command -v ufw &> /dev/null; then
    if sudo ufw status | grep -q "Status: active"; then
        echo -e "${YELLOW}⚠️  UFW firewall is active${NC}"
        echo "   You may need to allow the following ports:"
        echo "   - 8000 (FastAPI Inference API)"
        echo "   - 5000 (MLflow UI)"
        echo "   - 3000 (Grafana)"
        echo "   - 9090 (Prometheus)"
        echo ""
        read -p "Open these ports now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo ufw allow 8000/tcp
            sudo ufw allow 5000/tcp
            sudo ufw allow 3000/tcp
            sudo ufw allow 9090/tcp
            echo -e "${GREEN}✅ Ports opened${NC}"
        fi
    fi
fi

# ============================================
# 5. Build and start services
# ============================================
echo ""
echo "🏗️  Building Docker images..."

# Build images (this may take a while)
docker compose build

echo ""
echo "🚀 Starting services..."

# Start services in detached mode
docker compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# ============================================
# 6. Check service status
# ============================================
echo ""
echo "📊 Service status:"
docker compose ps

# ============================================
# 7. Display access information
# ============================================
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo "=========================================="
echo ""
echo "📡 Access URLs:"
echo ""
echo "  FastAPI Inference API:"
echo "    - API:      http://$(hostname -I | awk '{print $1}'):8000"
echo "    - Docs:     http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "    - Health:   http://$(hostname -I | awk '{print $1}'):8000/health"
echo ""
echo "  MLflow:"
echo "    - UI:       http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "  Monitoring:"
echo "    - Grafana:  http://$(hostname -I | awk '{print $1}'):3000 (admin/admin)"
echo "    - Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
echo ""
echo "  MinIO:"
echo "    - Console:  http://$(hostname -I | awk '{print $1}'):9001 (minioadmin/minioadmin)"
echo ""
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "  1. Train models (required before using inference):"
echo "     docker compose run --rm trainer"
echo ""
echo "  2. Check service logs:"
echo "     docker compose logs -f [service_name]"
echo ""
echo "  3. Stop services:"
echo "     docker compose down"
echo ""
echo "  4. View all logs:"
echo "     docker compose logs -f"
echo ""
echo "=========================================="


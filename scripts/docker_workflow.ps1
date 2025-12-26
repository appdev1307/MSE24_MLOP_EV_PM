# Complete Docker Workflow Script
# Thực hiện toàn bộ workflow từ training đến deployment

param(
    [switch]$SkipDownload,
    [switch]$SkipTraining,
    [switch]$SkipDeploy
)

Write-Host "🚀 Docker Workflow - Predictive Maintenance" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Stage 1: Check Dataset
if (-not $SkipDownload) {
    Write-Host "`n📥 Stage 1: Checking Dataset..." -ForegroundColor Yellow
    $datasetPath = "src/data/EV_Predictive_Maintenance_Dataset_15min.csv"
    
    if (-not (Test-Path $datasetPath)) {
        Write-Host "⚠️  Dataset not found: $datasetPath" -ForegroundColor Yellow
        Write-Host "Please download dataset first:" -ForegroundColor White
        Write-Host "  1. Manual: https://www.kaggle.com/datasets/datasetengineer/eviot-predictivemaint-dataset/data" -ForegroundColor Gray
        Write-Host "  2. Script: .\scripts\download_dataset.ps1" -ForegroundColor Gray
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne "y") {
            exit 1
        }
    } else {
        Write-Host "✅ Dataset found: $datasetPath" -ForegroundColor Green
    }
}

# Stage 2-4: Start Services & Train
if (-not $SkipTraining) {
    Write-Host "`n📦 Stage 2-4: Starting Services & Training..." -ForegroundColor Yellow
    
    # Start infrastructure
    Write-Host "Starting infrastructure services..." -ForegroundColor Cyan
    docker compose up -d minio mlflow
    
    # Wait for services
    Write-Host "Waiting for services to be ready..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    
    # Setup MinIO
    Write-Host "Setting up MinIO bucket..." -ForegroundColor Cyan
    docker compose exec -T minio mc alias set local http://localhost:9000 minioadmin minioadmin 2>$null
    docker compose exec -T minio mc mb local/mlflow-artifacts 2>$null
    
    # Build và train
    Write-Host "Building trainer image..." -ForegroundColor Cyan
    docker compose build trainer
    
    Write-Host "Training models..." -ForegroundColor Cyan
    docker compose up trainer
    
    Write-Host "✅ Training completed!" -ForegroundColor Green
} else {
    Write-Host "`n⏭️  Skipping training..." -ForegroundColor Yellow
}

# Stage 5-6: View Results
Write-Host "`n📊 Stage 5-6: View Experiments & Metrics" -ForegroundColor Yellow
Write-Host "Open MLflow UI: http://localhost:6969" -ForegroundColor Cyan
Write-Host "Experiments are logged in: predictive-maintenance" -ForegroundColor White

# Stage 7-8: Register Model
Write-Host "`n📝 Stage 7-8: Select Best Model & Register" -ForegroundColor Yellow
Write-Host "1. Go to http://localhost:6969" -ForegroundColor White
Write-Host "2. Compare experiments" -ForegroundColor White
Write-Host "3. Select best model" -ForegroundColor White
Write-Host "4. Register to Model Registry" -ForegroundColor White
Write-Host "5. Transition to Staging → Production" -ForegroundColor White

# Stage 9: Deploy
if (-not $SkipDeploy) {
    Write-Host "`n🚀 Stage 9: Deploying to Production..." -ForegroundColor Yellow
    
    Write-Host "Building inference service..." -ForegroundColor Cyan
    docker compose build fastapi-inference
    
    Write-Host "Starting inference service..." -ForegroundColor Cyan
    docker compose up -d fastapi-inference
    
    Write-Host "Starting monitoring services..." -ForegroundColor Cyan
    docker compose up -d prometheus grafana alertmanager
    
    Write-Host "✅ Deployment completed!" -ForegroundColor Green
    Write-Host "`n📊 Services:" -ForegroundColor Cyan
    Write-Host "  - API: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  - MLflow: http://localhost:6969" -ForegroundColor White
    Write-Host "  - Prometheus: http://localhost:9090" -ForegroundColor White
    Write-Host "  - Grafana: http://localhost:3000" -ForegroundColor White
} else {
    Write-Host "`n⏭️  Skipping deployment..." -ForegroundColor Yellow
}

Write-Host "`n✅ Workflow completed!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan



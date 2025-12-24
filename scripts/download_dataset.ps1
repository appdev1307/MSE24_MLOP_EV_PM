# Download dataset from Kaggle (PowerShell)
# Requires: pip install kaggle
# Setup Kaggle API: https://www.kaggle.com/docs/api

$DATASET_NAME = "datasetengineer/eviot-predictivemaint-dataset"
$DATA_DIR = "src/data"
$FILENAME = "EV_Predictive_Maintenance_Dataset_15min.csv"

Write-Host "Downloading dataset from Kaggle..." -ForegroundColor Cyan
Write-Host "Dataset: $DATASET_NAME"

# Check if kaggle is installed
try {
    $null = Get-Command kaggle -ErrorAction Stop
    Write-Host "Kaggle CLI found" -ForegroundColor Green
} catch {
    Write-Host "kaggle CLI not found. Installing..." -ForegroundColor Yellow
    pip install kaggle
}

# Check Kaggle credentials
if (-not (Test-Path "$env:USERPROFILE\.kaggle\kaggle.json")) {
    Write-Host "Kaggle credentials not found!" -ForegroundColor Yellow
    Write-Host "Please setup Kaggle API:" -ForegroundColor Yellow
    Write-Host "1. Go to https://www.kaggle.com/settings" -ForegroundColor White
    Write-Host "2. Create API token" -ForegroundColor White
    Write-Host "3. Save kaggle.json to $env:USERPROFILE\.kaggle\" -ForegroundColor White
    exit 1
}

# Create data directory
if (-not (Test-Path $DATA_DIR)) {
    New-Item -ItemType Directory -Path $DATA_DIR -Force | Out-Null
    Write-Host "Created directory: $DATA_DIR" -ForegroundColor Green
}

# Download dataset
Write-Host "`nDownloading..." -ForegroundColor Green
Push-Location $DATA_DIR
try {
    kaggle datasets download -d $DATASET_NAME -p .
    
    # Extract zip file
    $zipFiles = Get-ChildItem -Filter "*.zip"
    if ($zipFiles) {
        Write-Host "Extracting..." -ForegroundColor Green
        Expand-Archive -Path $zipFiles[0].Name -DestinationPath . -Force
        Remove-Item -Path "*.zip" -Force
        Write-Host "Extracted dataset" -ForegroundColor Green
    }
    
    # Check if file exists
    if (Test-Path $FILENAME) {
        Write-Host "`nDataset downloaded successfully!" -ForegroundColor Green
        Write-Host "Location: $DATA_DIR\$FILENAME" -ForegroundColor White
        $fileInfo = Get-Item $FILENAME
        Write-Host "Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor White
        Write-Host "Last Modified: $($fileInfo.LastWriteTime)" -ForegroundColor White
    } else {
        Write-Host "`nWarning: Expected file $FILENAME not found" -ForegroundColor Yellow
        Write-Host "Available files:" -ForegroundColor Yellow
        Get-ChildItem | Select-Object Name, Length
    }
} catch {
    Write-Host "`nError downloading dataset: $_" -ForegroundColor Red
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "1. Kaggle API credentials are set up" -ForegroundColor White
    Write-Host "2. You have access to the dataset" -ForegroundColor White
    Write-Host "3. Internet connection is available" -ForegroundColor White
} finally {
    Pop-Location
}

Write-Host "`nDone!" -ForegroundColor Green



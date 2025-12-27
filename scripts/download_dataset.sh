#!/bin/bash

# Download dataset from Kaggle (Linux/Unix)
# Requires: pip install kaggle
# Setup Kaggle API: https://www.kaggle.com/docs/api

DATASET_NAME="datasetengineer/eviot-predictivemaint-dataset"
DATA_DIR="src/data"
FILENAME="EV_Predictive_Maintenance_Dataset_15min.csv"

echo "Downloading dataset from Kaggle..."
echo "Dataset: $DATASET_NAME"

# Check if kaggle is installed
if ! command -v kaggle &> /dev/null; then
    echo "kaggle CLI not found. Installing..."
    pip install kaggle
fi

# Check Kaggle credentials
if [ ! -f "$HOME/.kaggle/kaggle.json" ]; then
    echo "Kaggle credentials not found!"
    echo "Please setup Kaggle API:"
    echo "1. Go to https://www.kaggle.com/settings"
    echo "2. Create API token"
    echo "3. Save kaggle.json to $HOME/.kaggle/"
    echo "4. Set permissions: chmod 600 $HOME/.kaggle/kaggle.json"
    exit 1
fi

# Set proper permissions for kaggle.json
chmod 600 "$HOME/.kaggle/kaggle.json"

# Create data directory
mkdir -p "$DATA_DIR"
echo "Created directory: $DATA_DIR"

# Download dataset
echo ""
echo "Downloading..."
cd "$DATA_DIR" || exit 1

kaggle datasets download -d "$DATASET_NAME" -p .

# Extract zip file if exists
if ls *.zip 1> /dev/null 2>&1; then
    echo "Extracting..."
    unzip -o *.zip
    rm -f *.zip
    echo "Extracted dataset"
fi

# Check if file exists
if [ -f "$FILENAME" ]; then
    echo ""
    echo "Dataset downloaded successfully!"
    echo "Location: $DATA_DIR/$FILENAME"
    ls -lh "$FILENAME"
else
    echo ""
    echo "Warning: Expected file $FILENAME not found"
    echo "Available files:"
    ls -lh
fi

echo ""
echo "Done!"






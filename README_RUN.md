# EV Predictive Maintenance (Local + Docker) - Run Instructions

This package contains a runnable local MLOps prototype for Predictive Maintenance
using your EV telemetry CSV.

## Structure
- `src/` : training and inference scripts
- `data/features/` : features will be created here by preprocessing step
- `models/` : trained model artifacts will be saved here

## Prerequisites
- Linux / macOS (or WSL on Windows)
- Python 3.10+
- Docker (optional)

## Local run

1. Create virtualenv and install dependencies
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   export EV_CSV=/Users/macintoshhd/Downloads/MSE24/2025_semester_03/MLOps/Final_thesis/ev_pm_mlops_package/src/data/EV_Predictive_Maintenance_Dataset_15min.csv


2. Prepare data and features
   ```bash
   #python src/preprocessing.py
   ```

3. Train anomaly detector
   ```bash
   python src/anomaly.py
   ```

4. Train classifier (on anomalies)
   ```bash
   python src/classifier.py
   ```

5. Train RUL regression
   ```bash
   python src/rul.py
   ```

6. Run the inference server locally
   ```bash
   python -m src.inference_server
   ```

7. Test
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
 -d '{"payload": {"State_of_Charge": 80, "Battery_Temperature": 30, "Motor_Temperature": 60, "Ambient_Temperature": 25, "Odometer": 12000, "Speed": 60, "Current": 120, "Voltage": 350, "Health_Index": 85, "Vehicle_ID":"EV-1"}}'


## Docker

1. Build image
   ```bash
   docker build -t ev-inference:local .
   ```

2. Run container
   ```bash
   docker run --rm -p 8080:8080 \
     -v $(pwd)/models:/app/models \
     -v /path/to/EV_Predictive_Maintenance_Dataset_15min.csv:/app/data/EV_Predictive_MAINT.csv:ro \
     ev-inference:local
   ```

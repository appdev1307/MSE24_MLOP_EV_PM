# src/rul.py
# Train LightGBM RUL model using 'RUL' target and include the Maintenance_Type encoded (if available)
# RUL trained on full dataset; RUL model will accept same numeric features + encoded fault label (if present)

import os
import random
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from lightgbm import LGBMRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from math import sqrt
import mlflow

SEED = 42


def set_seed(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


set_seed()

# Resolve paths relative to repository root for Docker/local consistency
ROOT = Path(__file__).resolve().parent
BASE_CSV = ROOT / "data" / "EV_Predictive_Maintenance_Dataset_15min.csv"
PARQUET_IF = ROOT.parent / "data" / "features_with_anomaly.parquet"
MODEL_DIR = ROOT.parent / "models" / "rul"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Load data (prefer annotated)
if PARQUET_IF.exists():
    df = pd.read_parquet(PARQUET_IF)
    print("Loaded annotated:", PARQUET_IF)
else:
    df = pd.read_csv(BASE_CSV)
    print("Loaded CSV:", BASE_CSV)

# Validate RUL target exists
if "RUL" not in df.columns:
    raise RuntimeError("Column 'RUL' not found in dataset. Cannot train RUL.")

# Features (same numeric ones)
FEATURES = [
    "SoC", "SoH", "Battery_Voltage", "Battery_Current", "Battery_Temperature",
    "Charge_Cycles", "Motor_Temperature", "Motor_Vibration", "Motor_Torque",
    "Motor_RPM", "Power_Consumption", "Brake_Pad_Wear", "Brake_Pressure",
    "Reg_Brake_Efficiency", "Tire_Pressure", "Tire_Temperature", "Suspension_Load",
    "Ambient_Temperature", "Ambient_Humidity", "Load_Weight", "Driving_Speed",
    "Distance_Traveled", "Idle_Time", "Route_Roughness", "Component_Health_Score",
    "Failure_Probability", "TTF"
]
features = [c for c in FEATURES if c in df.columns]

# Optionally include Maintenance_Type encoded as a numeric feature
label_col_path = "models/classifier/label_col.joblib"
label_encoder_path = "models/classifier/label_encoder.joblib"
if os.path.exists(label_col_path):
    label_col = joblib.load(label_col_path)
else:
    label_col = None

if label_col and label_col in df.columns:
    # ensure encoder exists or build one from training data if missing
    if os.path.exists(label_encoder_path):
        le = joblib.load(label_encoder_path)
    else:
        le = LabelEncoder()
        df[label_col] = df[label_col].astype(str)
        df[label_col] = le.fit_transform(df[label_col])
        joblib.dump(le, label_encoder_path)
    # add encoded label as feature
    df[label_col] = le.transform(df[label_col].astype(str))
    features.append(label_col)

if not features:
    raise RuntimeError("No features available for RUL training.")

# Prepare data
X = df[features].fillna(0.0).astype(float)
y = df["RUL"].astype(float)

# Train-test split (train on full with small holdout optional)
# We'll do a quick random split for evaluation but fit on full for deployment to maximize data
from sklearn.model_selection import train_test_split
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.15, random_state=SEED)

model_params = {
    "n_estimators": 400,
    "learning_rate": 0.05,
    "random_state": SEED
}
model = LGBMRegressor(**model_params)
model.fit(Xtr, ytr)

pred = model.predict(Xte)
rmse = sqrt(mean_squared_error(yte, pred))
mae = mean_absolute_error(yte, pred)
r2 = r2_score(yte, pred)
print("RUL model RMSE (val):", rmse)
print("RUL model MAE (val):", mae)
print("RUL model R2 (val):", r2)

# Re-fit on full dataset before saving (recommended)
model.fit(X, y)

# Save model + features
joblib.dump(model, os.path.join(MODEL_DIR, "lgbm_rul.joblib"))
joblib.dump(features, os.path.join(MODEL_DIR, "rul_features.joblib"))

print("Saved RUL model & feature list to", MODEL_DIR)

# MLflow logging
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:6969"))
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT", "predictive-maintenance"))
with mlflow.start_run(run_name="rul"):
    # Set tags for filtering in MLflow UI
    dataset_name = BASE_CSV.stem  # e.g., "EV_Predictive_Maintenance_Dataset_15min"
    mlflow.set_tag("dataset", dataset_name)
    mlflow.set_tag("model", "LightGBM")
    
    mlflow.log_params({
        **model_params,
        "feature_count": len(features)
    })
    mlflow.log_metrics({
        "rmse": rmse,
        "mae": mae,
        "r2": r2
    })

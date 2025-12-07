# src/anomaly.py
import os
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

CSV = "src/data/EV_Predictive_Maintenance_Dataset_15min.csv"
OUT_PARQUET = "data/features_with_anomaly.parquet"
MODEL_DIR = "models/anomaly"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)

print("Loading:", CSV)
df = pd.read_csv(CSV)

# Exact numeric features from your CSV
FEATURES = [
    "State_of_Charge",
    "Battery_Temperature",
    "Motor_Temperature",
    "Ambient_Temperature",
    "Odometer",
    "Speed",
    "Current",
    "Voltage",
    "Health_Index",
]

# Keep only features that exist (defensive)
FEATURES = [c for c in FEATURES if c in df.columns]
if not FEATURES:
    raise RuntimeError("No feature columns found in dataset.")

X = df[FEATURES].fillna(0.0).astype(float)

print("Using features:", FEATURES)

# Scale
scaler = StandardScaler()
Xs = scaler.fit_transform(X)

# Train IsolationForest
iso = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
iso.fit(Xs)

# Predict: sklearn returns 1 normal, -1 anomaly -> convert to 0/1
if_pred = iso.predict(Xs)
df["IF_Anomaly"] = (if_pred == -1).astype(int)

# If original Anomaly column exists, keep it (supervised label)
# Save artifacts
joblib.dump(iso, os.path.join(MODEL_DIR, "isolation_forest.joblib"))
joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))
joblib.dump(FEATURES, os.path.join(MODEL_DIR, "isofeat.joblib"))

df.to_parquet(OUT_PARQUET, index=False)

print("Saved:", OUT_PARQUET)
print("Models saved to:", MODEL_DIR)
print("IF anomaly rate:", df["IF_Anomaly"].mean())

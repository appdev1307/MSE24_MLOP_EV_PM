# src/classifier.py
# Trains a classifier to predict Maintenance_Type (preferred).
# If Maintenance_Type missing, falls back to supervised 'Anomaly' column (if present),
# otherwise uses the generated IF_Anomaly label (unsupervised -> supervised fallback).

import os
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, accuracy_score

# Resolve paths relative to repository root to avoid CWD issues (Docker/local)
ROOT = Path(__file__).resolve().parent
BASE_CSV = ROOT / "data" / "EV_Predictive_Maintenance_Dataset_15min.csv"
PARQUET_IF = ROOT.parent / "data" / "features_with_anomaly.parquet"
MODEL_DIR = ROOT.parent / "models" / "classifier"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Load data: prefer annotated parquet (contains IF_Anomaly)
if PARQUET_IF.exists():
    df = pd.read_parquet(PARQUET_IF)
    print("Loaded annotated data:", PARQUET_IF)
else:
    df = pd.read_csv(BASE_CSV)
    print("Loaded CSV:", BASE_CSV)

# Determine label: prefer Maintenance_Type -> else Anomaly -> else IF_Anomaly
label_candidates = ["Maintenance_Type", "Anomaly", "IF_Anomaly"]
label_col = next((c for c in label_candidates if c in df.columns), None)
if label_col is None:
    raise RuntimeError("No suitable label found for classifier. Expected Maintenance_Type or Anomaly or IF_Anomaly.")

print("Training classifier using label:", label_col)

# Features to use (numeric list)
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
if not features:
    raise RuntimeError("No numeric features available for classifier.")

X = df[features].fillna(0.0).astype(float)
y_raw = df[label_col].copy()

# If label is Maintenance_Type (likely string), encode it
label_encoder = None
if y_raw.dtype == object or not np.issubdtype(y_raw.dtype, np.number):
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw.astype(str))
else:
    y = y_raw.astype(int).values

# Keep track of what value is 'normal' (most frequent label) — treat as non-fault
unique, counts = np.unique(y, return_counts=True)
normal_label = unique[np.argmax(counts)]
print("Inferred normal label (most frequent class) ->", normal_label)

# Split and scale
scaler = StandardScaler()
Xs = scaler.fit_transform(X)
Xtr, Xte, ytr, yte = train_test_split(Xs, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y))>1 else None)

# Train a fast XGBoost classifier
clf = XGBClassifier(
    n_estimators=150,
    max_depth=4,
    learning_rate=0.12,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric="mlogloss",
    tree_method="hist",
    random_state=42
)
clf.fit(Xtr, ytr)

pred = clf.predict(Xte)
print("Classifier accuracy:", accuracy_score(yte, pred))
print(classification_report(yte, pred, zero_division=1))

# Save artifacts: model, scaler, features, label encoder, normal_label
joblib.dump(clf, os.path.join(MODEL_DIR, "classifier.joblib"))
joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))
joblib.dump(features, os.path.join(MODEL_DIR, "features.joblib"))
joblib.dump(label_col, os.path.join(MODEL_DIR, "label_col.joblib"))
joblib.dump(normal_label, os.path.join(MODEL_DIR, "normal_label.joblib"))
if label_encoder is not None:
    joblib.dump(label_encoder, os.path.join(MODEL_DIR, "label_encoder.joblib"))

print("Saved classifier artifacts to", MODEL_DIR)

# src/anomaly.py
import os
import random
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
import mlflow

SEED = 42


def set_seed(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


set_seed()

# Resolve paths relative to repository root for Docker/local consistency
ROOT = Path(__file__).resolve().parent
CSV = ROOT / "data" / "EV_Predictive_Maintenance_Dataset_15min.csv"
OUT_PARQUET = ROOT.parent / "data" / "features_with_anomaly.parquet"
MODEL_DIR = ROOT.parent / "models" / "anomaly"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)

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
iso_params = {
    "n_estimators": 200,
    "contamination": 0.02,
    "random_state": SEED
}
iso = IsolationForest(**iso_params)
iso.fit(Xs)

# Predict: sklearn returns 1 normal, -1 anomaly -> convert to 0/1
if_pred = iso.predict(Xs)
df["IF_Anomaly"] = (if_pred == -1).astype(int)
anomaly_rate = float(df["IF_Anomaly"].mean())

# Optional evaluation if ground-truth Anomaly label exists
metrics = {
    "anomaly_rate": anomaly_rate,
    "precision": None,
    "recall": None,
    "f1": None
}
conf_mat = None
label_col = "Anomaly" if "Anomaly" in df.columns else None
if label_col:
    y_true = df[label_col].fillna(0).astype(int)
    y_pred = df["IF_Anomaly"].astype(int)
    metrics["precision"] = precision_score(y_true, y_pred, zero_division=0)
    metrics["recall"] = recall_score(y_true, y_pred, zero_division=0)
    metrics["f1"] = f1_score(y_true, y_pred, zero_division=0)
    conf_mat = confusion_matrix(y_true, y_pred)
    print("Anomaly ground-truth available -> logging metrics")
    print("Precision:", metrics["precision"])
    print("Recall:", metrics["recall"])
    print("F1:", metrics["f1"])

# Save artifacts
joblib.dump(iso, os.path.join(MODEL_DIR, "isolation_forest.joblib"))
joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))
joblib.dump(FEATURES, os.path.join(MODEL_DIR, "isofeat.joblib"))
df.to_parquet(OUT_PARQUET, index=False)

print("Saved:", OUT_PARQUET)
print("Models saved to:", MODEL_DIR)
print("IF anomaly rate:", anomaly_rate)

# MLflow logging (separate run for anomaly training)
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT", "predictive-maintenance"))
with mlflow.start_run(run_name="anomaly", nested=True):
    mlflow.log_params({
        "model": "IsolationForest",
        **iso_params,
        "feature_count": len(FEATURES)
    })
    mlflow.log_metrics({k: v for k, v in metrics.items() if v is not None})
    if conf_mat is not None:
        cm_path = MODEL_DIR / "confusion_matrix_anomaly.csv"
        pd.DataFrame(conf_mat, columns=["pred_normal", "pred_anomaly"], index=["true_normal", "true_anomaly"]).to_csv(cm_path)
        mlflow.log_artifact(cm_path)


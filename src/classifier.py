# src/classifier.py
# Trains a classifier to predict Maintenance_Type (preferred).
# If Maintenance_Type missing, falls back to supervised 'Anomaly' column (if present),
# otherwise uses the generated IF_Anomaly label (unsupervised -> supervised fallback).

import os
import random
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    f1_score,
    recall_score,
    confusion_matrix
)
from sklearn.utils.class_weight import compute_class_weight
import mlflow

SEED = 42


def set_seed(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


set_seed()

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
Xtr, Xte, ytr, yte = train_test_split(
    Xs,
    y,
    test_size=0.2,
    random_state=SEED,
    stratify=y if len(np.unique(y)) > 1 else None
)

# Handle class imbalance with class weights (only if >1 class)
sample_weight = None
if len(np.unique(ytr)) > 1:
    class_weights = compute_class_weight(class_weight="balanced", classes=np.unique(ytr), y=ytr)
    weight_map = {cls: w for cls, w in zip(np.unique(ytr), class_weights)}
    sample_weight = np.array([weight_map[label] for label in ytr])
    print("Computed class weights:", weight_map)

# Train a fast XGBoost classifier
clf_params = {
    "n_estimators": 150,
    "max_depth": 4,
    "learning_rate": 0.12,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "eval_metric": "mlogloss",
    "tree_method": "hist",
    "random_state": SEED
}
clf = XGBClassifier(**clf_params)
clf.fit(Xtr, ytr, sample_weight=sample_weight)

pred = clf.predict(Xte)
acc = accuracy_score(yte, pred)
report = classification_report(yte, pred, zero_division=1, output_dict=True)
macro_f1 = report.get("macro avg", {}).get("f1-score", 0.0)

# Fault recall (treat anything != normal_label as fault)
fault_mask = yte != normal_label
fault_recall = None
if fault_mask.any():
    fault_recall = recall_score(
        (yte != normal_label).astype(int),
        (pred != normal_label).astype(int),
        zero_division=0
    )

print("Classifier accuracy:", acc)
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

# Persist diagnostics
conf_mat = confusion_matrix(yte, pred)
cm_path = os.path.join(MODEL_DIR, "confusion_matrix_classifier.csv")
pd.DataFrame(conf_mat).to_csv(cm_path, index=False)

# MLflow logging
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT", "predictive-maintenance"))
with mlflow.start_run(run_name="classifier"):
    mlflow.log_params({
        **clf_params,
        "feature_count": len(features),
        "label_col": label_col
    })
    mlflow.log_metrics({
        "accuracy": acc,
        "macro_f1": macro_f1,
        "fault_recall": fault_recall if fault_recall is not None else 0.0
    })
    mlflow.log_artifact(cm_path)

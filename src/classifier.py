"""
Fault Classification Model Training
Trains an XGBoost classifier to predict maintenance types or fault categories.

Label priority:
1. Maintenance_Type (preferred)
2. Anomaly (if Maintenance_Type missing)
3. IF_Anomaly (if both missing - from anomaly detection)
"""
import os
import random
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from xgboost import XGBClassifier

# Configuration
SEED = 42

# Paths
ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "data" / "EV_Predictive_Maintenance_Dataset_15min.csv"
PARQUET_PATH = ROOT.parent / "data" / "features_with_anomaly.parquet"
MODEL_DIR = ROOT.parent / "models" / "classifier"

# Features for classification
FEATURES = [
    "SoC", "SoH", "Battery_Voltage", "Battery_Current", "Battery_Temperature",
    "Charge_Cycles", "Motor_Temperature", "Motor_Vibration", "Motor_Torque",
    "Motor_RPM", "Power_Consumption", "Brake_Pad_Wear", "Brake_Pressure",
    "Reg_Brake_Efficiency", "Tire_Pressure", "Tire_Temperature", "Suspension_Load",
    "Ambient_Temperature", "Ambient_Humidity", "Load_Weight", "Driving_Speed",
    "Distance_Traveled", "Idle_Time", "Route_Roughness", "Component_Health_Score",
    "Failure_Probability", "TTF",
]

# Label candidates (in priority order)
LABEL_CANDIDATES = ["Maintenance_Type", "Anomaly", "IF_Anomaly"]


def set_seed(seed: int = SEED) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def main():
    """Main training function."""
    # Set seed for reproducibility
    set_seed()

    # Create model directory
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Load data (prefer parquet with IF_Anomaly labels)
    if PARQUET_PATH.exists():
        df = pd.read_parquet(PARQUET_PATH)
        print(f"Loaded annotated data: {PARQUET_PATH}")
    else:
        df = pd.read_csv(CSV_PATH)
        print(f"Loaded CSV: {CSV_PATH}")

    # Determine label column (priority order)
    label_col = next((c for c in LABEL_CANDIDATES if c in df.columns), None)
    if label_col is None:
        raise RuntimeError(
            "No suitable label found. Expected one of: Maintenance_Type, Anomaly, or IF_Anomaly"
        )

    print(f"Training classifier using label: {label_col}")

    # Filter available features
    available_features = [f for f in FEATURES if f in df.columns]
    if not available_features:
        raise RuntimeError("No numeric features available for classifier.")

    # Prepare features and labels
    X = df[available_features].fillna(0.0).astype(float)
    y_raw = df[label_col].copy()

    # Encode labels if needed
    label_encoder = None
    if y_raw.dtype == object or not np.issubdtype(y_raw.dtype, np.number):
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(y_raw.astype(str))
    else:
        y = y_raw.astype(int).values

    # Identify normal label (most frequent class)
    unique_labels, counts = np.unique(y, return_counts=True)
    normal_label = unique_labels[np.argmax(counts)]
    print(f"Inferred normal label (most frequent class): {normal_label}")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled,
        y,
        test_size=0.2,
        random_state=SEED,
        stratify=y if len(unique_labels) > 1 else None,
    )

    # Handle class imbalance with class weights
    sample_weight = None
    unique_train_labels = np.unique(y_train)
    if len(unique_train_labels) > 1:
        class_weights = compute_class_weight(
            class_weight="balanced",
            classes=unique_train_labels,
            y=y_train,
        )
        weight_map = {cls: w for cls, w in zip(unique_train_labels, class_weights)}
        sample_weight = np.array([weight_map[label] for label in y_train])
        print(f"Computed class weights: {weight_map}")

    # Train XGBoost classifier
    clf_params = {
        "n_estimators": 150,
        "max_depth": 4,
        "learning_rate": 0.12,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "eval_metric": "mlogloss",
        "tree_method": "hist",
        "random_state": SEED,
    }
    clf = XGBClassifier(**clf_params)
    clf.fit(X_train, y_train, sample_weight=sample_weight)

    # Evaluate
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, zero_division=1, output_dict=True)
    macro_f1 = report.get("macro avg", {}).get("f1-score", 0.0)

    # Calculate fault recall (treat anything != normal_label as fault)
    fault_recall = None
    fault_mask = y_test != normal_label
    if fault_mask.any():
        fault_recall = recall_score(
            fault_mask.astype(int),
            (y_pred != normal_label).astype(int),
            zero_division=0,
        )

    print(f"Classifier accuracy: {accuracy:.4f}")
    print(classification_report(y_test, y_pred, zero_division=1))

    # Save artifacts
    joblib.dump(clf, MODEL_DIR / "classifier.joblib")
    joblib.dump(scaler, MODEL_DIR / "scaler.joblib")
    joblib.dump(available_features, MODEL_DIR / "features.joblib")
    joblib.dump(label_col, MODEL_DIR / "label_col.joblib")
    joblib.dump(normal_label, MODEL_DIR / "normal_label.joblib")
    if label_encoder is not None:
        joblib.dump(label_encoder, MODEL_DIR / "label_encoder.joblib")

    print(f"Saved classifier artifacts to {MODEL_DIR}")

    # Save confusion matrix
    conf_mat = confusion_matrix(y_test, y_pred)
    cm_path = MODEL_DIR / "confusion_matrix_classifier.csv"
    pd.DataFrame(conf_mat).to_csv(cm_path, index=False)

    # Log to MLflow
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:6969"))
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT", "predictive-maintenance"))

    with mlflow.start_run(run_name="classifier"):
        dataset_name = CSV_PATH.stem
        mlflow.set_tag("dataset", dataset_name)
        mlflow.set_tag("model", "XGBoost")

        mlflow.log_params({
            **clf_params,
            "feature_count": len(available_features),
            "label_col": label_col,
        })
        mlflow.log_metrics({
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "fault_recall": fault_recall if fault_recall is not None else 0.0,
        })
        mlflow.log_artifact(str(cm_path))


if __name__ == "__main__":
    main()

"""
Remaining Useful Life (RUL) Prediction Model Training
Trains a LightGBM regressor to predict remaining useful life of EV components.

Uses numeric features plus optionally encoded Maintenance_Type from classifier.
"""
import os
import random
from math import sqrt
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Configuration
SEED = 42

# Paths
ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "data" / "EV_Predictive_Maintenance_Dataset_15min.csv"
PARQUET_PATH = ROOT.parent / "data" / "features_with_anomaly.parquet"
MODEL_DIR = ROOT.parent / "models" / "rul"
CLASSIFIER_MODEL_DIR = ROOT.parent / "models" / "classifier"

# Features for RUL prediction
FEATURES = [
    "SoC", "SoH", "Battery_Voltage", "Battery_Current", "Battery_Temperature",
    "Charge_Cycles", "Motor_Temperature", "Motor_Vibration", "Motor_Torque",
    "Motor_RPM", "Power_Consumption", "Brake_Pad_Wear", "Brake_Pressure",
    "Reg_Brake_Efficiency", "Tire_Pressure", "Tire_Temperature", "Suspension_Load",
    "Ambient_Temperature", "Ambient_Humidity", "Load_Weight", "Driving_Speed",
    "Distance_Traveled", "Idle_Time", "Route_Roughness", "Component_Health_Score",
    "Failure_Probability", "TTF",
]


def set_seed(seed: int = SEED) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def load_classifier_label_info() -> tuple[str | None, LabelEncoder | None]:
    """
    Load label column name and encoder from classifier model if available.
    
    Returns:
        Tuple of (label_col_name, label_encoder) or (None, None) if not found
    """
    label_col_path = CLASSIFIER_MODEL_DIR / "label_col.joblib"
    label_encoder_path = CLASSIFIER_MODEL_DIR / "label_encoder.joblib"
    
    if not label_col_path.exists():
        return None, None
    
    label_col = joblib.load(label_col_path)
    
    if label_encoder_path.exists():
        label_encoder = joblib.load(label_encoder_path)
    else:
        label_encoder = None
    
    return label_col, label_encoder


def add_encoded_label_feature(
    df: pd.DataFrame,
    label_col: str,
    label_encoder: LabelEncoder | None,
) -> str | None:
    """
    Add encoded label column as a feature for RUL prediction.
    
    Args:
        df: DataFrame to modify
        label_col: Name of the label column
        label_encoder: LabelEncoder to use (or None to create new one)
    
    Returns:
        Name of the encoded label column if added, None otherwise
    """
    if label_col not in df.columns:
        return None
    
    if label_encoder is None:
        # Create new encoder if not provided
        label_encoder = LabelEncoder()
        df[label_col] = label_encoder.fit_transform(df[label_col].astype(str))
        # Save encoder for future use
        CLASSIFIER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(label_encoder, CLASSIFIER_MODEL_DIR / "label_encoder.joblib")
    else:
        # Use existing encoder
        df[label_col] = label_encoder.transform(df[label_col].astype(str))
    
    return label_col


def main() -> None:
    """Main training function."""
    # Set seed for reproducibility
    set_seed()

    # Create model directory
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Load data (prefer annotated parquet with IF_Anomaly labels)
    if PARQUET_PATH.exists():
        df = pd.read_parquet(PARQUET_PATH)
        print(f"Loaded annotated data: {PARQUET_PATH}")
    else:
        df = pd.read_csv(CSV_PATH)
        print(f"Loaded CSV: {CSV_PATH}")

    # Validate RUL target exists
    if "RUL" not in df.columns:
        raise RuntimeError("Column 'RUL' not found in dataset. Cannot train RUL model.")

    # Filter available features
    available_features = [f for f in FEATURES if f in df.columns]
    
    # Optionally add encoded Maintenance_Type as feature
    label_col, label_encoder = load_classifier_label_info()
    if label_col:
        encoded_label = add_encoded_label_feature(df, label_col, label_encoder)
        if encoded_label and encoded_label not in available_features:
            available_features.append(encoded_label)
            print(f"Added encoded label feature: {encoded_label}")

    if not available_features:
        raise RuntimeError("No features available for RUL training.")

    # Prepare features and target
    X = df[available_features].fillna(0.0).astype(float)
    y = df["RUL"].astype(float)

    # Train-test split for evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=SEED
    )

    # Train LightGBM model
    model_params = {
        "n_estimators": 400,
        "learning_rate": 0.05,
        "random_state": SEED,
    }
    model = LGBMRegressor(**model_params)
    model.fit(X_train, y_train)

    # Evaluate on test set
    y_pred = model.predict(X_test)
    rmse = sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"RUL model RMSE (val): {rmse:.4f}")
    print(f"RUL model MAE (val): {mae:.4f}")
    print(f"RUL model R² (val): {r2:.4f}")

    # Re-fit on full dataset for deployment
    model.fit(X, y)

    # Save model and features
    joblib.dump(model, MODEL_DIR / "lgbm_rul.joblib")
    joblib.dump(available_features, MODEL_DIR / "rul_features.joblib")

    print(f"Saved RUL model & feature list to {MODEL_DIR}")

    # Log to MLflow
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:6969"))
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT", "predictive-maintenance"))

    with mlflow.start_run(run_name="rul"):
        dataset_name = CSV_PATH.stem
        mlflow.set_tag("dataset", dataset_name)
        mlflow.set_tag("model", "LightGBM")

        mlflow.log_params({
            **model_params,
            "feature_count": len(available_features),
        })
        mlflow.log_metrics({
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
        })


if __name__ == "__main__":
    main()

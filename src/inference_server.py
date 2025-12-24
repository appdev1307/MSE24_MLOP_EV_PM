# src/inference_server.py
# FastAPI server: IsolationForest → Classifier → RUL (if fault)

import os
import joblib
import numpy as np
import mlflow
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import tempfile

# Prometheus instrumentation
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

# Custom counters for alerting
PREDICTIONS_TOTAL = Counter(
    "predictions_total",
    "Total number of inference predictions made"
)
ANOMALY_PREDICTIONS = Counter(
    "anomaly_predictions_total",
    "Number of times anomaly was detected (IF_Anomaly == 1)"
)

# ==============================
# MLflow Config
# ==============================
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")

MODEL_NAMES = {
    "anomaly": "ev-anomaly-model",
    "classifier": "ev-classifier-model",
    "rul": "ev-rul-model",
}

mlflow.set_tracking_uri(MLFLOW_URI)

# Cache directory for downloaded models
MODEL_CACHE_DIR = os.path.join(tempfile.gettempdir(), "mlflow_ev_models")
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

# ==============================
# Download production model (@production alias)
# ==============================
def download_production_model(model_name: str):
    """Download the @production version. Files are directly in the root."""
    model_uri = f"models:/{model_name}@production"
    local_dir = os.path.join(MODEL_CACHE_DIR, model_name)

    try:
        print(f"⬇️ Downloading {model_name}@production ...")
        downloaded_path = mlflow.artifacts.download_artifacts(
            artifact_uri=model_uri,
            dst_path=local_dir
        )
        print(f"✅ Model downloaded to: {downloaded_path}")
        return downloaded_path
    except Exception as e:
        print(f"❌ Failed to download {model_name}@production: {e}")
        return None

# Download all models at startup
print("⬇️ Downloading models from MLflow (@production)...")
anomaly_dir = download_production_model(MODEL_NAMES["anomaly"])
classifier_dir = download_production_model(MODEL_NAMES["classifier"])
rul_dir = download_production_model(MODEL_NAMES["rul"])

# ==============================
# Safe load helper
# ==============================
def safe_load(directory: str | None, filename: str, name: str):
    if directory is None:
        print(f"   Missing directory for {name}")
        return None
    path = os.path.join(directory, filename)
    if os.path.exists(path):
        print(f"   Loaded {name}: {filename}")
        return joblib.load(path)
    else:
        print(f"   Missing {name}: {filename} (not found)")
        return None

# Load Anomaly components
isof = safe_load(anomaly_dir, "isolation_forest.joblib", "IsolationForest")
if_scaler = safe_load(anomaly_dir, "scaler.joblib", "Anomaly Scaler")
if_features = safe_load(anomaly_dir, "isofeat.joblib", "Anomaly Features")

# Load Classifier components
clf = safe_load(classifier_dir, "classifier.joblib", "Classifier")
clf_scaler = safe_load(classifier_dir, "scaler.joblib", "Classifier Scaler")
clf_features = safe_load(classifier_dir, "features.joblib", "Classifier Features")
clf_label_encoder = safe_load(classifier_dir, "label_encoder.joblib", "Label Encoder")
clf_normal_label = safe_load(classifier_dir, "normal_label.joblib", "Normal Label")

# Load RUL components
rul_model = safe_load(rul_dir, "lgbm_rul.joblib", "RUL Model")
rul_features = safe_load(rul_dir, "rul_features.joblib", "RUL Features")

# ==============================
# FastAPI App
# ==============================
app = FastAPI(title="EV Predictive Maintenance Inference")

# Enable Prometheus metrics at /metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

class Payload(BaseModel):
    data: dict

def _build_row(feature_list, data):
    return np.array([float(data.get(f, 0.0)) for f in feature_list]).reshape(1, -1)

@app.post("/predict")
def predict(payload: Payload):
    data = payload.data

    # Increment total predictions
    PREDICTIONS_TOTAL.inc()

    result = {}

    # 1. Anomaly Detection
    if isof is None or if_scaler is None or if_features is None:
        return {"error": "Anomaly model/scaler/features missing in @production."}

    try:
        x_if = _build_row(if_features, data)
        x_if_scaled = if_scaler.transform(x_if)
        if_pred = isof.predict(x_if_scaled)[0]
        is_anomaly = int(if_pred == -1)

        if is_anomaly == 1:
            ANOMALY_PREDICTIONS.inc()
    except Exception as e:
        return {"error": f"Anomaly inference error: {str(e)}"}

    result["IF_Anomaly"] = is_anomaly

    if is_anomaly == 0:
        result["status"] = "Normal - no fault detected"
        return result

    # 2. Classifier
    if clf is None or clf_scaler is None or clf_features is None:
        result["classifier"] = "not available"
        return result

    try:
        x_clf = _build_row(clf_features, data)
        x_clf_scaled = clf_scaler.transform(x_clf)
        clf_pred = clf.predict(x_clf_scaled)[0]
        label_name = (
            clf_label_encoder.inverse_transform([int(clf_pred)])[0]
            if clf_label_encoder is not None else str(clf_pred)
        )
    except Exception as e:
        return {"error": f"Classifier inference error: {str(e)}"}

    result.update({
        "classifier_label_code": int(clf_pred),
        "classifier_label_name": label_name
    })

    normal_code = int(clf_normal_label) if clf_normal_label is not None else 0
    is_fault = int(clf_pred) != normal_code
    result["is_fault"] = is_fault

    # 3. RUL if fault
    if is_fault:
        if rul_model is None or rul_features is None:
            result["RUL"] = "not available"
            return result
        try:
            x_rul = _build_row(rul_features, data)
            rul_pred = float(rul_model.predict(x_rul)[0])
            result["RUL_estimated"] = rul_pred
        except Exception as e:
            result["RUL_error"] = str(e)
    else:
        result["RUL_estimated"] = "not_applicable"

    return result

# ==============================
# Startup
# ==============================
if __name__ == "__main__":
    print("\n🚀 Starting inference server...")
    print(f"   Anomaly model loaded: {bool(isof)}")
    print(f"   Classifier loaded: {bool(clf)}")
    print(f"   RUL model loaded: {bool(rul_model)}")
    uvicorn.run("src.inference_server:app", host="0.0.0.0", port=8000, reload=False)
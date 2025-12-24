import os
import time
import socket
import json
import joblib
import numpy as np
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import Response
from pydantic import BaseModel

from confluent_kafka import Producer

import mlflow
from mlflow.tracking import MlflowClient

# =======================
# PROMETHEUS
# =======================
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# ============================================================
# ---------------------- MLFLOW CONFIG ------------------------
# ============================================================

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_URI)

# 🔴 FIX IS HERE
client = MlflowClient(tracking_uri=MLFLOW_URI)

CACHE_DIR = "/tmp/models"
os.makedirs(CACHE_DIR, exist_ok=True)

def load_joblib_from_registry(model_name: str, artifact_name: str):
    """
    Load raw artifact (.joblib) from MLflow Registry (Production)
    """
    mv = client.get_latest_versions(model_name, stages=["Production"])[0]
    local_path = client.download_artifacts(
        run_id=mv.run_id,
        path=f"{model_name}/{artifact_name}",
        dst_path=CACHE_DIR
    )
    return joblib.load(local_path)

# ============================================================
# ----------------------- LOAD MODELS -------------------------
# ============================================================

try:
    print("✅ Loading models from MLflow Registry (Production)")

    isof = load_joblib_from_registry(
        "ev-anomaly-model", "isolation_forest.joblib"
    )
    clf_model = load_joblib_from_registry(
        "ev-classifier-model", "classifier.joblib"
    )
    rul_model = load_joblib_from_registry(
        "ev-rul-model", "lgbm_rul.joblib"
    )

    print("✅ Models loaded successfully")

except Exception as e:
    print(f"❌ Failed to load models from MLflow Registry: {e}")
    isof = clf_model = rul_model = None

# ============================================================
# ---------------------- FASTAPI APP --------------------------
# ============================================================

app = FastAPI(title="EV Predictive Maintenance Inference API")

REQUEST_COUNT = Counter("inference_requests_total", "Total inference requests")
REQUEST_LATENCY = Histogram("inference_latency_seconds", "Inference latency")

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    REQUEST_COUNT.inc()
    REQUEST_LATENCY.observe(time.time() - start)
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ============================================================
# ---------------------- SCHEMA -------------------------------
# ============================================================

class Payload(BaseModel):
    data: Dict[str, Any]

# ============================================================
# ---------------------- ENDPOINT -----------------------------
# ============================================================

@app.post("/predict")
def predict(payload: Payload):

    if isof is None:
        return {"error": "Anomaly model not available"}

    data = payload.data
    X = np.array([list(data.values())], dtype=float)

    is_anomaly = int(isof.predict(X)[0] == -1)
    result = {"IF_Anomaly": is_anomaly}

    if is_anomaly == 0:
        result["status"] = "Normal - no fault detected"
        return result

    label = int(clf_model.predict(X)[0])
    result["classifier_label"] = label
    result["is_fault"] = True
    result["RUL_estimated"] = float(rul_model.predict(X)[0])

    return result

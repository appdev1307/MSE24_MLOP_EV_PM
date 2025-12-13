import os
import time
import socket
import joblib
import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any, List
from confluent_kafka import Producer

# =======================
# MONITORING (ADDED ONLY)
# =======================
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)

# ============================================================
# ----------------------- LOAD MODELS -------------------------
# ============================================================

def load_or_none(path):
    return joblib.load(path) if os.path.exists(path) else None

MODEL_DIR = "models"

# ---- Anomaly (Isolation Forest) ----
isof = load_or_none(f"{MODEL_DIR}/anomaly/isolation_forest.joblib")
if_scaler = load_or_none(f"{MODEL_DIR}/anomaly/scaler.joblib")
if_features = load_or_none(f"{MODEL_DIR}/anomaly/isofeat.joblib")

# ---- Classifier ----
clf_model = load_or_none(f"{MODEL_DIR}/classifier/classifier.joblib")
clf_scaler = load_or_none(f"{MODEL_DIR}/classifier/scaler.joblib")
clf_features = load_or_none(f"{MODEL_DIR}/classifier/features.joblib")
clf_label_encoder = load_or_none(f"{MODEL_DIR}/classifier/label_encoder.joblib")

# ---- RUL Predictor ----
rul_model = load_or_none(f"{MODEL_DIR}/rul/lgbm_rul.joblib")
rul_features = load_or_none(f"{MODEL_DIR}/rul/rul_features.joblib")

# ---- Meaningful labels mapping ----
FAULT_MAP = {
    0: "Battery Aging",
    1: "Thermal Runaway Risk",
    2: "Motor Overheat",
    3: "Brake System Failure",
    4: "Sensor Drift"
}

# ============================================================
# ---------------------- KAFKA CONFIG -------------------------
# ============================================================

KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = "ev_predictions"

kafka_producer = None
kafka_enabled = True
try:
    kafka_producer = Producer({"bootstrap.servers": KAFKA_SERVER})
except Exception as e:
    kafka_producer = None
    kafka_enabled = False
    print(f"[WARN] Kafka producer init failed, disabled: {e}")

# ============================================================
# ---------------------- FASTAPI APP --------------------------
# ============================================================

app = FastAPI(title="EV Predictive Maintenance Inference API")

# =======================
# MONITORING METRICS
# =======================

REQUEST_COUNT = Counter(
    "inference_requests_total",
    "Total number of inference requests"
)

REQUEST_LATENCY = Histogram(
    "inference_request_latency_seconds",
    "Inference request latency in seconds"
)

ANOMALY_PREDICTIONS = Counter(
    "anomaly_predictions_total",
    "Total anomaly predictions"
)

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    REQUEST_COUNT.inc()
    REQUEST_LATENCY.observe(time.time() - start_time)
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
# ------------------- HELPERS --------------------------------
# ============================================================

def _build_row(feature_list: List[str], input_data: Dict[str, Any]):
    return np.array([[float(input_data.get(f, 0)) for f in feature_list]])

def kafka_send_prediction(data: Dict[str, Any]):
    if not kafka_enabled or kafka_producer is None:
        print("[WARN] Kafka disabled or not reachable; skipping send.")
        return
    try:
        kafka_producer.produce(KAFKA_TOPIC, value=str(data))
    except Exception as e:
        print(f"[WARN] Kafka send failed (non-blocking): {e}")

# ============================================================
# ------------------------- ENDPOINT --------------------------
# ============================================================

@app.post("/predict")
def predict(payload: Payload):

    data = payload.data
    result = {}

    # ========================================================
    # 1) Anomaly Detection
    # ========================================================
    if isof is None or if_scaler is None or if_features is None:
        return {"error": "Anomaly model/scaler/features missing. Run anomaly pipeline first."}

    try:
        x_if = _build_row(if_features, data)
        x_if_scaled = if_scaler.transform(x_if)
        if_pred = isof.predict(x_if_scaled)[0]  # 1 normal, -1 anomaly
        is_anomaly = int(if_pred == -1)
    except Exception as e:
        return {"error": f"Anomaly inference error: {e}"}

    result["IF_Anomaly"] = is_anomaly

    # =======================
    # MONITORING HOOK (ONLY)
    # =======================
    if is_anomaly == 1:
        ANOMALY_PREDICTIONS.inc()

    # ========================================================
    # RULE OVERRIDE: Battery Aging
    # ========================================================
    if is_anomaly == 0:
        soh = float(data.get("SoH", 1))
        cycles = float(data.get("Charge_Cycles", 0))

        if soh < 0.6 or cycles > 2000:
            is_anomaly = 1
            result["IF_Anomaly"] = 1
            ANOMALY_PREDICTIONS.inc()
        else:
            result["status"] = "Normal - no fault detected"
            return result

    # ========================================================
    # 2) Fault Classification
    # ========================================================
    classifier_label = None
    is_fault = False

    if clf_model and clf_scaler and clf_features:
        try:
            x_clf = _build_row(clf_features, data)
            x_clf_scaled = clf_scaler.transform(x_clf)
            pred_code = clf_model.predict(x_clf_scaled)[0]
            classifier_label = FAULT_MAP.get(int(pred_code), str(pred_code))
            is_fault = True
        except Exception as e:
            classifier_label = f"Classifier Error: {e}"
    else:
        classifier_label = "Classifier unavailable"

    result["classifier_label"] = classifier_label
    result["is_fault"] = is_fault

    # ========================================================
    # 3) RUL Prediction
    # ========================================================
    rul_value = None
    if is_fault and rul_model and rul_features:
        try:
            x_rul = _build_row(rul_features, data)
            rul_value = float(rul_model.predict(x_rul)[0])
        except Exception:
            rul_value = None

    result["RUL_estimated"] = rul_value

    # ========================================================
    # 4) Kafka Event - Only push alerts
    # ========================================================
    alert_payload = {
        "timestamp": int(time.time()),
        "host": socket.gethostname(),
        "input": payload.data,
        "prediction": {
            "IF_Anomaly": is_anomaly,
            "classifier_label": classifier_label,
            "is_fault": bool(is_fault),
            "RUL_estimated": float(rul_value) if rul_value is not None else None
        }
    }

    if is_anomaly == 1 or is_fault:
        kafka_send_prediction(alert_payload)

    return result

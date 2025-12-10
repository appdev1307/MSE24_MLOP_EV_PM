# src/inference_server.py
# FastAPI server implementing: IsolationForest -> Classifier -> RUL (if fault)
import os
import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from confluent_kafka import Producer
import socket
import json


# Use paths relative to project root (run from repo root)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.path.dirname(os.path.abspath(__file__))

# Model artifact paths
IF_MODEL = os.path.join("models", "anomaly", "isolation_forest.joblib")
IF_SCALER = os.path.join("models", "anomaly", "scaler.joblib")
IF_FEAT = os.path.join("models", "anomaly", "isofeat.joblib")

CLF_MODEL = os.path.join("models", "classifier", "classifier.joblib")
CLF_SCALER = os.path.join("models", "classifier", "scaler.joblib")
CLF_FEAT = os.path.join("models", "classifier", "features.joblib")
CLF_LABEL = os.path.join("models", "classifier", "label_col.joblib")
CLF_LABEL_ENCODER = os.path.join("models", "classifier", "label_encoder.joblib")
CLF_NORMAL = os.path.join("models", "classifier", "normal_label.joblib")

RUL_MODEL = os.path.join("models", "rul", "lgbm_rul.joblib")
RUL_FEAT = os.path.join("models", "rul", "rul_features.joblib")

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
PRED_TOPIC = os.environ.get("PRED_TOPIC", "predictions")

producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP})

def kafka_send_prediction(payload: dict):
    try:
        producer.produce(PRED_TOPIC, json.dumps(payload).encode("utf-8"))
        producer.poll(0)  # flush callback
    except Exception as e:
        print("Kafka produce error:", e)


# safe loads
def safe_load(path):
    return joblib.load(path) if os.path.exists(path) else None

isof = safe_load(IF_MODEL)
if_scaler = safe_load(IF_SCALER)
if_features = safe_load(IF_FEAT)

clf = safe_load(CLF_MODEL)
clf_scaler = safe_load(CLF_SCALER)
clf_features = safe_load(CLF_FEAT)
clf_label_col = safe_load(CLF_LABEL)
clf_label_encoder = safe_load(CLF_LABEL_ENCODER)
clf_normal_label = safe_load(CLF_NORMAL)

rul_model = safe_load(RUL_MODEL)
rul_features = safe_load(RUL_FEAT)

app = FastAPI(title="EV Predictive Maintenance Inference")

# Input schema: accept flexible dict of features (we'll pick the ones needed)
class Payload(BaseModel):
    data: dict  # keys are column names and values are numeric (or Vehicle identifier)

def _build_row(feature_list, data):
    # returns np.array shaped (1, n)
    return np.array([float(data.get(f, 0.0)) for f in feature_list]).reshape(1, -1)

@app.post("/predict")
def predict(payload: Payload):
    data = payload.data

    # 1) Anomaly detection (must exist)
    if isof is None or if_scaler is None or if_features is None:
        return {"error": "Anomaly model/scaler/features missing. Run src/anomaly.py first."}

    try:
        x_if = _build_row(if_features, data)
        x_if_scaled = if_scaler.transform(x_if)
        if_pred = isof.predict(x_if_scaled)[0]  # 1 normal, -1 anomaly
        is_anomaly = int(if_pred == -1)
    except Exception as e:
        return {"error": f"Anomaly inference error: {e}"}

    result = {"IF_Anomaly": is_anomaly}

    # If no anomaly -> return normal
    if is_anomaly == 0:
        result.update({"status": "Normal - no fault detected"})
        return result

    # 2) Classifier (must exist)
    if clf is None or clf_scaler is None or clf_features is None:
        # classifier missing -> return anomaly only
        result.update({"classifier": "not available"})
        return result

    try:
        x_clf = _build_row(clf_features, data)
        x_clf_scaled = clf_scaler.transform(x_clf)
        clf_pred = clf.predict(x_clf_scaled)[0]
        # decode label if encoder exists
        if clf_label_encoder:
            label_name = clf_label_encoder.inverse_transform([int(clf_pred)])[0]
        else:
            label_name = str(clf_pred)
    except Exception as e:
        return {"error": f"Classifier inference error: {e}"}

    result.update({"classifier_label_code": int(clf_pred), "classifier_label_name": label_name})

    # decide if this class indicates a fault (anything not equal to the normal_label)
    try:
        normal_code = int(clf_normal_label) if clf_normal_label is not None else None
    except:
        normal_code = None

    is_fault = True
    if normal_code is not None:
        is_fault = (int(clf_pred) != normal_code)
    else:
        # if we don't know normal code, treat any non-zero numeric as fault
        try:
            is_fault = int(clf_pred) != 0
        except:
            is_fault = True

    result["is_fault"] = bool(is_fault)

    # 3) If fault -> RUL (if available)
    if is_fault:
        if rul_model is None or rul_features is None:
            result.update({"RUL": "not available"})
            return result
        try:
            x_rul = _build_row(rul_features, data)
            rul_pred = float(rul_model.predict(x_rul)[0])
            result.update({"RUL_estimated": float(rul_pred)})
        except Exception as e:
            result.update({"RUL_error": str(e)})
    else:
        result.update({"RUL_estimated": "not_applicable"})

    payload_kafka = {
        "timestamp": int(time.time()),
        "host": socket.gethostname(),
        "input": payload.data,
        "prediction": {
            "IF_Anomaly": int(pred_if),
            "classifier_label": classifier_label,
            "is_fault": bool(is_fault),
            "RUL_estimated": float(rul_value)
        }
    }

    kafka_send_prediction(payload_kafka)


    return result

if __name__ == "__main__":
    print("Loaded models? IF:", bool(isof), "CLF:", bool(clf), "RUL:", bool(rul_model))
    uvicorn.run("src.inference_server:app", host="0.0.0.0", port=8000, reload=False)

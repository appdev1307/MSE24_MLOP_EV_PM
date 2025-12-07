# src/inference_server_docker.py
import os
import sys
import json
import logging
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import mlflow

# ---- Logging ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("inference_server")

# ---- MLflow ----
MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_URI)

# ---- Artifact paths (local preferred) ----
IF_LOCAL = "models/anomaly/isolation_forest.joblib"
IF_SCALER_LOCAL = "models/anomaly/scaler.joblib"
IF_FEAT_LOCAL = "models/anomaly/isofeat.joblib"

CLF_LOCAL = "models/classifier/classifier.joblib"
CLF_SCALER_LOCAL = "models/classifier/scaler.joblib"
CLF_FEATURES_LOCAL = "models/classifier/features.joblib"
CLF_LABELCOL_LOCAL = "models/classifier/label_col.joblib"
CLF_LABELENC_LOCAL = "models/classifier/label_encoder.joblib"
CLF_NORMAL_LOCAL = "models/classifier/normal_label.joblib"

RUL_LOCAL = "models/rul/lgbm_rul.joblib"
RUL_FEAT_LOCAL = "models/rul/rul_features.joblib"

# ---- Helper: load local joblib or MLflow model ----
def load_local_joblib(path):
    if os.path.exists(path):
        try:
            obj = joblib.load(path)
            logger.info(f"Loaded local joblib: {path}")
            return obj
        except Exception as e:
            logger.error(f"Failed loading joblib {path}: {e}")
    return None

def load_mlflow_model(registered_name):
    try:
        client = mlflow.tracking.MlflowClient()
        # try Production, then Staging, then default
        for stage in ("Production", "Staging", None):
            try:
                versions = client.get_latest_versions(registered_name, stages=[stage]) if stage else client.get_latest_versions(registered_name)
            except Exception:
                versions = []
            if versions:
                ver = versions[0]
                model_uri = f"models:/{registered_name}/{ver.version}"
                logger.info(f"Attempting to load MLflow model: {model_uri}")
                try:
                    # load as pyfunc (generic)
                    py = mlflow.pyfunc.load_model(model_uri)
                    logger.info(f"Loaded MLflow pyfunc model: {registered_name} v{ver.version}")
                    return py
                except Exception as e:
                    logger.error(f"Failed to load mlflow model {model_uri}: {e}")
    except Exception as e:
        logger.error(f"MLflow client error: {e}")
    return None

# ---- Load models (local first, then MLflow by registered names) ----
logger.info("Loading models (local preferred, then MLflow)...")

# Anomaly (IsolationForest)
anomaly_model = load_local_joblib(IF_LOCAL)
anomaly_scaler = load_local_joblib(IF_SCALER_LOCAL)
anomaly_features = load_local_joblib(IF_FEAT_LOCAL)
if anomaly_model is None:
    anomaly_model = load_mlflow_model("ev_anomaly")  # try mlflow registered
    # anomaly_model may be pyfunc wrapper; scaler/features may still be local
    if anomaly_model and anomaly_features is None:
        # try to find features artifact in models directory
        anomaly_features = load_local_joblib(IF_FEAT_LOCAL)

# Classifier
classifier_model = load_local_joblib(CLF_LOCAL)
classifier_scaler = load_local_joblib(CLF_SCALER_LOCAL)
classifier_features = load_local_joblib(CLF_FEATURES_LOCAL)
classifier_label_col = load_local_joblib(CLF_LABELCOL_LOCAL)
classifier_label_encoder = load_local_joblib(CLF_LABELENC_LOCAL)
classifier_normal_label = load_local_joblib(CLF_NORMAL_LOCAL)
if classifier_model is None:
    classifier_model = load_mlflow_model("ev_classifier")

# RUL
rul_model = load_local_joblib(RUL_LOCAL)
rul_features = load_local_joblib(RUL_FEAT_LOCAL)
if rul_model is None:
    rul_model = load_mlflow_model("ev_rul")

logger.info(f"Models loaded: anomaly={bool(anomaly_model)}, classifier={bool(classifier_model)}, rul={bool(rul_model)}")

# ---- FastAPI app ----
app = FastAPI(title="EV Predictive Maintenance Inference")

# ---- Accept both 'data' and 'payload' ----
class PredictRequest(BaseModel):
    data: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None

def pick_input(req: PredictRequest) -> Dict[str, Any]:
    d = req.data if req.data is not None else req.payload
    if d is None:
        raise HTTPException(status_code=400, detail="No input found; provide JSON with 'data' or 'payload' object.")
    return d

def safe_build_vector(features_list, data_dict):
    return np.array([float(data_dict.get(f, 0.0)) for f in features_list]).reshape(1, -1)

@app.get("/health")
def health():
    return {
        "anomaly_loaded": bool(anomaly_model),
        "classifier_loaded": bool(classifier_model),
        "rul_loaded": bool(rul_model)
    }

@app.post("/predict")
def predict(req: PredictRequest):
    data = pick_input(req)
    logger.info(json.dumps({"event": "predict_request", "payload_keys": list(data.keys())}))

    # 1) Anomaly detection
    if anomaly_model is None or anomaly_scaler is None or anomaly_features is None:
        raise HTTPException(status_code=500, detail="Anomaly model/scaler/features not available. Run training or register to MLflow.")

    try:
        x_if = safe_build_vector(anomaly_features, data)
        x_if_scaled = anomaly_scaler.transform(x_if)
        if hasattr(anomaly_model, "predict"):
            # sklearn estimator
            pred_if = anomaly_model.predict(x_if_scaled)[0]
        else:
            # pyfunc (MLflow) -> expects DataFrame
            import pandas as _pd
            df_if = _pd.DataFrame([dict(zip(anomaly_features, x_if.flatten()))])
            pred_if = int(anomaly_model.predict(df_if).values[0])
        is_anomaly = int(pred_if == -1 or pred_if == 1 and pred_if != 0)  # convert various encodings: -1 anomaly, 1 normal -> normalize
        # normalize: if model outputs -1 anomaly else 0 normal
        if pred_if == -1:
            is_anomaly = 1
        elif pred_if == 1 and np.allclose(pred_if, 1):
            # some IF implementations return 1 normal, -1 anomaly
            is_anomaly = 0
    except Exception as e:
        logger.error("Anomaly inference error: " + str(e))
        raise HTTPException(status_code=500, detail=f"Anomaly inference error: {e}")

    result = {"IF_Anomaly": int(is_anomaly)}

    # If no anomaly -> return normal
    if is_anomaly == 0:
        result.update({"status": "Normal - no fault detected"})
        logger.info(json.dumps({"event": "predict_response", "result": result}))
        return result

    # 2) Classifier (must exist)
    if classifier_model is None or classifier_scaler is None or classifier_features is None:
        result.update({"classifier": "not available"})
        logger.info(json.dumps({"event": "predict_response", "result": result}))
        return result

    try:
        x_clf = safe_build_vector(classifier_features, data)
        x_clf_scaled = classifier_scaler.transform(x_clf)
        if hasattr(classifier_model, "predict"):
            clf_pred = classifier_model.predict(x_clf_scaled)[0]
        else:
            import pandas as _pd
            df_clf = _pd.DataFrame([dict(zip(classifier_features, x_clf.flatten()))])
            clf_pred = classifier_model.predict(df_clf).values[0]
        # decode label if encoder exists
        if classifier_label_encoder is not None:
            try:
                label_name = classifier_label_encoder.inverse_transform([int(clf_pred)])[0]
            except Exception:
                label_name = str(clf_pred)
        else:
            label_name = str(clf_pred)
    except Exception as e:
        logger.error("Classifier inference error: " + str(e))
        raise HTTPException(status_code=500, detail=f"Classifier inference error: {e}")

    result.update({"classifier_label_code": int(clf_pred), "classifier_label_name": label_name})

    # decide whether this code means fault (use stored 'normal' label if available)
    is_fault = True
    if classifier_normal_label is not None:
        try:
            is_fault = int(clf_pred) != int(classifier_normal_label)
        except Exception:
            is_fault = True
    else:
        try:
            is_fault = int(clf_pred) != 0
        except Exception:
            is_fault = True

    result["is_fault"] = bool(is_fault)

    # 3) If fault -> RUL (if available)
    if is_fault:
        if rul_model is None or rul_features is None:
            result.update({"RUL": "not available"})
            logger.info(json.dumps({"event": "predict_response", "result": result}))
            return result
        try:
            x_rul = safe_build_vector(rul_features, data)
            if hasattr(rul_model, "predict"):
                rul_pred = float(rul_model.predict(x_rul)[0])
            else:
                import pandas as _pd
                df_rul = _pd.DataFrame([dict(zip(rul_features, x_rul.flatten()))])
                rul_pred = float(rul_model.predict(df_rul).values[0])
            result.update({"RUL_estimated": float(rul_pred)})
        except Exception as e:
            logger.error("RUL inference error: " + str(e))
            result.update({"RUL_error": str(e)})
    else:
        result.update({"RUL_estimated": "not_applicable"})

    logger.info(json.dumps({"event": "predict_response", "result": result}))
    return result

import os
import time
import socket
import joblib
import numpy as np
import subprocess
import threading
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from confluent_kafka import Producer

# =======================
# MONITORING
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

def reload_models():
    """Reload tất cả models từ disk."""
    global isof, if_scaler, if_features
    global clf_model, clf_scaler, clf_features, clf_label_encoder
    global rul_model, rul_features
    
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

app = FastAPI(
    title="EV Predictive Maintenance API",
    description="API cho inference và training models",
    version="1.0.0"
)

# ============================================================
# ---------------------- TRAINING STATE ----------------------
# ============================================================

# Check if running in Docker
IN_DOCKER = os.path.exists("/.dockerenv")
WORKSPACE_DIR = "/workspace" if IN_DOCKER else os.getcwd()

# Training state
training_state = {
    "status": "idle",  # idle, running, completed, failed
    "started_at": None,
    "completed_at": None,
    "log": []
}

TRAINER_SCRIPT = os.getenv("TRAINER_SCRIPT", "src/train_wrapper.py")
USE_DOCKER = os.getenv("USE_DOCKER", "true").lower() == "true"

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

class TrainingRequest(BaseModel):
    """Request model cho training API."""
    force: bool = False
    rebuild: bool = True  # Có build lại Docker image không

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
# ---------------------- TRAINING FUNCTIONS --------------------
# ============================================================

def check_docker_available():
    """Kiểm tra xem docker command có sẵn không."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def run_training(rebuild: bool = True):
    """Chạy training trong background thread."""
    global training_state
    
    training_state["status"] = "running"
    training_state["started_at"] = datetime.now().isoformat()
    training_state["completed_at"] = None
    training_state["log"] = []
    
    try:
        docker_available = check_docker_available()
        
        if USE_DOCKER and docker_available:
            # Chạy training trong Docker container
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": "Starting training in Docker container..."
            })
            
            # Build trainer image nếu cần
            if rebuild:
                build_cmd = ["docker", "compose", "build", "trainer"]
                training_state["log"].append({
                    "timestamp": datetime.now().isoformat(),
                    "message": "Building trainer image..."
                })
                build_process = subprocess.run(
                    build_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=WORKSPACE_DIR,
                    timeout=600  # 10 minutes timeout
                )
                training_state["log"].append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Build output: {build_process.stdout[-500:]}"  # Last 500 chars
                })
            
            # Chạy training trong Docker container
            cmd = ["docker", "compose", "run", "--rm", "trainer"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=WORKSPACE_DIR
            )
        else:
            # Fallback: Chạy training script trực tiếp
            if USE_DOCKER and not docker_available:
                training_state["log"].append({
                    "timestamp": datetime.now().isoformat(),
                    "message": "Docker not available, falling back to direct script execution..."
                })
            
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": f"Running training script directly: {TRAINER_SCRIPT}"
            })
            process = subprocess.Popen(
                ["python", TRAINER_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=WORKSPACE_DIR
            )
        
        # Đọc log real-time
        for line in process.stdout:
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": line.strip()
            })
            # Giữ log không quá 1000 dòng
            if len(training_state["log"]) > 1000:
                training_state["log"] = training_state["log"][-1000:]
        
        process.wait()
        
        if process.returncode == 0:
            training_state["status"] = "completed"
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": "Training completed successfully! Reloading models..."
            })
            # Reload models sau khi training xong
            reload_models()
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": "Models reloaded successfully!"
            })
        else:
            training_state["status"] = "failed"
            training_state["log"].append({
                "timestamp": datetime.now().isoformat(),
                "message": f"Training failed with exit code {process.returncode}"
            })
            
    except Exception as e:
        training_state["status"] = "failed"
        training_state["log"].append({
            "timestamp": datetime.now().isoformat(),
            "message": f"Error: {str(e)}"
        })
    finally:
        training_state["completed_at"] = datetime.now().isoformat()

# ============================================================
# ------------------------- ENDPOINTS --------------------------
# ============================================================

@app.post("/predict")
def predict(payload: Payload):

    data = payload.data
    result = {}

    # ========================================================
    # 1) Anomaly Detection (Isolation Forest)
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

    # ========================================================
    # RULE OVERRIDE: Battery Aging
    # ========================================================
    if is_anomaly == 0:
        soh = float(data.get("SoH", 1))
        cycles = float(data.get("Charge_Cycles", 0))

        if soh < 0.6 or cycles > 2000:
            is_anomaly = 1
            result["IF_Anomaly"] = 1
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
    # FINAL MONITORING HOOK (ONLY PLACE)
    # ========================================================
    if result.get("IF_Anomaly") == 1:
        ANOMALY_PREDICTIONS.inc()

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

# ============================================================
# ---------------------- TRAINING ENDPOINTS --------------------
# ============================================================

@app.post("/api/train")
async def start_training(request: TrainingRequest):
    """
    API endpoint để trigger training job.
    
    - **force**: Nếu True, sẽ bắt đầu training ngay cả khi đang có job đang chạy
    - **rebuild**: Nếu True, sẽ build lại Docker image trước khi chạy training
    """
    global training_state
    
    if training_state["status"] == "running" and not request.force:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Training is already running!",
                "status": training_state["status"],
                "hint": "Use force=true to stop current job and start new one"
            }
        )
    
    # Start training in background thread
    thread = threading.Thread(target=run_training, args=(request.rebuild,), daemon=True)
    thread.start()
    
    return JSONResponse(content={
        "message": "Training started! Check status at /api/training/status",
        "status": "running",
        "rebuild": request.rebuild
    })

@app.get("/api/training/status")
async def get_training_status():
    """API endpoint để lấy training status."""
    return JSONResponse(content=training_state)

@app.get("/api/training/logs")
async def get_training_logs():
    """API endpoint để lấy training logs."""
    return JSONResponse(content={
        "logs": training_state["log"],
        "total": len(training_state["log"])
    })

@app.post("/api/models/reload")
async def reload_models_endpoint():
    """API endpoint để reload models từ disk (sau khi training xong)."""
    try:
        reload_models()
        return JSONResponse(content={
            "message": "Models reloaded successfully!",
            "models_loaded": {
                "anomaly": isof is not None,
                "classifier": clf_model is not None,
                "rul": rul_model is not None
            }
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to reload models: {str(e)}"}
        )

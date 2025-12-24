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
from typing import Dict, Any, List, Optional
from confluent_kafka import Producer
import mlflow
from src.mlflow_utils import (
    load_model_from_registry,
    get_model_info,
    MODEL_NAMES
)

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

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MLFLOW_MODEL_STAGE = os.getenv("MLFLOW_MODEL_STAGE", "Production")  # Production, Staging, or None for local
USE_MLFLOW_REGISTRY = os.getenv("USE_MLFLOW_REGISTRY", "true").lower() == "true"

# Model info from registry
model_info = {
    "anomaly": None,
    "classifier": None,
    "rul": None
}

def load_or_none(path):
    """Load model from local filesystem."""
    return joblib.load(path) if os.path.exists(path) else None

def load_model_with_fallback(model_name: str, local_path: str, model_type: str = "sklearn"):
    """
    Load model from MLflow Registry with fallback to local filesystem.
    
    Args:
        model_name: Name of the model (anomaly, classifier, rul)
        local_path: Local path to model file
        model_type: Type of model (sklearn, xgboost, lightgbm)
    
    Returns:
        Loaded model or None
    """
    # Try MLflow Registry first if enabled
    if USE_MLFLOW_REGISTRY and MLFLOW_MODEL_STAGE:
        try:
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            model = load_model_from_registry(model_name, stage=MLFLOW_MODEL_STAGE)
            print(f"✅ Loaded {model_name} from MLflow Registry (stage: {MLFLOW_MODEL_STAGE})")
            
            # Get model info
            info = get_model_info(model_name, stage=MLFLOW_MODEL_STAGE)
            model_info[model_name] = info
            
            # Extract actual model from pyfunc wrapper
            # MLflow pyfunc models wrap the actual model
            try:
                if hasattr(model, "_model_impl"):
                    impl = model._model_impl
                    # Try different ways to extract the actual model
                    if hasattr(impl, 'sklearn_model'):
                        return impl.sklearn_model
                    elif hasattr(impl, 'xgboost_model'):
                        return impl.xgboost_model
                    elif hasattr(impl, 'lightgbm_model'):
                        return impl.lightgbm_model
                    elif hasattr(impl, 'model'):
                        return impl.model
                    else:
                        # Return the implementation itself
                        return impl
                elif hasattr(model, "predict"):
                    # If it's already the model or has predict method, use it
                    return model
                else:
                    # Last resort: return as-is (might work for some models)
                    return model
            except Exception as extract_error:
                print(f"⚠️ Error extracting model from wrapper: {extract_error}")
                # Return wrapper - will need to handle in prediction code
                return model
        except Exception as e:
            print(f"⚠️ Failed to load {model_name} from MLflow Registry: {e}")
            print(f"   Falling back to local filesystem: {local_path}")
    
    # Fallback to local filesystem
    return load_or_none(local_path)

def reload_models():
    """Reload tất cả models từ MLflow Registry hoặc local filesystem."""
    global isof, if_scaler, if_features
    global clf_model, clf_scaler, clf_features, clf_label_encoder, clf_normal_label, clf_label_col
    global rul_model, rul_features
    
    MODEL_DIR = "models"
    
    print("\n" + "="*80)
    print("LOADING MODELS")
    print("="*80)
    print(f"MLflow Registry: {'Enabled' if USE_MLFLOW_REGISTRY else 'Disabled'}")
    print(f"Model Stage: {MLFLOW_MODEL_STAGE if MLFLOW_MODEL_STAGE else 'Local filesystem'}")
    print()
    
    # ---- Anomaly (Isolation Forest) ----
    print("Loading anomaly model...")
    isof = load_model_with_fallback("anomaly", f"{MODEL_DIR}/anomaly/isolation_forest.joblib")
    if_scaler = load_or_none(f"{MODEL_DIR}/anomaly/scaler.joblib")  # Always from local (artifact)
    if_features = load_or_none(f"{MODEL_DIR}/anomaly/isofeat.joblib")  # Always from local (artifact)
    
    # ---- Classifier ----
    print("Loading classifier model...")
    clf_model = load_model_with_fallback("classifier", f"{MODEL_DIR}/classifier/classifier.joblib")
    clf_scaler = load_or_none(f"{MODEL_DIR}/classifier/scaler.joblib")  # Always from local
    clf_features = load_or_none(f"{MODEL_DIR}/classifier/features.joblib")
    clf_label_encoder = load_or_none(f"{MODEL_DIR}/classifier/label_encoder.joblib")
    clf_normal_label = load_or_none(f"{MODEL_DIR}/classifier/normal_label.joblib")
    clf_label_col = load_or_none(f"{MODEL_DIR}/classifier/label_col.joblib")
    
    # ---- RUL Predictor ----
    print("Loading RUL model...")
    rul_model = load_model_with_fallback("rul", f"{MODEL_DIR}/rul/lgbm_rul.joblib")
    rul_features = load_or_none(f"{MODEL_DIR}/rul/rul_features.joblib")  # Always from local
    
    print("\n" + "="*80)
    print("MODEL LOADING SUMMARY")
    print("="*80)
    print(f"Anomaly: {'✅' if isof else '❌'}")
    print(f"Classifier: {'✅' if clf_model else '❌'}")
    print(f"RUL: {'✅' if rul_model else '❌'}")
    print()

MODEL_DIR = "models"

# Initialize MLflow tracking URI
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Load models (will try MLflow Registry first, then fallback to local)
reload_models()

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
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "ev_predictions")

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

@app.get("/health")
def health():
    """Health check endpoint với thông tin về models và MLflow Registry."""
    health_status = {
        "status": "healthy",
        "services": {
            "anomaly": isof is not None and if_scaler is not None and if_features is not None,
            "classifier": clf_model is not None and clf_scaler is not None and clf_features is not None,
            "rul": rul_model is not None and rul_features is not None
        },
        "kafka": {
            "enabled": kafka_enabled,
            "connected": kafka_producer is not None
        },
        "mlflow": {
            "tracking_uri": MLFLOW_TRACKING_URI,
            "registry_enabled": USE_MLFLOW_REGISTRY,
            "model_stage": MLFLOW_MODEL_STAGE if USE_MLFLOW_REGISTRY else None,
            "model_info": model_info
        }
    }
    
    # Determine overall health
    all_models_loaded = all(health_status["services"].values())
    if not all_models_loaded:
        health_status["status"] = "degraded"
        health_status["message"] = "Some models are not loaded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)
def health():
    """Health check endpoint for monitoring and load balancers."""
    health_status = {
        "status": "healthy",
        "services": {
            "anomaly": isof is not None and if_scaler is not None and if_features is not None,
            "classifier": clf_model is not None and clf_scaler is not None and clf_features is not None,
            "rul": rul_model is not None and rul_features is not None
        },
        "kafka": kafka_enabled and kafka_producer is not None
    }
    
    # Determine overall health
    all_models_loaded = all(health_status["services"].values())
    if not all_models_loaded:
        health_status["status"] = "degraded"
        health_status["message"] = "Some models are not loaded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/")
def root():
    """Root endpoint with API information."""
    return JSONResponse(content={
        "name": "EV Predictive Maintenance API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "predict": "/predict",
            "docs": "/docs",
            "training": "/api/train",
            "training_status": "/api/training/status"
        }
    })

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
    """Send prediction data to Kafka topic with improved error handling."""
    if not kafka_enabled or kafka_producer is None:
        print(f"[WARN] Kafka disabled or not reachable; skipping send to topic: {KAFKA_TOPIC}")
        return False
    
    try:
        import json
        # Serialize to JSON string instead of str() for better compatibility
        message_value = json.dumps(data)
        kafka_producer.produce(
            KAFKA_TOPIC, 
            value=message_value,
            callback=lambda err, msg: print(f"[ERROR] Kafka delivery failed: {err}") if err else None
        )
        # Trigger delivery callbacks
        kafka_producer.poll(0)
        return True
    except Exception as e:
        print(f"[ERROR] Kafka send failed to topic {KAFKA_TOPIC}: {e}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return False

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
        return JSONResponse(
            status_code=503,
            content={"error": "Anomaly model/scaler/features missing. Run anomaly pipeline first."}
        )

    try:
        x_if = _build_row(if_features, data)
        x_if_scaled = if_scaler.transform(x_if)
        if_pred = isof.predict(x_if_scaled)[0]  # 1 normal, -1 anomaly
        is_anomaly = int(if_pred == -1)
    except Exception as e:
        import traceback
        error_msg = f"Anomaly inference error: {e}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

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
    pred_code = None
    is_fault = False

    if clf_model and clf_scaler and clf_features:
        try:
            x_clf = _build_row(clf_features, data)
            x_clf_scaled = clf_scaler.transform(x_clf)
            # Handle both direct model and pyfunc wrapper
            if hasattr(clf_model, 'predict'):
                pred = clf_model.predict(x_clf_scaled)
                pred_code = int(pred[0] if hasattr(pred, '__len__') and len(pred) > 0 else pred)
            else:
                # Fallback
                pred_code = int(clf_model(x_clf_scaled)[0]) if callable(clf_model) else 0
            
            # Decode label using label_encoder if available, otherwise use FAULT_MAP
            if clf_label_encoder:
                try:
                    classifier_label = clf_label_encoder.inverse_transform([pred_code])[0]
                except Exception as decode_err:
                    print(f"[WARN] Label decoder error for code {pred_code}: {decode_err}")
                    classifier_label = FAULT_MAP.get(pred_code, str(pred_code))
            else:
                classifier_label = FAULT_MAP.get(pred_code, str(pred_code))
            
            # Check if prediction is a fault (not normal_label)
            if clf_normal_label is not None:
                is_fault = (pred_code != clf_normal_label)
            else:
                # Fallback: assume non-zero codes are faults
                is_fault = (pred_code != 0)
        except Exception as e:
            import traceback
            error_msg = f"Classifier Error: {e}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            classifier_label = error_msg
            is_fault = False  # Don't proceed with RUL if classifier fails
    else:
        print("[WARN] Classifier model/scaler/features not available")
        classifier_label = "Classifier unavailable"

    result["classifier_label"] = classifier_label
    result["is_fault"] = is_fault

    # ========================================================
    # 3) RUL Prediction
    # ========================================================
    rul_value = None
    if is_fault and rul_model and rul_features:
        try:
            # Build features for RUL
            x_rul_list = []
            for f in rul_features:
                if f == clf_label_col and clf_label_col and pred_code is not None:
                    # Use encoded prediction code from classifier
                    x_rul_list.append(float(pred_code))
                else:
                    # Use feature from input data
                    x_rul_list.append(float(data.get(f, 0.0)))
            
            x_rul = np.array([x_rul_list])
            # Handle both direct model and pyfunc wrapper
            if hasattr(rul_model, 'predict'):
                rul_pred = rul_model.predict(x_rul)
                rul_value = float(rul_pred[0] if hasattr(rul_pred, '__len__') and len(rul_pred) > 0 else rul_pred)
            else:
                # Fallback
                rul_value = float(rul_model(x_rul)[0]) if callable(rul_model) else None
        except Exception as e:
            import traceback
            print(f"[ERROR] RUL prediction failed: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
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
    # Format: Match alert_service expected format
    alert_payload = {
        "timestamp": int(time.time()),
        "host": socket.gethostname(),
        "input": payload.data,
        "prediction": {
            "IF_Anomaly": int(is_anomaly),
            "classifier_label": str(classifier_label) if classifier_label else None,
            "is_fault": bool(is_fault),
            "RUL_estimated": float(rul_value) if rul_value is not None else None,
            "failure_prob": payload.data.get("Failure_Probability", 0.0)  # Add for alert service
        }
    }

    if is_anomaly == 1 or is_fault:
        kafka_success = kafka_send_prediction(alert_payload)
        if not kafka_success:
            print(f"[WARN] Failed to send alert to Kafka, but prediction completed successfully")

    # Ensure all values in result are JSON serializable (Python native types)
    json_result = {
        "IF_Anomaly": int(result.get("IF_Anomaly", 0)),
        "classifier_label": str(result.get("classifier_label")) if result.get("classifier_label") else None,
        "is_fault": bool(result.get("is_fault", False)),
        "RUL_estimated": float(result.get("RUL_estimated")) if result.get("RUL_estimated") is not None else None
    }
    
    # Add status if present
    if "status" in result:
        json_result["status"] = str(result["status"])
    
    return json_result

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

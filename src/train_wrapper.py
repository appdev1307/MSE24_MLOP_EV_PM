import os
import subprocess
import mlflow
import shutil
from pathlib import Path
from mlflow_utils import (
    register_anomaly_model,
    register_classifier_model,
    register_rul_model
)

# ==============================
# CONFIG
# ==============================
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT", "predictive-maintenance")

SCRIPTS = [
    "src/anomaly.py",      # Must run first to generate parquet with IF_Anomaly
    "src/classifier.py",   # Uses parquet from anomaly
    "src/rul.py"           # Uses parquet and classifier artifacts
]

MODELS_DIR = Path("models")
MODEL_SUBDIRS = ["anomaly", "classifier", "rul"]

# ==============================
# SETUP
# ==============================
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment(EXPERIMENT_NAME)

# Clean old models (DEV MODE behavior)
if MODELS_DIR.exists():
    print("🧹 Cleaning old models directory")
    shutil.rmtree(MODELS_DIR)

MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ==============================
# HELPERS
# ==============================
def run_scripts_or_fail():
    for script in SCRIPTS:
        print(f"▶ Running {script}")
        ret = subprocess.run(["python", script])
        if ret.returncode != 0:
            raise RuntimeError(f"❌ Training failed in {script}")

def log_models():
    """Log models as artifacts to MLflow."""
    for subdir in MODEL_SUBDIRS:
        path = MODELS_DIR / subdir
        if path.exists():
            print(f"📦 Logging {path}")
            mlflow.log_artifacts(str(path), artifact_path=f"models/{subdir}")
        else:
            print(f"⚠️ Skipping missing model dir: {path}")

def register_models(run_id: str, initial_stage: str = "Staging"):
    """
    Register all models to MLflow Model Registry.
    
    Args:
        run_id: MLflow run ID for the parent pipeline run
        initial_stage: Initial stage for registered models (Staging, Production, None)
    """
    print("\n" + "="*80)
    print("REGISTERING MODELS TO MLFLOW MODEL REGISTRY")
    print("="*80)
    
    try:
        # Register anomaly model
        anomaly_dir = MODELS_DIR / "anomaly"
        if anomaly_dir.exists():
            print(f"\n📝 Registering anomaly model...")
            register_anomaly_model(anomaly_dir, run_id=run_id, stage=initial_stage)
        else:
            print(f"⚠️ Anomaly model directory not found: {anomaly_dir}")
        
        # Register classifier model
        classifier_dir = MODELS_DIR / "classifier"
        if classifier_dir.exists():
            print(f"\n📝 Registering classifier model...")
            register_classifier_model(classifier_dir, run_id=run_id, stage=initial_stage)
        else:
            print(f"⚠️ Classifier model directory not found: {classifier_dir}")
        
        # Register RUL model
        rul_dir = MODELS_DIR / "rul"
        if rul_dir.exists():
            print(f"\n📝 Registering RUL model...")
            register_rul_model(rul_dir, run_id=run_id, stage=initial_stage)
        else:
            print(f"⚠️ RUL model directory not found: {rul_dir}")
        
        print("\n" + "="*80)
        print("✅ All models registered successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error registering models: {e}")
        import traceback
        traceback.print_exc()
        raise

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    # Get initial stage from environment (default: Staging)
    initial_stage = os.getenv("MLFLOW_MODEL_STAGE", "Staging")
    
    with mlflow.start_run() as run:
        # Set tags for filtering in MLflow UI
        dataset_name = "EV_Predictive_Maintenance_Dataset_15min"
        mlflow.set_tag("dataset", dataset_name)
        mlflow.set_tag("model", "ensemble")  # Pipeline includes multiple models
        
        mlflow.log_param("pipeline", "ev_predictive_maintenance")
        mlflow.log_param("scripts", ",".join(SCRIPTS))
        mlflow.log_param("model_stage", initial_stage)

        run_scripts_or_fail()
        log_models()

        # Register models to Model Registry
        register_models(run.info.run_id, initial_stage=initial_stage)

        print("\n✅ Training pipeline completed")
        print("🏃 Run:", run.info.run_id)
        print(f"📦 Models registered to stage: {initial_stage}")
        print(f"🔗 View in MLflow UI: {MLFLOW_URI}")

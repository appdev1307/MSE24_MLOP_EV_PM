import os
import subprocess
import mlflow
import shutil
from pathlib import Path

# ==============================
# CONFIG
# ==============================
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT", "predictive-maintenance")

SCRIPTS = [
    "src/classifier.py",
    "src/rul.py",
    "src/anomaly.py"
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
    for subdir in MODEL_SUBDIRS:
        path = MODELS_DIR / subdir
        if path.exists():
            print(f"📦 Logging {path}")
            mlflow.log_artifacts(str(path), artifact_path=f"models/{subdir}")
        else:
            print(f"⚠️ Skipping missing model dir: {path}")

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    with mlflow.start_run() as run:
        mlflow.log_param("pipeline", "ev_predictive_maintenance")
        mlflow.log_param("scripts", ",".join(SCRIPTS))

        run_scripts_or_fail()
        log_models()

        print("✅ Training pipeline completed")
        print("🏃 Run:", run.info.run_id)

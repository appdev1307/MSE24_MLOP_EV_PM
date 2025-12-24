import os
import subprocess
import mlflow
import joblib
from mlflow.tracking import MlflowClient

# ==============================
# CONFIG
# ==============================
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT", "predictive-maintenance")

SCRIPTS = [
    "src/anomaly.py",
    "src/classifier.py",
    "src/rul.py",
]

# ==============================
# SETUP
# ==============================
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment(EXPERIMENT_NAME)
client = MlflowClient()

# ==============================
# HELPERS
# ==============================
def run_scripts_or_fail():
    for script in SCRIPTS:
        print(f"▶ Running {script}")
        ret = subprocess.run(["python", script])
        if ret.returncode != 0:
            raise RuntimeError(f"❌ Training failed: {script}")

def log_and_register(local_model_path: str, model_name: str):
    """
    MLflow 2.14 SAFE registry flow
    """
    print(f"📌 Registering {model_name}")

    # 1️⃣ Log as artifact ONLY
    mlflow.log_artifact(local_model_path, artifact_path=model_name)

    run_id = mlflow.active_run().info.run_id
    source = f"runs:/{run_id}/{model_name}/{os.path.basename(local_model_path)}"

    # 2️⃣ Create registered model if needed
    try:
        client.create_registered_model(model_name)
    except Exception:
        pass  # already exists

    # 3️⃣ Create model version
    mv = client.create_model_version(
        name=model_name,
        source=source,
        run_id=run_id,
    )

    # 4️⃣ Promote to Production
    client.transition_model_version_stage(
        name=model_name,
        version=mv.version,
        stage="Production",
        archive_existing_versions=True
    )

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    with mlflow.start_run():
        run_scripts_or_fail()

        log_and_register(
            "models/anomaly/isolation_forest.joblib",
            "ev-anomaly-model"
        )
        log_and_register(
            "models/classifier/classifier.joblib",
            "ev-classifier-model"
        )
        log_and_register(
            "models/rul/lgbm_rul.joblib",
            "ev-rul-model"
        )

        print("✅ All models registered and promoted to Production")

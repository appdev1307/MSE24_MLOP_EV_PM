import os
import subprocess
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.exceptions import RestException

# ==============================
# CONFIG
# ==============================
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT", "predictive-maintenance")

# Timeout for each individual training script (seconds). Adjust as needed.
# 1800 = 30 minutes. Set to 0 or None to disable timeout.
SCRIPT_TIMEOUT = int(os.getenv("TRAINING_SCRIPT_TIMEOUT", "1800"))  # 0 = no timeout

SCRIPTS = [
    "src/anomaly.py",
    "src/classifier.py",
    "src/rul.py",
]

# Model groups: (local_directory, registered_model_name, bundle_artifact_path)
MODEL_GROUPS = [
    ("models/anomaly",    "ev-anomaly-model",    "anomaly_bundle"),
    ("models/classifier", "ev-classifier-model", "classifier_bundle"),
    ("models/rul",        "ev-rul-model",        "rul_bundle"),
]

# ==============================
# SETUP
# ==============================
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment(EXPERIMENT_NAME)
client = MlflowClient(tracking_uri=MLFLOW_URI)

# ==============================
# HELPERS
# ==============================
def run_scripts_or_fail():
    """Run all training scripts with optional timeout."""
    for script in SCRIPTS:
        print(f"▶ Running {script} {'(no timeout)' if SCRIPT_TIMEOUT <= 0 else f'(timeout: {SCRIPT_TIMEOUT}s)'} ...")

        try:
            result = subprocess.run(
                ["python", script],
                capture_output=True,
                text=True,
                timeout=SCRIPT_TIMEOUT if SCRIPT_TIMEOUT > 0 else None
            )

            if result.returncode == 0:
                print(f"✅ {script} completed successfully")
                if result.stdout.strip():
                    print(result.stdout)
            else:
                print(f"❌ {script} failed (return code {result.returncode})")
                if result.stdout:
                    print("STDOUT:\n", result.stdout)
                if result.stderr:
                    print("STDERR:\n", result.stderr)
                raise RuntimeError(f"Training failed: {script}")

        except subprocess.TimeoutExpired:
            print(f"⏰ {script} TIMED OUT after {SCRIPT_TIMEOUT} seconds!")
            raise RuntimeError(f"Training timeout: {script}")
        except Exception as e:
            print(f"❌ Unexpected error running {script}: {e}")
            raise

def register_model_group(local_dir: str, model_name: str, bundle_path: str):
    """Log entire directory as a bundle and register as a new version with @production alias."""
    if not os.path.isdir(local_dir):
        print(f"⚠️ Directory not found: {local_dir} → skipping {model_name}")
        return

    contents = os.listdir(local_dir)
    print(f"📂 Found {len(contents)} files in {local_dir}: {contents}")

    print(f"📌 Logging directory '{local_dir}' → artifact path '{bundle_path}'")
    mlflow.log_artifacts(local_dir, artifact_path=bundle_path)

    run_id = mlflow.active_run().info.run_id
    source_uri = f"runs:/{run_id}/{bundle_path}"

    # Create registered model if it doesn't exist
    try:
        client.create_registered_model(model_name)
        print(f"   Created new registered model: {model_name}")
    except RestException as e:
        if "RESOURCE_ALREADY_EXISTS" not in str(e):
            raise
        # Already exists → OK

    # Create new model version
    mv = client.create_model_version(
        name=model_name,
        source=source_uri,
        run_id=run_id,
        description=f"Bundle containing: {', '.join(contents)}"
    )

    # Set @production alias (modern way)
    client.set_registered_model_alias(
        name=model_name,
        alias="production",
        version=str(mv.version)
    )

    print(f"✅ {model_name} → version {mv.version} registered and aliased as @production")

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    print("🚀 Starting model training and registry pipeline...\n")

    try:
        with mlflow.start_run(run_name="model-training-and-registry"):
            run_scripts_or_fail()

            print("\n📦 Registering model bundles...")
            for local_dir, model_name, bundle_path in MODEL_GROUPS:
                register_model_group(local_dir, model_name, bundle_path)

        print("\n🎉 Pipeline completed successfully! All models are bundled and promoted to @production.")

    except Exception as e:
        print(f"\n💥 Pipeline failed: {e}")
        raise
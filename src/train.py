"""
Training Pipeline Orchestrator
Orchestrates the complete training pipeline: anomaly detection → classification → RUL prediction.
Registers all models to MLflow Model Registry.
"""
import os
import shutil
import subprocess
import traceback
from pathlib import Path

import mlflow

from mlflow_utils import (
    register_anomaly_model,
    register_classifier_model,
    register_rul_model,
)

# Configuration
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:6969")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT", "predictive-maintenance")
INITIAL_STAGE = os.getenv("MLFLOW_MODEL_STAGE", "Staging")

# Training scripts (must run in this order)
TRAINING_SCRIPTS = [
    "src/anomaly.py",      # Must run first to generate parquet with IF_Anomaly
    "src/classifier.py",   # Uses parquet from anomaly
    "src/rul.py",          # Uses parquet and classifier artifacts
]

# Model directories
MODELS_DIR = Path("models")
MODEL_SUBDIRS = ["anomaly", "classifier", "rul"]


def run_training_scripts() -> None:
    """Run all training scripts in sequence, fail fast on error."""
    for script in TRAINING_SCRIPTS:
        print(f"▶ Running {script}")
        result = subprocess.run(["python", script], check=False)
        if result.returncode != 0:
            raise RuntimeError(f"❌ Training failed in {script}")


def log_models_to_mlflow() -> None:
    """Log all trained models as artifacts to MLflow."""
    for subdir in MODEL_SUBDIRS:
        model_path = MODELS_DIR / subdir
        if model_path.exists():
            print(f"📦 Logging {model_path}")
            mlflow.log_artifacts(str(model_path), artifact_path=f"models/{subdir}")
        else:
            print(f"⚠️  Skipping missing model dir: {model_path}")


def register_all_models(run_id: str, stage: str = INITIAL_STAGE) -> None:
    """
    Register all models to MLflow Model Registry.
    
    Args:
        run_id: MLflow run ID for the parent pipeline run
        stage: Initial stage for registered models (Staging, Production, None)
    """
    print("\n" + "=" * 80)
    print("REGISTERING MODELS TO MLFLOW MODEL REGISTRY")
    print("=" * 80)

    model_dirs = {
        "anomaly": MODELS_DIR / "anomaly",
        "classifier": MODELS_DIR / "classifier",
        "rul": MODELS_DIR / "rul",
    }

    register_functions = {
        "anomaly": register_anomaly_model,
        "classifier": register_classifier_model,
        "rul": register_rul_model,
    }

    try:
        for model_name, model_dir in model_dirs.items():
            if model_dir.exists():
                print(f"\n📝 Registering {model_name} model...")
                register_func = register_functions[model_name]
                register_func(model_dir, run_id=run_id, stage=stage)
            else:
                print(f"⚠️  {model_name.capitalize()} model directory not found: {model_dir}")

        print("\n" + "=" * 80)
        print("✅ All models registered successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error registering models: {e}")
        traceback.print_exc()
        raise


def setup_mlflow() -> None:
    """Initialize MLflow tracking URI and experiment."""
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)


def cleanup_models_directory() -> None:
    """Clean old models directory (dev mode behavior)."""
    if MODELS_DIR.exists():
        print("🧹 Cleaning old models directory")
        shutil.rmtree(MODELS_DIR)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Main training pipeline."""
    # Setup
    setup_mlflow()
    cleanup_models_directory()

    # Run training pipeline
    with mlflow.start_run() as run:
        # Set tags for filtering in MLflow UI
        dataset_name = "EV_Predictive_Maintenance_Dataset_15min"
        mlflow.set_tag("dataset", dataset_name)
        mlflow.set_tag("model", "ensemble")  # Pipeline includes multiple models

        # Log pipeline parameters
        mlflow.log_param("pipeline", "ev_predictive_maintenance")
        mlflow.log_param("scripts", ",".join(TRAINING_SCRIPTS))
        mlflow.log_param("model_stage", INITIAL_STAGE)

        # Execute training pipeline
        run_training_scripts()
        log_models_to_mlflow()

        # Register models to Model Registry
        register_all_models(run.info.run_id, stage=INITIAL_STAGE)

        # Summary
        print("\n✅ Training pipeline completed")
        print(f"🏃 Run: {run.info.run_id}")
        print(f"📦 Models registered to stage: {INITIAL_STAGE}")
        print(f"🔗 View in MLflow UI: {MLFLOW_URI}")


if __name__ == "__main__":
    main()


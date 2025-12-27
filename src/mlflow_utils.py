"""
Utility functions for MLflow Model Registry integration
"""

import os
import mlflow
import joblib
from pathlib import Path
from typing import Optional, Dict, Any
from mlflow.tracking import MlflowClient

# Model registry names
MODEL_NAMES = {
    "anomaly": "EV_Anomaly_Detector",
    "classifier": "EV_Fault_Classifier",
    "rul": "EV_RUL_Predictor"
}

def get_mlflow_client() -> MlflowClient:
    """Get MLflow client with tracking URI."""
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:6969")
    return MlflowClient(tracking_uri=tracking_uri)

def register_anomaly_model(
    model_dir: Path,
    run_id: Optional[str] = None,
    stage: str = "Staging"
) -> str:
    """
    Register Isolation Forest anomaly model to MLflow Model Registry.
    Note: Should be called from within an active MLflow run context.
    """
    """
    Register Isolation Forest anomaly model to MLflow Model Registry.
    
    Args:
        model_dir: Directory containing model files (isolation_forest.joblib, scaler.joblib, isofeat.joblib)
        run_id: MLflow run ID (if None, uses current active run)
        stage: Initial stage for the model (Staging, Production, Archived)
    
    Returns:
        Model version
    """
    model_path = model_dir / "isolation_forest.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load model to register
    model = joblib.load(model_path)
    
    # Save model as MLflow model format (creates MLmodel file)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_model_path = Path(tmp_dir) / "model"
        mlflow.sklearn.save_model(model, str(tmp_model_path))
        
        # Log model artifacts to current run
        mlflow.log_artifacts(str(tmp_model_path), artifact_path="anomaly_model")
        
        # Get model URI from current run
        active_run = mlflow.active_run()
        if not active_run:
            raise RuntimeError("No active MLflow run found")
        
        model_uri = f"runs:/{active_run.info.run_id}/anomaly_model"
    
    # Log additional artifacts (already logged in train_wrapper, but log again for completeness)
    if (model_dir / "scaler.joblib").exists():
        mlflow.log_artifact(str(model_dir / "scaler.joblib"), "anomaly_artifacts")
    if (model_dir / "isofeat.joblib").exists():
        mlflow.log_artifact(str(model_dir / "isofeat.joblib"), "anomaly_artifacts")
    
    # Register model to Model Registry (separate step)
    try:
        mv = mlflow.register_model(
            model_uri=model_uri,
            name=MODEL_NAMES["anomaly"]
        )
        
        # Get version from ModelVersion object
        version = mv.version
        
        # Transition to stage if needed
        if stage and stage != "None":
            client = get_mlflow_client()
            client.transition_model_version_stage(
                name=MODEL_NAMES["anomaly"],
                version=version,
                stage=stage
            )
            print(f"✅ Registered {MODEL_NAMES['anomaly']} version {version} to {stage}")
        else:
            print(f"✅ Registered {MODEL_NAMES['anomaly']} version {version}")
        
        return str(version)
    except Exception as e:
        print(f"⚠️ Failed to register model: {e}")
        print(f"   Model logged at: {model_uri}")
        print(f"   You can register it manually later")
        raise

def register_classifier_model(
    model_dir: Path,
    run_id: Optional[str] = None,
    stage: str = "Staging"
) -> str:
    """
    Register XGBoost classifier model to MLflow Model Registry.
    Note: Should be called from within an active MLflow run context.
    
    Args:
        model_dir: Directory containing classifier files
        run_id: MLflow run ID (not used, kept for compatibility)
        stage: Initial stage for the model
    
    Returns:
        Model version number
    """
    model_path = model_dir / "classifier.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load model
    model = joblib.load(model_path)
    
    # Save model as MLflow model format (creates MLmodel file)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_model_path = Path(tmp_dir) / "model"
        mlflow.xgboost.save_model(model, str(tmp_model_path))
        
        # Log model artifacts to current run
        mlflow.log_artifacts(str(tmp_model_path), artifact_path="classifier_model")
        
        # Get model URI from current run
        active_run = mlflow.active_run()
        if not active_run:
            raise RuntimeError("No active MLflow run found")
        
        model_uri = f"runs:/{active_run.info.run_id}/classifier_model"
    
    # Log additional artifacts
    artifacts = ["scaler.joblib", "features.joblib", "label_encoder.joblib", 
                 "normal_label.joblib", "label_col.joblib"]
    for artifact in artifacts:
        if (model_dir / artifact).exists():
            mlflow.log_artifact(str(model_dir / artifact), "classifier_artifacts")
    
    # Register model to Model Registry
    try:
        mv = mlflow.register_model(
            model_uri=model_uri,
            name=MODEL_NAMES["classifier"]
        )
        
        # Get version from ModelVersion object
        version = mv.version
        
        # Transition to stage if needed
        if stage and stage != "None":
            client = get_mlflow_client()
            client.transition_model_version_stage(
                name=MODEL_NAMES["classifier"],
                version=version,
                stage=stage
            )
            print(f"✅ Registered {MODEL_NAMES['classifier']} version {version} to {stage}")
        else:
            print(f"✅ Registered {MODEL_NAMES['classifier']} version {version}")
        
        return str(version)
    except Exception as e:
        print(f"⚠️ Failed to register model: {e}")
        print(f"   Model logged at: {model_uri}")
        raise

def register_rul_model(
    model_dir: Path,
    run_id: Optional[str] = None,
    stage: str = "Staging"
) -> str:
    """
    Register LightGBM RUL model to MLflow Model Registry.
    Note: Should be called from within an active MLflow run context.
    
    Args:
        model_dir: Directory containing RUL model files
        run_id: MLflow run ID (not used, kept for compatibility)
        stage: Initial stage for the model
    
    Returns:
        Model version number
    """
    model_path = model_dir / "lgbm_rul.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load model
    model = joblib.load(model_path)
    
    # Save model as MLflow model format (creates MLmodel file)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_model_path = Path(tmp_dir) / "model"
        mlflow.lightgbm.save_model(model, str(tmp_model_path))
        
        # Log model artifacts to current run
        mlflow.log_artifacts(str(tmp_model_path), artifact_path="rul_model")
        
        # Get model URI from current run
        active_run = mlflow.active_run()
        if not active_run:
            raise RuntimeError("No active MLflow run found")
        
        model_uri = f"runs:/{active_run.info.run_id}/rul_model"
    
    # Log features
    if (model_dir / "rul_features.joblib").exists():
        mlflow.log_artifact(str(model_dir / "rul_features.joblib"), "rul_artifacts")
    
    # Register model to Model Registry
    try:
        mv = mlflow.register_model(
            model_uri=model_uri,
            name=MODEL_NAMES["rul"]
        )
        
        # Get version from ModelVersion object
        version = mv.version
        
        # Transition to stage if needed
        if stage and stage != "None":
            client = get_mlflow_client()
            client.transition_model_version_stage(
                name=MODEL_NAMES["rul"],
                version=version,
                stage=stage
            )
            print(f"✅ Registered {MODEL_NAMES['rul']} version {version} to {stage}")
        else:
            print(f"✅ Registered {MODEL_NAMES['rul']} version {version}")
        
        return str(version)
    except Exception as e:
        print(f"⚠️ Failed to register model: {e}")
        print(f"   Model logged at: {model_uri}")
        raise

def load_model_from_registry(
    model_name: str,
    stage: str = "Production",
    version: Optional[int] = None
):
    """
    Load model from MLflow Model Registry.
    
    Args:
        model_name: Name of the model (anomaly, classifier, rul)
        stage: Stage to load from (Production, Staging, Archived)
        version: Specific version to load (if None, loads latest from stage)
    
    Returns:
        Loaded model
    """
    if model_name not in MODEL_NAMES:
        raise ValueError(f"Unknown model name: {model_name}. Must be one of {list(MODEL_NAMES.keys())}")
    
    registered_name = MODEL_NAMES[model_name]
    
    if version:
        model_uri = f"models:/{registered_name}/{version}"
    else:
        model_uri = f"models:/{registered_name}/{stage}"
    
    try:
        model = mlflow.pyfunc.load_model(model_uri)
        print(f"✅ Loaded {registered_name} from {model_uri}")
        return model
    except Exception as e:
        print(f"⚠️ Failed to load {registered_name} from registry: {e}")
        raise

def get_model_info(model_name: str, stage: str = "Production") -> Dict[str, Any]:
    """
    Get information about a registered model.
    
    Args:
        model_name: Name of the model (anomaly, classifier, rul)
        stage: Stage to get info from
    
    Returns:
        Dictionary with model information
    """
    if model_name not in MODEL_NAMES:
        raise ValueError(f"Unknown model name: {model_name}")
    
    registered_name = MODEL_NAMES[model_name]
    client = get_mlflow_client()
    
    try:
        versions = client.get_latest_versions(registered_name, stages=[stage])
        if versions:
            version = versions[0]
            return {
                "name": registered_name,
                "version": version.version,
                "stage": version.current_stage,
                "run_id": version.run_id,
                "creation_timestamp": version.creation_timestamp
            }
        else:
            return {"error": f"No model found in {stage} stage"}
    except Exception as e:
        return {"error": str(e)}


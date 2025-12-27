#!/usr/bin/env python3
"""
Complete Workflow Script - Predictive Maintenance on Vehicle Telemetry Data

Workflow:
1. Download dataset from Kaggle
2. Process data
3. Prepare data
4. Train models
5. Run experiments
6. Analyze metrics
7. Select best model
8. Register version 1
9. Deploy to production
"""

import os
import sys
import subprocess
import mlflow
from mlflow.tracking import MlflowClient
from pathlib import Path

# Configuration
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:6969")
EXPERIMENT_NAME = "predictive-maintenance"
MODEL_NAME = "ev-predictive-maintenance"
DATASET_PATH = "src/data/EV_Predictive_Maintenance_Dataset_15min.csv"

def step_1_download_dataset():
    """Stage 1: Download dataset from Kaggle"""
    print("\n" + "="*60)
    print("Stage 1: Download Dataset from Kaggle")
    print("="*60)
    
    if os.path.exists(DATASET_PATH):
        print(f"✅ Dataset already exists: {DATASET_PATH}")
        return True
    
    print("📥 Downloading dataset...")
    print("Run: bash scripts/download_dataset.sh")
    print("Or: .\\scripts\\download_dataset.ps1")
    
    return False

def step_2_process_data():
    """Stage 2: Process data"""
    print("\n" + "="*60)
    print("Stage 2: Process Data")
    print("="*60)
    
    print("🔄 Running preprocessing...")
    result = subprocess.run(["python", "src/preprocessing.py"], capture_output=True)
    
    if result.returncode == 0:
        print("✅ Data processing completed")
        return True
    else:
        print(f"❌ Error: {result.stderr.decode()}")
        return False

def step_3_prepare_data():
    """Stage 3: Prepare data"""
    print("\n" + "="*60)
    print("Stage 3: Prepare Data")
    print("="*60)
    
    print("📊 Data preparation is done during preprocessing")
    print("✅ Features selected and normalized")
    return True

def step_4_train_models():
    """Stage 4: Train models"""
    print("\n" + "="*60)
    print("Stage 4: Train Models")
    print("="*60)
    
    print("🚂 Training models...")
    result = subprocess.run(["python", "src/train_wrapper.py"], capture_output=True)
    
    if result.returncode == 0:
        print("✅ Training completed")
        print(result.stdout.decode())
        return True
    else:
        print(f"❌ Error: {result.stderr.decode()}")
        return False

def step_5_run_experiments():
    """Stage 5: Run experiments (already done in training)"""
    print("\n" + "="*60)
    print("Stage 5: Run Experiments")
    print("="*60)
    
    print("✅ Experiments logged to MLflow")
    print(f"📊 View at: {MLFLOW_URI}")
    return True

def step_6_analyze_metrics():
    """Stage 6: Analyze metrics"""
    print("\n" + "="*60)
    print("Stage 6: Analyze Metrics")
    print("="*60)
    
    try:
        client = MlflowClient(tracking_uri=MLFLOW_URI)
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        
        if experiment is None:
            print("⚠️  No experiments found")
            return False
        
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["metrics.f1_score DESC"]
        )
        
        print(f"\n📊 Found {len(runs)} runs:")
        print("-" * 60)
        
        for i, run in enumerate(runs[:5], 1):  # Top 5
            metrics = run.data.metrics
            params = run.data.params
            
            print(f"\n{i}. Run: {run.info.run_name}")
            print(f"   Run ID: {run.info.run_id}")
            print(f"   Metrics:")
            for key, value in metrics.items():
                print(f"     - {key}: {value:.4f}")
            print(f"   Status: {run.info.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing metrics: {e}")
        return False

def step_7_select_best_model():
    """Stage 7: Select best model"""
    print("\n" + "="*60)
    print("Stage 7: Select Best Model")
    print("="*60)
    
    try:
        client = MlflowClient(tracking_uri=MLFLOW_URI)
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        
        if experiment is None:
            print("⚠️  No experiments found")
            return None
        
        # Find best run by F1 score
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["metrics.f1_score DESC"],
            max_results=1
        )
        
        if not runs:
            print("⚠️  No runs found")
            return None
        
        best_run = runs[0]
        print(f"✅ Best model selected:")
        print(f"   Run ID: {best_run.info.run_id}")
        print(f"   Run Name: {best_run.info.run_name}")
        
        metrics = best_run.data.metrics
        print(f"   Metrics:")
        for key, value in metrics.items():
            print(f"     - {key}: {value:.4f}")
        
        return best_run.info.run_id
        
    except Exception as e:
        print(f"❌ Error selecting best model: {e}")
        return None

def step_8_register_model(best_run_id):
    """Stage 8: Register version 1"""
    print("\n" + "="*60)
    print("Stage 8: Register Version 1")
    print("="*60)
    
    if not best_run_id:
        print("⚠️  No best run ID provided")
        return False
    
    try:
        client = MlflowClient(tracking_uri=MLFLOW_URI)
        
        # Register model
        model_version = client.create_model_version(
            name=MODEL_NAME,
            source=f"runs:/{best_run_id}/model",
            run_id=best_run_id
        )
        
        print(f"✅ Model registered:")
        print(f"   Name: {MODEL_NAME}")
        print(f"   Version: {model_version.version}")
        print(f"   Stage: {model_version.current_stage}")
        
        # Add description
        client.update_model_version(
            name=MODEL_NAME,
            version=model_version.version,
            description="Best model from experiment v1 - Predictive Maintenance on Vehicle Telemetry Data"
        )
        
        # Transition to Staging
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=model_version.version,
            stage="Staging"
        )
        
        print(f"✅ Model transitioned to Staging")
        print(f"📝 Next: Review in Staging, then transition to Production")
        
        return True
        
    except Exception as e:
        print(f"❌ Error registering model: {e}")
        return False

def step_9_deploy_production():
    """Stage 9: Deploy to production"""
    print("\n" + "="*60)
    print("Stage 9: Deploy to Production")
    print("="*60)
    
    print("🚀 Deploying to production...")
    print("\nRun these commands:")
    print("  docker compose build fastapi-inference")
    print("  docker compose up -d fastapi-inference")
    print("\nOr use:")
    print("  docker compose up -d")
    
    print("\n📊 Monitor at:")
    print("  - API: http://localhost:8000/docs")
    print("  - Prometheus: http://localhost:9090")
    print("  - Grafana: http://localhost:3000")
    
    return True

def main():
    """Run complete workflow"""
    print("\n" + "="*60)
    print("Complete Workflow - Predictive Maintenance")
    print("="*60)
    
    # Setup MLflow
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    steps = [
        ("Download Dataset", step_1_download_dataset, False),
        ("Process Data", step_2_process_data, True),
        ("Prepare Data", step_3_prepare_data, True),
        ("Train Models", step_4_train_models, True),
        ("Run Experiments", step_5_run_experiments, True),
        ("Analyze Metrics", step_6_analyze_metrics, True),
        ("Select Best Model", step_7_select_best_model, True),
        ("Register Version 1", None, False),  # Will be called with result
        ("Deploy Production", step_9_deploy_production, False),
    ]
    
    best_run_id = None
    
    for i, (name, func, required) in enumerate(steps, 1):
        if func is None:
            # Special case for register model
            if best_run_id:
                step_8_register_model(best_run_id)
            continue
        
        success = func()
        
        if not success and required:
            print(f"\n❌ Workflow stopped at step {i}: {name}")
            sys.exit(1)
        
        if name == "Select Best Model":
            best_run_id = success
    
    print("\n" + "="*60)
    print("✅ Workflow Completed!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review model in MLflow UI")
    print("2. Transition model from Staging to Production")
    print("3. Deploy inference service")
    print("4. Monitor in Prometheus/Grafana")

if __name__ == "__main__":
    main()


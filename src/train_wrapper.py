import os
import subprocess
import mlflow
import glob
from mlflow.tracking import MlflowClient

# mlflow setup
MLFLOW_URI = os.environ.get('MLFLOW_TRACKING_URI', 'http://localhost:5000')
mlflow.set_tracking_uri(MLFLOW_URI)
EXPERIMENT_NAME = os.environ.get('MLFLOW_EXPERIMENT', 'predictive-maintenance')
mlflow.set_experiment(EXPERIMENT_NAME)

# Scripts to run (comma separated)
#SCRIPTS = os.environ.get('TRAINING_SCRIPTS', 'classifier.py,rul.py,anomaly.py').split(',')
SCRIPTS = [
    "src/classifier.py",
    "src/rul.py",
    "src/anomaly.py"
]

# Default to project-level models folder
DEFAULT_MODEL_GLOB = './models/*.joblib'
MODEL_GLOBS = [g.strip() for g in os.environ.get('MODEL_GLOBS', DEFAULT_MODEL_GLOB).split(',') if g.strip()]

def run_scripts():
    for s in SCRIPTS:
        s = s.strip()
        if not s:
            continue
        if not os.path.exists(s):
            print(f"Warning: script {s} not found in working directory {os.getcwd()}")
            continue
        print(f"Running {s} ...")
        ret = subprocess.run(['python', s], check=False)
        if ret.returncode != 0:
            print(f"Warning: script {s} exited with code {ret.returncode}")

def find_and_log_artifacts():
    artifacts = []
    for g in MODEL_GLOBS:
        matches = glob.glob(g, recursive=True)
        if matches:
            artifacts.extend(matches)

    if not artifacts:
        # fallback: search common patterns anywhere in repo
        artifacts = glob.glob('**/*.joblib', recursive=True) + glob.glob('**/*.pkl', recursive=True)

    artifacts = sorted(set(artifacts))

    if not artifacts:
        print("No model artifacts found to log.")
        return []

    with mlflow.start_run() as run:
        mlflow.log_param('scripts', ','.join(SCRIPTS))
        for artifact in artifacts:
            print(f"Logging artifact {artifact}")
            mlflow.log_artifact(artifact, artifact_path='models')
        print('Logged artifacts for run_id=', run.info.run_id)
    return artifacts

if __name__ == '__main__':
    run_scripts()
    logged = find_and_log_artifacts()
    if logged:
        print('Artifacts logged to MLflow:')
        for a in logged:
            print(' -', a)
    else:
        print('No artifacts were logged.')

import os
import mlflow
import joblib
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

app = FastAPI()

MLFLOW_URI = os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
mlflow.set_tracking_uri(MLFLOW_URI)

MODEL_ARTIFACT_PATH = os.environ.get('MODEL_ARTIFACT_PATH', 'models')
RUN_ID = os.environ.get('MODEL_RUN_ID', None)  # optional: specific run id

inference_counter = Counter('inference_requests_total', 'Total inference requests', ['endpoint'])
inference_latency = Histogram('inference_latency_seconds', 'Inference latency seconds', ['endpoint'])

class Payload(BaseModel):
    data: dict

_model = None

from mlflow.tracking import MlflowClient
client = MlflowClient()

def load_model():
    global _model
    if _model is not None:
        return _model
    # find run
    if RUN_ID:
        run_id = RUN_ID
    else:
        # pick latest run in experiment (default experiment)
        experiments = client.list_experiments()
        if experiments:
            exp = experiments[0]
            runs = client.search_runs(exp.experiment_id, order_by=["attributes.start_time desc"], max_results=1)
            if not runs:
                raise RuntimeError('No runs found')
            run_id = runs[0].info.run_id
        else:
            raise RuntimeError('No experiments found')

    # download artifacts
    artifacts_dir = '/tmp/artifacts'
    if not os.path.exists(artifacts_dir):
        os.makedirs(artifacts_dir)
    try:
        local_path = client.download_artifacts(run_id, MODEL_ARTIFACT_PATH, artifacts_dir)
    except Exception as e:
        raise RuntimeError(f"Failed to download artifacts: {e}")

    # search for joblib/pkl
    import glob
    candidates = glob.glob(os.path.join(local_path, '**', '*.joblib'), recursive=True) + glob.glob(os.path.join(local_path, '**', '*.pkl'), recursive=True)
    if not candidates:
        raise RuntimeError('No joblib/pkl model artifacts found in downloaded artifacts')
    model_file = candidates[0]
    _model = joblib.load(model_file)
    return _model

@app.post('/predict')
async def predict(payload: Payload):
    endpoint = '/predict'
    inference_counter.labels(endpoint=endpoint).inc()
    with inference_latency.labels(endpoint=endpoint).time():
        model = load_model()
        df = pd.DataFrame([payload.data])
        preds = model.predict(df)
        return {'predictions': preds.tolist()}

@app.get('/metrics')
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.get('/health')
async def health():
    return {'status': 'ok'}

python - <<PY
import mlflow, joblib
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("ev_rul")
with mlflow.start_run():
    m = joblib.load("models/rul/lgbm_rul.joblib")
    mlflow.lightgbm.log_model(m, "lgbm_rul", registered_model_name="ev_rul")
print("logged")
PY

FROM python:3.10-slim
WORKDIR /workspace
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "mlflow_inference:app", "--host", "0.0.0.0", "--port", "8000"]

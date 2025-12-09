FROM python:3.10-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "mlflow_inference:app", "--host", "0.0.0.0", "--port", "8000"]

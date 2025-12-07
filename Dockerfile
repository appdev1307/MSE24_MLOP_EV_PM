FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY src /app/src
COPY models /app/models
ENV MODEL_DIR=/app/models
EXPOSE 8080
CMD ["python","/app/src/inference_server.py"]

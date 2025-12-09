FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends             build-essential             gcc             libpq-dev             curl             && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "train_wrapper.py"]

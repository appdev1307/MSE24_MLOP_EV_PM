FROM python:3.10-slim

WORKDIR /workspace

RUN apt-get update && \
    apt-get install -y gcc g++ git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install lightgbm

COPY . .

CMD ["python", "src/train_wrapper.py"]

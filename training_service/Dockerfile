FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn[standard] requests

# Copy training service
COPY main.py .

# Expose port
EXPOSE 8080

# Run training service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]


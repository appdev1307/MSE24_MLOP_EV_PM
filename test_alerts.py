import requests
import time
import subprocess

API_URL = "http://localhost:8000/predict"

def post(payload):
    return requests.post(API_URL, json={"data": payload}, timeout=5)

def get_fastapi_container():
    """
    Auto-detect fastapi-inference container name
    """
    result = subprocess.check_output(
        ["docker", "ps", "--format", "{{.Names}}"]
    ).decode()

    for line in result.splitlines():
        if "fastapi-inference" in line:
            return line

    raise RuntimeError("fastapi-inference container not found")

print("\n==============================")
print("1) TEST: HighAnomalyRate alert")
print("==============================")

# Trigger anomaly via real business rule
for i in range(30):
    post({"SoH": 0.3, "Charge_Cycles": 3000})
    time.sleep(1)

print(">> Sent anomaly requests. Wait ~1 minute.")
time.sleep(60)

print("\n==============================")
print("2) TEST: HighInferenceLatency")
print("==============================")

# Burst traffic to increase latency
for _ in range(5):
    for i in range(100):
        try:
            post({"SoH": 0.9, "Charge_Cycles": 10})
        except Exception:
            pass

print(">> Traffic burst sent. Wait ~1 minute.")
time.sleep(60)

print("\n==============================")
print("3) TEST: NoInferenceTraffic")
print("==============================")

print(">> Do nothing for 5 minutes...")
time.sleep(300)

print("\n==============================")
print("4) TEST: FastAPIInferenceDown")
print("==============================")

container_name = get_fastapi_container()
print(f">> Detected container: {container_name}")

print(">> Stopping fastapi-inference container")
subprocess.run(["docker", "stop", container_name])

print(">> Waiting 40 seconds")
time.sleep(40)

print(">> Restarting fastapi-inference container")
subprocess.run(["docker", "start", container_name])

print("\n==============================")
print("TEST COMPLETE")
print("==============================")
print("Check:")
print("  Prometheus:    http://localhost:9090")
print("  Alertmanager:  http://localhost:9093")

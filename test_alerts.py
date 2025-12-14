import requests
import time
import subprocess

API_BASE = "http://localhost:8000"
PREDICT_URL = f"{API_BASE}/predict"
METRICS_URL = f"{API_BASE}/metrics"

ANOMALY_PAYLOAD = {
    "SoC": 0.10,
    "SoH": 0.50,
    "Battery_Voltage": 200,
    "Battery_Current": 350,
    "Battery_Temperature": 95,
    "Charge_Cycles": 2000,
    "Motor_Temperature": 150,
    "Motor_Vibration": 0.6,
    "Power_Consumption": 50,
    "Brake_Pressure": 10,
    "Tire_Pressure": 10,
    "Ambient_Temperature": 80,
    "Ambient_Humidity": 0.95,
    "Load_Weight": 3000,
    "Driving_Speed": 200,
    "Distance_Traveled": 700000,
    "Idle_Time": 60,
    "Route_Roughness": 0.9,
    "Component_Health_Score": 0.1,
    "Failure_Probability": 0.95,
    "TTF": 50
}

NORMAL_PAYLOAD = {
    "SoC": 0.9,
    "SoH": 0.95,
    "Battery_Voltage": 350,
    "Battery_Current": 50,
    "Battery_Temperature": 25,
    "Charge_Cycles": 50
}

# ============================================================
# Helpers
# ============================================================

def wait_for_fastapi(timeout=60):
    print(">> Waiting for FastAPI readiness...")
    for _ in range(timeout):
        try:
            r = requests.get(METRICS_URL, timeout=1)
            if r.status_code == 200:
                print(">> FastAPI is READY")
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("FastAPI did not become ready")


def post(payload):
    return requests.post(
        PREDICT_URL,
        json={"data": payload},
        timeout=5
    )


def get_fastapi_container():
    result = subprocess.check_output(
        ["docker", "ps", "-a", "--format", "{{.Names}}"]
    ).decode()

    for line in result.splitlines():
        if line.startswith("mse24_mlop_ev_pm-fastapi-inference"):
            print(f">> Using FastAPI container: {line}")
            return line

    raise RuntimeError("fastapi-inference container not found")


def print_metric(name):
    metrics = requests.get(METRICS_URL).text
    for line in metrics.splitlines():
        if line.startswith(name):
            print("METRIC:", line)


# ============================================================
# TEST SEQUENCE
# ============================================================

wait_for_fastapi()

FASTAPI_CONTAINER = get_fastapi_container()

print("\n==============================")
print("1) TEST: HighAnomalyRate")
print("==============================")

for i in range(10):
    r = post(ANOMALY_PAYLOAD)
    print(f"Anomaly {i+1}: {r.json()}")

print_metric("anomaly_predictions_total")

print(">> Waiting 60s for alert to FIRE")
time.sleep(60)


print("\n==============================")
print("2) TEST: Normal Traffic")
print("==============================")

for i in range(5):
    r = post(NORMAL_PAYLOAD)
    print(f"Normal {i+1}: {r.json()}")
    time.sleep(1)

print(">> Waiting 30s")
time.sleep(30)


print("\n==============================")
print("3) TEST: No Traffic")
print("==============================")

print(">> Silence for 5 minutes (NoInferenceTraffic)")
time.sleep(300)


print("\n==============================")
print("4) TEST: FastAPIInferenceDown")
print("==============================")

subprocess.run(["docker", "stop", FASTAPI_CONTAINER], check=True)
print(">> Waiting 45s for Prometheus to detect DOWN")
time.sleep(45)

subprocess.run(["docker", "start", FASTAPI_CONTAINER], check=True)
print(">> Restarted FastAPI")

print("\n==============================")
print("TEST COMPLETE")
print("==============================")
print("Check:")
print("  Prometheus:   http://localhost:9090/alerts")
print("  Alertmanager: http://localhost:9093")

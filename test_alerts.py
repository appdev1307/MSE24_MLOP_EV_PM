import requests
import time
import subprocess
import json

# ==============================
# CONFIG
# ==============================
API_BASE = "http://localhost:8000"
PREDICT_URL = f"{API_BASE}/predict"
DOCS_URL = f"{API_BASE}/docs"  # Used for readiness check (more reliable than /metrics)

# Full anomaly payload — extreme values to trigger anomaly → fault → low RUL
ANOMALY_PAYLOAD = {
    "data": {
        "SoC": 0.10,
        "SoH": 0.50,
        "Battery_Voltage": 200.0,
        "Battery_Current": 350.0,
        "Battery_Temperature": 95.0,
        "Charge_Cycles": 2000.0,
        "Motor_Temperature": 150.0,
        "Motor_Vibration": 0.6,
        "Power_Consumption": 50.0,
        "Brake_Pressure": 10.0,
        "Tire_Pressure": 10.0,
        "Ambient_Temperature": 80.0,
        "Ambient_Humidity": 0.95,
        "Load_Weight": 3000.0,
        "Driving_Speed": 200.0,
        "Distance_Traveled": 700000.0,
        "Idle_Time": 60.0,
        "Route_Roughness": 0.9,
        "Component_Health_Score": 0.1,
        "Failure_Probability": 0.95,
        "TTF": 50.0
    }
}

# Normal payload — healthy values
NORMAL_PAYLOAD = {
    "data": {
        "SoC": 0.8,
        "SoH": 0.95,
        "Battery_Voltage": 360.0,
        "Battery_Current": 40.0,
        "Battery_Temperature": 28.0,
        "Charge_Cycles": 300.0,
        "Motor_Temperature": 60.0,
        "Motor_Vibration": 0.05,
        "Power_Consumption": 25.0,
        "Brake_Pressure": 50.0,
        "Tire_Pressure": 32.0,
        "Ambient_Temperature": 25.0,
        "Ambient_Humidity": 0.5,
        "Load_Weight": 1500.0,
        "Driving_Speed": 80.0,
        "Distance_Traveled": 50000.0,
        "Idle_Time": 10.0,
        "Route_Roughness": 0.2,
        "Component_Health_Score": 0.95,
        "Failure_Probability": 0.01,
        "TTF": 5000.0
    }
}

# ============================================================
# Helpers
# ============================================================
def wait_for_fastapi(timeout=180):
    """Wait until FastAPI Swagger UI is accessible."""
    print(">> Waiting for FastAPI to be ready (checking /docs)...")
    for i in range(timeout):
        try:
            r = requests.get(DOCS_URL, timeout=5)
            if r.status_code == 200 and "swagger-ui" in r.text.lower():
                print(">> FastAPI is READY! Swagger UI loaded.")
                return True
        except Exception:
            pass
        print(f"   Attempt {i+1}/{timeout} - still waiting...")
        time.sleep(1)
    raise RuntimeError("FastAPI did not become ready in time!")

def post(payload):
    """Send prediction request and return JSON response."""
    try:
        r = requests.post(PREDICT_URL, json=payload, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"HTTP {r.status_code}: {r.text}")
            return {"error": f"HTTP {r.status_code}", "detail": r.text}
    except Exception as e:
        print(f"Request failed: {e}")
        return {"error": str(e)}

def get_fastapi_container():
    """Find the running FastAPI inference container name."""
    try:
        result = subprocess.check_output(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            text=True
        )
        for line in result.splitlines():
            if "fastapi-inference" in line:
                print(f">> Found FastAPI container: {line.strip()}")
                return line.strip()
        raise RuntimeError("No fastapi-inference container found")
    except Exception as e:
        raise RuntimeError(f"Failed to list containers: {e}")

# ============================================================
# TEST SEQUENCE
# ============================================================
print("Starting End-to-End Inference & Alerting Test Suite\n")

wait_for_fastapi()
container_name = get_fastapi_container()

print("\n" + "="*60)
print("1) High Anomaly Rate Test → should trigger HighAnomalyRate alert")
print("="*60)
for i in range(10):
    result = post(ANOMALY_PAYLOAD)
    print(f"Anomaly Request {i+1}/10:")
    print(json.dumps(result, indent=2))
    time.sleep(0.5)

print("\n>> Waiting 70 seconds for Prometheus to evaluate HighAnomalyRate...")
time.sleep(70)

print("\n" + "="*60)
print("2) Normal Traffic → should reduce anomaly rate")
print("="*60)
for i in range(5):
    result = post(NORMAL_PAYLOAD)
    print(f"Normal Request {i+1}/5:")
    print(json.dumps(result, indent=2))
    time.sleep(1)

print("\n>> Waiting 30 seconds...")
time.sleep(30)

print("\n" + "="*60)
print("3) No Traffic Period → should trigger NoInferenceTraffic alert")
print("="*60)
print(">> Silence for 5 minutes...")
time.sleep(300)

print("\n" + "="*60)
print("4) Service Down/Up Test → should trigger FastAPIInferenceDown alert")
print("="*60)
print(">> Stopping FastAPI container...")
subprocess.run(["docker", "stop", container_name], check=True)
print(">> Waiting 60 seconds for DOWN detection...")
time.sleep(60)

print(">> Restarting FastAPI container...")
subprocess.run(["docker", "start", container_name], check=True)
print(">> Waiting 20 seconds for recovery...")
time.sleep(20)
wait_for_fastapi(timeout=60)  # Confirm it's back

print("\n" + "="*70)
print("TEST SUITE COMPLETE!")
print("="*70)
print("Now verify alerts in your monitoring system:")
print("   • Prometheus Alerts:  http://localhost:9090/alerts")
print("   • Alertmanager:       http://localhost:9093")
print("\nExpected alerts to have fired:")
print("   - HighAnomalyRate")
print("   - NoInferenceTraffic")
print("   - FastAPIInferenceDown (firing + resolved)")
print("\nWell done! Your full MLOps + Observability pipeline is working! 🎉")
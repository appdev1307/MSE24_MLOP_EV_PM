import requests
import time
import subprocess
import json

API_URL = "http://localhost:8000/predict"

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


def post(payload):
    return requests.post(
        API_URL,
        json={"data": payload},
        timeout=5
    )


def get_fastapi_container():
    result = subprocess.check_output(
        ["docker", "ps", "--format", "{{.Names}}"]
    ).decode()

    for line in result.splitlines():
        if "fastapi-inference" in line:
            return line

    raise RuntimeError("fastapi-inference container not found")


print("\n==============================")
print("1) TEST: HighAnomalyRate")
print("==============================")

# Send anomalies fast enough to trigger rate()
for i in range(15):
    r = post(ANOMALY_PAYLOAD)
    print(f"Anomaly {i+1}: {r.json()}")
    time.sleep(2)

print(">> Waiting 90s for Prometheus evaluation")
time.sleep(90)


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
print("3) TEST: No Traffic (Silence)")
print("==============================")

print(">> Do nothing for 5 minutes (NoInferenceTraffic alert)")
time.sleep(300)


print("\n==============================")
print("4) TEST: FastAPIInferenceDown")
print("==============================")

container = get_fastapi_container()
print(f">> Detected container: {container}")

print(">> Stopping inference container")
subprocess.run(["docker", "stop", container])

print(">> Waiting 60 seconds")
time.sleep(60)

print(">> Restarting inference container")
subprocess.run(["docker", "start", container])


print("\n==============================")
print("TEST COMPLETE")
print("==============================")
print("Check:")
print("  Prometheus:   http://localhost:9090/alerts")
print("  Alertmanager: http://localhost:9093")

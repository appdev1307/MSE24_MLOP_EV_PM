import requests
import json
import os

API_URL = os.getenv("API_URL", "http://localhost:8000/predict")
TIMEOUT = 10


def run_test_case(name, data, expect_fault: bool):
    print(f"\n==================== {name} ====================")

    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"data": data},
            timeout=TIMEOUT
        )
    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", e)
        return

    print("HTTP Status:", response.status_code)

    if response.status_code != 200:
        print("❌ API Error")
        print(response.text)
        return

    try:
        result = response.json()
        print(json.dumps(result, indent=2))
    except Exception:
        print("❌ Invalid JSON response")
        print(response.text)
        return

    # ===================== BASIC ASSERTIONS =====================
    assert "IF_Anomaly" in result, "Missing IF_Anomaly"
    assert "status" in result, "Missing status"

    if expect_fault:
        assert result["IF_Anomaly"] == 1, "Expected anomaly but got normal"
        assert result.get("is_fault", True), "Expected fault flag"
    else:
        assert result["IF_Anomaly"] == 0, "Expected normal but got anomaly"

    print("✅ Test passed")


# ===============================================================
# TEST CASES
# ===============================================================

# 1️⃣ NORMAL OPERATION
run_test_case(
    name="NORMAL CASE",
    expect_fault=False,
    data={
        "SoC": 0.8,
        "SoH": 0.95,
        "Battery_Voltage": 420,
        "Battery_Current": 40,
        "Battery_Temperature": 28,
        "Charge_Cycles": 150,
        "Motor_Temperature": 45,
        "Motor_Vibration": 0.05,
        "Power_Consumption": 18,
        "Brake_Pressure": 45,
        "Tire_Pressure": 32,
        "Ambient_Temperature": 25,
        "Ambient_Humidity": 0.4,
        "Load_Weight": 800,
        "Driving_Speed": 60,
        "Distance_Traveled": 30000,
        "Idle_Time": 5,
        "Route_Roughness": 0.1,
        "Component_Health_Score": 0.95,
        "Failure_Probability": 0.02,
        "TTF": 800
    }
)

# 2️⃣ THERMAL RUNAWAY RISK
run_test_case(
    name="THERMAL RUNAWAY RISK",
    expect_fault=True,
    data={
        "SoC": 0.2,
        "SoH": 0.7,
        "Battery_Voltage": 200,
        "Battery_Current": 350,
        "Battery_Temperature": 95,
        "Charge_Cycles": 1200,
        "Motor_Temperature": 70,
        "Motor_Vibration": 0.2,
        "Power_Consumption": 55,
        "Brake_Pressure": 30,
        "Tire_Pressure": 28,
        "Ambient_Temperature": 80,
        "Ambient_Humidity": 0.95,
        "Load_Weight": 2500,
        "Driving_Speed": 110,
        "Distance_Traveled": 400000,
        "Idle_Time": 20,
        "Route_Roughness": 0.6,
        "Component_Health_Score": 0.3,
        "Failure_Probability": 0.95,
        "TTF": 80
    }
)

# 3️⃣ MOTOR OVERHEAT
run_test_case(
    name="MOTOR OVERHEAT",
    expect_fault=True,
    data={
        "SoC": 0.6,
        "SoH": 0.85,
        "Battery_Voltage": 380,
        "Battery_Current": 180,
        "Battery_Temperature": 45,
        "Charge_Cycles": 500,
        "Motor_Temperature": 150,
        "Motor_Vibration": 0.6,
        "Power_Consumption": 70,
        "Brake_Pressure": 20,
        "Tire_Pressure": 30,
        "Ambient_Temperature": 45,
        "Ambient_Humidity": 0.6,
        "Load_Weight": 3000,
        "Driving_Speed": 200,
        "Distance_Traveled": 250000,
        "Idle_Time": 10,
        "Route_Roughness": 0.9,
        "Component_Health_Score": 0.4,
        "Failure_Probability": 0.85,
        "TTF": 120
    }
)

# 4️⃣ BATTERY AGING
run_test_case(
    name="BATTERY AGING",
    expect_fault=True,
    data={
        "SoC": 0.1,
        "SoH": 0.5,
        "Battery_Voltage": 200,
        "Battery_Current": 90,
        "Battery_Temperature": 40,
        "Charge_Cycles": 2000,
        "Motor_Temperature": 55,
        "Motor_Vibration": 0.25,
        "Power_Consumption": 30,
        "Brake_Pressure": 35,
        "Tire_Pressure": 29,
        "Ambient_Temperature": 35,
        "Ambient_Humidity": 0.5,
        "Load_Weight": 1500,
        "Driving_Speed": 70,
        "Distance_Traveled": 700000,
        "Idle_Time": 60,
        "Route_Roughness": 0.4,
        "Component_Health_Score": 0.1,
        "Failure_Probability": 0.9,
        "TTF": 50
    }
)

# 5️⃣ MULTI-FAULT CRITICAL
run_test_case(
    name="MULTI-FAULT CRITICAL",
    expect_fault=True,
    data={
        "SoC": 0.05,
        "SoH": 0.3,
        "Battery_Voltage": 180,
        "Battery_Current": 400,
        "Battery_Temperature": 110,
        "Charge_Cycles": 3000,
        "Motor_Temperature": 170,
        "Motor_Vibration": 0.8,
        "Power_Consumption": 90,
        "Brake_Pressure": 10,
        "Tire_Pressure": 18,
        "Ambient_Temperature": 85,
        "Ambient_Humidity": 0.98,
        "Load_Weight": 3500,
        "Driving_Speed": 220,
        "Distance_Traveled": 900000,
        "Idle_Time": 120,
        "Route_Roughness": 1.0,
        "Component_Health_Score": 0.05,
        "Failure_Probability": 0.99,
        "TTF": 20
    }
)

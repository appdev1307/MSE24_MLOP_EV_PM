import requests
import json

URL = "http://localhost:8000/predict"

# ===========================
# 1) NORMAL CASE (No Fault)
# ===========================
case_normal = {
    "data": {
        "SoC": 0.80,
        "SoH": 0.95,
        "Battery_Voltage": 420,
        "Battery_Current": 50,
        "Battery_Temperature": 30,
        "Charge_Cycles": 300,
        "Motor_Temperature": 60,
        "Motor_Vibration": 0.1,
        "Power_Consumption": 20,
        "Brake_Pressure": 30,
        "Tire_Pressure": 32,
        "Ambient_Temperature": 25,
        "Ambient_Humidity": 0.5,
        "Load_Weight": 500,
        "Driving_Speed": 60,
        "Distance_Traveled": 20000,
        "Idle_Time": 5,
        "Route_Roughness": 0.2,
        "Component_Health_Score": 0.95,
        "Failure_Probability": 0.01,
        "TTF": 5000
    }
}

# =========================================================
# 2) THERMAL RUNAWAY RISK (High Temp + High Current)
# =========================================================
case_thermal_runaway = {
    "data": {
        "SoC": 0.50,
        "SoH": 0.80,
        "Battery_Voltage": 390,
        "Battery_Current": 350,
        "Battery_Temperature": 98,
        "Charge_Cycles": 1500,
        "Motor_Temperature": 80,
        "Motor_Vibration": 0.3,
        "Power_Consumption": 40,
        "Brake_Pressure": 25,
        "Tire_Pressure": 28,
        "Ambient_Temperature": 40,
        "Ambient_Humidity": 0.7,
        "Load_Weight": 2000,
        "Driving_Speed": 80,
        "Distance_Traveled": 250000,
        "Idle_Time": 30,
        "Route_Roughness": 0.4,
        "Component_Health_Score": 0.4,
        "Failure_Probability": 0.65,
        "TTF": 200
    }
}

# =========================================================
# 3) MOTOR OVERHEAT (Motor temp high + vibration)
# =========================================================
case_motor_overheat = {
    "data": {
        "SoC": 0.65,
        "SoH": 0.70,
        "Battery_Voltage": 410,
        "Battery_Current": 150,
        "Battery_Temperature": 40,
        "Charge_Cycles": 1200,
        "Motor_Temperature": 140,
        "Motor_Vibration": 0.8,
        "Power_Consumption": 60,
        "Brake_Pressure": 20,
        "Tire_Pressure": 30,
        "Ambient_Temperature": 35,
        "Ambient_Humidity": 0.8,
        "Load_Weight": 1000,
        "Driving_Speed": 100,
        "Distance_Traveled": 300000,
        "Idle_Time": 20,
        "Route_Roughness": 0.7,
        "Component_Health_Score": 0.3,
        "Failure_Probability": 0.85,
        "TTF": 100
    }
}

# =========================================================
# 4) BATTERY AGING (Low SoH + High cycles)
# =========================================================
case_battery_aging = {
    "data": {
        "SoC": 0.20,
        "SoH": 0.40,
        "Battery_Voltage": 350,
        "Battery_Current": 100,
        "Battery_Temperature": 55,
        "Charge_Cycles": 2500,
        "Motor_Temperature": 70,
        "Motor_Vibration": 0.3,
        "Power_Consumption": 25,
        "Brake_Pressure": 20,
        "Tire_Pressure": 30,
        "Ambient_Temperature": 20,
        "Ambient_Humidity": 0.4,
        "Load_Weight": 800,
        "Driving_Speed": 50,
        "Distance_Traveled": 350000,
        "Idle_Time": 10,
        "Route_Roughness": 0.3,
        "Component_Health_Score": 0.2,
        "Failure_Probability": 0.55,
        "TTF": 150
    }
}

# =========================================================
# SEND REQUESTS
# =========================================================
test_cases = {
    "NORMAL CASE": case_normal,
    "THERMAL RUNAWAY RISK": case_thermal_runaway,
    "MOTOR OVERHEAT": case_motor_overheat,
    "BATTERY AGING": case_battery_aging
}

print("\n=================== API TEST RESULTS ===================")

for name, case in test_cases.items():
    print(f"\n--- {name} ---")
    response = requests.post(URL, json=case)
    print(json.dumps(response.json(), indent=4))

print("\n========================================================\n")

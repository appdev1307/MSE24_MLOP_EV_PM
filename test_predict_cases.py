"""
Test Cases cho API /predict - Hiểu Cách Hệ Thống Dự Đoán

File này chứa các test case minh họa cách hệ thống dự đoán lỗi xe điện.
Mỗi test case mô phỏng một tình huống thực tế và giải thích kết quả mong đợi.

Cách chạy:
    python test_predict_cases.py
    
Hoặc chạy từng test case riêng lẻ bằng cách import và gọi hàm test_predict().
"""

import requests
import json
import time
import sys

API_BASE = "http://localhost:8000"
PREDICT_URL = f"{API_BASE}/predict"

# ============================================================
# TEST CASE 1: XE BÌNH THƯỜNG - KHÔNG CÓ VẤN ĐỀ
# ============================================================
TEST_CASE_1_NORMAL = {
    "name": "Xe bình thường - Không có vấn đề",
    "description": """
    Tình huống: Xe điện mới, tất cả cảm biến đều trong ngưỡng bình thường.
    
    Đặc điểm:
    - SoC (mức pin): 90% - đầy đủ
    - SoH (sức khỏe pin): 95% - rất tốt
    - Nhiệt độ pin: 25°C - bình thường
    - Số chu kỳ sạc: 50 - còn mới
    - Tất cả thông số khác đều trong ngưỡng an toàn
    
    Kết quả mong đợi:
    - IF_Anomaly = 0 (không có bất thường)
    - status = "Normal - no fault detected"
    - Không chạy classifier và RUL (vì không có anomaly)
    """,
    "payload": {
        "data": {
            "SoC": 0.9,                    # Mức pin: 90% - đầy đủ
            "SoH": 0.95,                   # Sức khỏe pin: 95% - rất tốt
            "Battery_Voltage": 350,        # Điện áp: 350V - bình thường
            "Battery_Current": 50,         # Dòng điện: 50A - bình thường
            "Battery_Temperature": 25,     # Nhiệt độ pin: 25°C - mát
            "Charge_Cycles": 50,          # Đã sạc 50 lần - còn mới
            "Motor_Temperature": 30,      # Nhiệt độ motor: 30°C - bình thường
            "Motor_Vibration": 0.1,       # Độ rung: 0.1 - ổn định
            "Power_Consumption": 20,       # Tiêu thụ điện: 20kW - bình thường
            "Brake_Pressure": 50,         # Áp suất phanh: 50 - tốt
            "Tire_Pressure": 30,          # Áp suất lốp: 30 PSI - đúng
            "Ambient_Temperature": 25,    # Nhiệt độ môi trường: 25°C
            "Ambient_Humidity": 0.5,      # Độ ẩm: 50% - bình thường
            "Load_Weight": 1000,          # Trọng tải: 1000kg - nhẹ
            "Driving_Speed": 60,          # Tốc độ: 60km/h - vừa phải
            "Distance_Traveled": 50000,   # Quãng đường: 50,000km
            "Idle_Time": 10,              # Thời gian chờ: 10 phút
            "Route_Roughness": 0.3,       # Độ gồ ghề đường: 0.3 - bằng phẳng
            "Component_Health_Score": 0.9, # Điểm sức khỏe: 90% - tốt
            "Failure_Probability": 0.1,    # Xác suất hỏng: 10% - thấp
            "TTF": 1000                   # Thời gian đến hỏng: 1000 chu kỳ
        }
    },
    "expected": {
        "IF_Anomaly": 0,
        "status": "Normal - no fault detected"
    }
}

# ============================================================
# TEST CASE 2: PIN ĐÃ GIÀ - BATTERY AGING
# ============================================================
TEST_CASE_2_BATTERY_AGING = {
    "name": "Pin đã già - Battery Aging",
    "description": """
    Tình huống: Xe đã sử dụng lâu, pin bị lão hóa.
    
    Đặc điểm:
    - SoH (sức khỏe pin): 50% - đã giảm nhiều (bình thường > 80%)
    - Số chu kỳ sạc: 2500 - rất nhiều (nguy hiểm > 2000)
    - Nhiệt độ pin: 40°C - hơi cao
    - Điện áp: 280V - thấp hơn bình thường (350V)
    
    Kết quả mong đợi:
    - IF_Anomaly = 1 (có bất thường - do rule override: SoH < 60% hoặc Charge_Cycles > 2000)
    - classifier_label = "Battery Aging" hoặc mã số tương ứng
    - is_fault = true (có lỗi)
    - RUL_estimated = số chu kỳ còn lại (ví dụ: 200-500)
    """,
    "payload": {
        "data": {
            "SoC": 0.6,                    # Mức pin: 60% - thấp
            "SoH": 0.5,                    # Sức khỏe pin: 50% - ĐÃ GIÀ!
            "Battery_Voltage": 280,       # Điện áp: 280V - THẤP (bình thường 350V)
            "Battery_Current": 80,        # Dòng điện: 80A - cao
            "Battery_Temperature": 40,    # Nhiệt độ pin: 40°C - hơi nóng
            "Charge_Cycles": 2500,        # Đã sạc 2500 lần - QUÁ NHIỀU! (> 2000)
            "Motor_Temperature": 35,      # Nhiệt độ motor: 35°C - bình thường
            "Motor_Vibration": 0.2,       # Độ rung: 0.2 - ổn định
            "Power_Consumption": 25,      # Tiêu thụ điện: 25kW
            "Brake_Pressure": 45,         # Áp suất phanh: 45
            "Tire_Pressure": 28,          # Áp suất lốp: 28 PSI - hơi thấp
            "Ambient_Temperature": 30,    # Nhiệt độ môi trường: 30°C
            "Ambient_Humidity": 0.6,      # Độ ẩm: 60%
            "Load_Weight": 1500,          # Trọng tải: 1500kg
            "Driving_Speed": 70,          # Tốc độ: 70km/h
            "Distance_Traveled": 200000,  # Quãng đường: 200,000km - nhiều
            "Idle_Time": 5,               # Thời gian chờ: 5 phút
            "Route_Roughness": 0.4,       # Độ gồ ghề: 0.4
            "Component_Health_Score": 0.5, # Điểm sức khỏe: 50% - thấp
            "Failure_Probability": 0.7,   # Xác suất hỏng: 70% - cao
            "TTF": 300                    # Thời gian đến hỏng: 300 chu kỳ
        }
    },
    "expected": {
        "IF_Anomaly": 1,
        "is_fault": True,
        "classifier_label": "Battery Aging"  # hoặc mã số tương ứng
    }
}

# ============================================================
# TEST CASE 3: MOTOR QUÁ NÓNG - MOTOR OVERHEAT
# ============================================================
TEST_CASE_3_MOTOR_OVERHEAT = {
    "name": "Motor quá nóng - Motor Overheat",
    "description": """
    Tình huống: Motor hoạt động quá tải, nhiệt độ tăng cao.
    
    Đặc điểm:
    - Nhiệt độ motor: 150°C - QUÁ NÓNG! (bình thường < 80°C)
    - Nhiệt độ pin: 60°C - cũng cao
    - Tiêu thụ điện: 50kW - rất cao
    - Tốc độ: 120km/h - cao tốc
    - Độ rung motor: 0.6 - cao (bình thường < 0.3)
    
    Kết quả mong đợi:
    - IF_Anomaly = 1 (có bất thường)
    - classifier_label = "Motor Overheat" hoặc mã số tương ứng
    - is_fault = true
    - RUL_estimated = số chu kỳ còn lại
    """,
    "payload": {
        "data": {
            "SoC": 0.7,
            "SoH": 0.85,
            "Battery_Voltage": 320,
            "Battery_Current": 100,        # Dòng điện cao
            "Battery_Temperature": 60,    # Pin cũng nóng
            "Charge_Cycles": 800,         # Còn ít chu kỳ
            "Motor_Temperature": 150,     # MOTOR QUÁ NÓNG! (> 80°C)
            "Motor_Vibration": 0.6,       # Độ rung cao - bất thường
            "Power_Consumption": 50,      # Tiêu thụ rất cao
            "Brake_Pressure": 40,
            "Tire_Pressure": 32,
            "Ambient_Temperature": 35,    # Môi trường nóng
            "Ambient_Humidity": 0.7,
            "Load_Weight": 2500,          # Trọng tải cao
            "Driving_Speed": 120,         # Tốc độ cao
            "Distance_Traveled": 150000,
            "Idle_Time": 2,
            "Route_Roughness": 0.6,       # Đường gồ ghề
            "Component_Health_Score": 0.6,
            "Failure_Probability": 0.6,
            "TTF": 400
        }
    },
    "expected": {
        "IF_Anomaly": 1,
        "is_fault": True,
        "classifier_label": "Motor Overheat"  # hoặc mã số tương ứng
    }
}

# ============================================================
# TEST CASE 4: PHANH CÓ VẤN ĐỀ - BRAKE SYSTEM FAILURE
# ============================================================
TEST_CASE_4_BRAKE_FAILURE = {
    "name": "Hệ thống phanh có vấn đề - Brake System Failure",
    "description": """
    Tình huống: Hệ thống phanh bị mòn, áp suất thấp.
    
    Đặc điểm:
    - Áp suất phanh: 10 - RẤT THẤP! (bình thường > 40)
    - Mòn phanh: 0.9 - gần hết (bình thường < 0.5)
    - Hiệu suất phanh tái sinh: 0.3 - thấp
    - Tốc độ: 80km/h
    - Quãng đường: 300,000km - xe cũ
    
    Kết quả mong đợi:
    - IF_Anomaly = 1
    - classifier_label = "Brake System Failure" hoặc mã số tương ứng
    - is_fault = true
    - RUL_estimated = số chu kỳ còn lại
    """,
    "payload": {
        "data": {
            "SoC": 0.8,
            "SoH": 0.75,
            "Battery_Voltage": 340,
            "Battery_Current": 60,
            "Battery_Temperature": 30,
            "Charge_Cycles": 1500,
            "Motor_Temperature": 50,
            "Motor_Vibration": 0.3,
            "Power_Consumption": 30,
            "Brake_Pressure": 10,         # ÁP SUẤT PHANH RẤT THẤP!
            "Brake_Pad_Wear": 0.9,        # Mòn phanh gần hết
            "Reg_Brake_Efficiency": 0.3,  # Hiệu suất phanh tái sinh thấp
            "Tire_Pressure": 25,          # Lốp cũng hơi non
            "Ambient_Temperature": 28,
            "Ambient_Humidity": 0.5,
            "Load_Weight": 2000,
            "Driving_Speed": 80,
            "Distance_Traveled": 300000,  # Xe đã chạy nhiều
            "Idle_Time": 8,
            "Route_Roughness": 0.5,
            "Component_Health_Score": 0.4, # Sức khỏe tổng thể thấp
            "Failure_Probability": 0.8,     # Xác suất hỏng cao
            "TTF": 200
        }
    },
    "expected": {
        "IF_Anomaly": 1,
        "is_fault": True,
        "classifier_label": "Brake System Failure"  # hoặc mã số tương ứng
    }
}

# ============================================================
# TEST CASE 5: NHIỆT ĐỘ QUÁ CAO - THERMAL RUNAWAY RISK
# ============================================================
TEST_CASE_5_THERMAL_RUNAWAY = {
    "name": "Nguy cơ nhiệt độ tăng vọt - Thermal Runaway Risk",
    "description": """
    Tình huống: Pin và motor đều quá nóng, nguy cơ cháy nổ.
    
    Đặc điểm:
    - Nhiệt độ pin: 95°C - CỰC KỲ NÓNG! (nguy hiểm > 60°C)
    - Nhiệt độ motor: 140°C - rất nóng
    - Nhiệt độ môi trường: 45°C - nóng
    - Độ ẩm: 95% - rất cao
    - Dòng điện: 350A - rất cao
    
    Kết quả mong đợi:
    - IF_Anomaly = 1 (chắc chắn - nhiệt độ quá cao)
    - classifier_label = "Thermal Runaway Risk" hoặc mã số tương ứng
    - is_fault = true
    - RUL_estimated = số chu kỳ còn lại (có thể rất thấp)
    """,
    "payload": {
        "data": {
            "SoC": 0.8,
            "SoH": 0.7,
            "Battery_Voltage": 300,
            "Battery_Current": 350,       # Dòng điện rất cao
            "Battery_Temperature": 95,    # PIN CỰC KỲ NÓNG! (> 60°C nguy hiểm)
            "Charge_Cycles": 1200,
            "Motor_Temperature": 140,     # Motor cũng rất nóng
            "Motor_Vibration": 0.5,
            "Power_Consumption": 60,      # Tiêu thụ rất cao
            "Brake_Pressure": 35,
            "Tire_Pressure": 30,
            "Ambient_Temperature": 45,    # Môi trường nóng
            "Ambient_Humidity": 0.95,     # Độ ẩm rất cao
            "Load_Weight": 3000,          # Trọng tải cao
            "Driving_Speed": 100,
            "Distance_Traveled": 180000,
            "Idle_Time": 1,               # Ít nghỉ
            "Route_Roughness": 0.8,       # Đường rất gồ ghề
            "Component_Health_Score": 0.3, # Sức khỏe kém
            "Failure_Probability": 0.9,    # Xác suất hỏng rất cao
            "TTF": 100                    # Thời gian đến hỏng ngắn
        }
    },
    "expected": {
        "IF_Anomaly": 1,
        "is_fault": True,
        "classifier_label": "Thermal Runaway Risk"  # hoặc mã số tương ứng
    }
}

# ============================================================
# TEST CASE 6: CẢM BIẾN LỆCH - SENSOR DRIFT
# ============================================================
TEST_CASE_6_SENSOR_DRIFT = {
    "name": "Cảm biến bị lệch - Sensor Drift",
    "description": """
    Tình huống: Cảm biến bị lệch, đọc sai giá trị.
    
    Đặc điểm:
    - Các giá trị không nhất quán với nhau
    - Component_Health_Score: 0.2 - rất thấp
    - Một số giá trị bất thường nhưng không rõ ràng là lỗi gì
    - Có thể là lỗi cảm biến, không phải lỗi thực sự của xe
    
    Kết quả mong đợi:
    - IF_Anomaly = 1 (phát hiện bất thường)
    - classifier_label = "Sensor Drift" hoặc mã số tương ứng
    - is_fault = true
    """,
    "payload": {
        "data": {
            "SoC": 0.5,
            "SoH": 0.6,
            "Battery_Voltage": 250,       # Hơi thấp
            "Battery_Current": 120,       # Hơi cao
            "Battery_Temperature": 35,    # Bình thường
            "Charge_Cycles": 1000,
            "Motor_Temperature": 45,      # Bình thường
            "Motor_Vibration": 0.4,       # Hơi cao
            "Power_Consumption": 35,
            "Brake_Pressure": 30,         # Hơi thấp
            "Tire_Pressure": 22,          # Hơi thấp
            "Ambient_Temperature": 30,
            "Ambient_Humidity": 0.6,
            "Load_Weight": 1800,
            "Driving_Speed": 65,
            "Distance_Traveled": 120000,
            "Idle_Time": 15,
            "Route_Roughness": 0.4,
            "Component_Health_Score": 0.2, # Rất thấp - có thể cảm biến lệch
            "Failure_Probability": 0.5,
            "TTF": 600
        }
    },
    "expected": {
        "IF_Anomaly": 1,
        "is_fault": True,
        "classifier_label": "Sensor Drift"  # hoặc mã số tương ứng
    }
}

# ============================================================
# TEST CASE 7: XE MỚI NHƯNG CÓ DẤU HIỆU BẤT THƯỜNG
# ============================================================
TEST_CASE_7_NEW_CAR_ANOMALY = {
    "name": "Xe mới nhưng có dấu hiệu bất thường",
    "description": """
    Tình huống: Xe mới (ít chu kỳ sạc) nhưng có một số giá trị bất thường.
    
    Đặc điểm:
    - Charge_Cycles: 100 - còn rất mới
    - SoH: 0.9 - tốt
    - NHƯNG: Nhiệt độ pin = 70°C - cao bất thường
    - Motor_Vibration: 0.7 - rung mạnh
    
    Kết quả mong đợi:
    - IF_Anomaly = 1 (phát hiện bất thường)
    - Có thể là lỗi sản xuất hoặc vấn đề mới phát sinh
    - is_fault = true
    - RUL_estimated có thể cao (vì xe mới)
    """,
    "payload": {
        "data": {
            "SoC": 0.85,
            "SoH": 0.9,                   # Pin còn tốt
            "Battery_Voltage": 345,
            "Battery_Current": 90,
            "Battery_Temperature": 70,    # NÓNG BẤT THƯỜNG cho xe mới
            "Charge_Cycles": 100,         # XE MỚI - chỉ 100 lần sạc
            "Motor_Temperature": 80,      # Motor cũng nóng
            "Motor_Vibration": 0.7,       # RUNG MẠNH - bất thường
            "Power_Consumption": 40,
            "Brake_Pressure": 50,
            "Tire_Pressure": 32,
            "Ambient_Temperature": 30,
            "Ambient_Humidity": 0.5,
            "Load_Weight": 1200,
            "Driving_Speed": 90,
            "Distance_Traveled": 10000,   # Xe mới - ít km
            "Idle_Time": 5,
            "Route_Roughness": 0.5,
            "Component_Health_Score": 0.7,
            "Failure_Probability": 0.4,
            "TTF": 800
        }
    },
    "expected": {
        "IF_Anomaly": 1,
        "is_fault": True
    }
}

# ============================================================
# TEST CASE 8: XE CŨ NHƯNG VẪN HOẠT ĐỘNG TỐT
# ============================================================
TEST_CASE_8_OLD_CAR_NORMAL = {
    "name": "Xe cũ nhưng vẫn hoạt động tốt",
    "description": """
    Tình huống: Xe đã sử dụng lâu nhưng được bảo trì tốt.
    
    Đặc điểm:
    - Charge_Cycles: 1800 - nhiều nhưng chưa đến ngưỡng nguy hiểm (2000)
    - SoH: 0.65 - giảm nhưng còn chấp nhận được (> 60%)
    - Tất cả thông số khác đều trong ngưỡng an toàn
    - Component_Health_Score: 0.75 - tốt
    
    Kết quả mong đợi:
    - IF_Anomaly = 0 (không có bất thường)
    - status = "Normal - no fault detected"
    - Xe cũ nhưng vẫn an toàn
    """,
    "payload": {
        "data": {
            "SoC": 0.75,
            "SoH": 0.65,                  # Giảm nhưng > 60% - còn OK
            "Battery_Voltage": 330,
            "Battery_Current": 70,
            "Battery_Temperature": 32,   # Bình thường
            "Charge_Cycles": 1800,       # Nhiều nhưng < 2000 - còn OK
            "Motor_Temperature": 45,      # Bình thường
            "Motor_Vibration": 0.25,     # Ổn định
            "Power_Consumption": 28,
            "Brake_Pressure": 48,         # Tốt
            "Tire_Pressure": 30,
            "Ambient_Temperature": 28,
            "Ambient_Humidity": 0.55,
            "Load_Weight": 1500,
            "Driving_Speed": 65,
            "Distance_Traveled": 180000, # Nhiều km
            "Idle_Time": 12,
            "Route_Roughness": 0.35,
            "Component_Health_Score": 0.75, # Tốt
            "Failure_Probability": 0.25,   # Thấp
            "TTF": 700
        }
    },
    "expected": {
        "IF_Anomaly": 0,
        "status": "Normal - no fault detected"
    }
}

# ============================================================
# TEST CASE 9: DỮ LIỆU THIẾU - EDGE CASE
# ============================================================
TEST_CASE_9_MISSING_DATA = {
    "name": "Dữ liệu thiếu một số trường",
    "description": """
    Tình huống: Một số cảm biến không gửi được dữ liệu.
    
    Đặc điểm:
    - Thiếu một số trường (sẽ được fill = 0.0)
    - Các trường có giá trị đều bình thường
    
    Kết quả mong đợi:
    - Hệ thống vẫn hoạt động (fill missing = 0.0)
    - Có thể ảnh hưởng đến độ chính xác dự đoán
    """,
    "payload": {
        "data": {
            "SoC": 0.8,
            "SoH": 0.85,
            "Battery_Voltage": 350,
            "Battery_Current": 60,
            "Battery_Temperature": 28,
            "Charge_Cycles": 500,
            # Thiếu một số trường - sẽ được fill = 0.0
        }
    },
    "expected": {
        # Có thể vẫn trả về kết quả, nhưng có thể không chính xác
    }
}

# ============================================================
# HÀM TEST
# ============================================================

def test_predict(payload, test_name, description, expected=None):
    """
    Test một trường hợp dự đoán.
    
    Args:
        payload: Dữ liệu gửi lên API
        test_name: Tên test case
        description: Mô tả tình huống
        expected: Kết quả mong đợi (optional)
    """
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)
    print(f"Mô tả: {description}")
    print("\n📤 Gửi request...")
    
    try:
        response = requests.post(PREDICT_URL, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Kết quả nhận được:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # So sánh với expected
            if expected:
                print("\n🔍 So sánh với kết quả mong đợi:")
                for key, expected_value in expected.items():
                    actual_value = result.get(key)
                    if actual_value == expected_value:
                        print(f"  ✅ {key}: {actual_value} (đúng)")
                    else:
                        print(f"  ⚠️  {key}: {actual_value} (mong đợi: {expected_value})")
            
            # Giải thích kết quả
            print("\n📝 Giải thích kết quả:")
            if result.get("IF_Anomaly") == 0:
                print("  - Không phát hiện bất thường → Xe hoạt động bình thường")
                print("  - Hệ thống không chạy classifier và RUL (tiết kiệm tài nguyên)")
            else:
                print(f"  - Phát hiện bất thường (IF_Anomaly = 1)")
                print(f"  - Loại lỗi: {result.get('classifier_label', 'N/A')}")
                print(f"  - Có phải lỗi: {result.get('is_fault', 'N/A')}")
                if result.get("RUL_estimated"):
                    print(f"  - Tuổi thọ còn lại: ~{result.get('RUL_estimated')} chu kỳ sạc")
                    print(f"    → Nên sửa chữa trong khoảng {result.get('RUL_estimated')} chu kỳ tới")
                else:
                    print("  - Không thể dự đoán tuổi thọ (có thể do classifier không xác định được lỗi)")
        else:
            print(f"\n❌ Lỗi: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Không thể kết nối đến API. Đảm bảo FastAPI đang chạy tại http://localhost:8000")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def check_api_available():
    """Kiểm tra API có sẵn không."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def run_all_tests():
    """Chạy tất cả test cases."""
    print("🧪 BẮT ĐẦU TEST CÁC TRƯỜNG HỢP DỰ ĐOÁN")
    print("="*80)
    print("Mục đích: Hiểu cách hệ thống dự đoán lỗi xe điện trong các tình huống khác nhau")
    print("="*80)
    
    # Kiểm tra API có sẵn không
    print("\n🔍 Kiểm tra kết nối API...")
    if not check_api_available():
        print("❌ API không khả dụng!")
        print(f"   Đảm bảo FastAPI đang chạy tại {API_BASE}")
        print("   Chạy: docker compose up -d fastapi-inference")
        sys.exit(1)
    print("✅ API đã sẵn sàng!")
    
    test_cases = [
        TEST_CASE_1_NORMAL,
        TEST_CASE_2_BATTERY_AGING,
        TEST_CASE_3_MOTOR_OVERHEAT,
        TEST_CASE_4_BRAKE_FAILURE,
        TEST_CASE_5_THERMAL_RUNAWAY,
        TEST_CASE_6_SENSOR_DRIFT,
        TEST_CASE_7_NEW_CAR_ANOMALY,
        TEST_CASE_8_OLD_CAR_NORMAL,
        TEST_CASE_9_MISSING_DATA,
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        test_predict(
            payload=test_case["payload"],
            test_name=f"{i}. {test_case['name']}",
            description=test_case["description"],
            expected=test_case.get("expected")
        )
        time.sleep(1)  # Đợi 1 giây giữa các test
    
    print("\n" + "="*80)
    print("✅ HOÀN THÀNH TẤT CẢ TEST CASES")
    print("="*80)
    print("\n💡 Lưu ý:")
    print("  - Kết quả có thể khác một chút tùy vào model đã train")
    print("  - classifier_label có thể là mã số thay vì tên (tùy vào label encoder)")
    print("  - RUL_estimated có thể khác nhau tùy vào dữ liệu training")
    print("  - Một số test case có thể không phát hiện lỗi nếu model chưa được train đầy đủ")
    print("\n📚 Đọc thêm:")
    print("  - docs/HIEU_HE_THONG.md - Hiểu chi tiết cách hệ thống hoạt động")
    print("  - http://localhost:8000/docs - API documentation")
    print("  - http://localhost:5000 - MLflow UI để xem training metrics")

def run_single_test(test_number):
    """Chạy một test case cụ thể."""
    test_cases = [
        TEST_CASE_1_NORMAL,
        TEST_CASE_2_BATTERY_AGING,
        TEST_CASE_3_MOTOR_OVERHEAT,
        TEST_CASE_4_BRAKE_FAILURE,
        TEST_CASE_5_THERMAL_RUNAWAY,
        TEST_CASE_6_SENSOR_DRIFT,
        TEST_CASE_7_NEW_CAR_ANOMALY,
        TEST_CASE_8_OLD_CAR_NORMAL,
        TEST_CASE_9_MISSING_DATA,
    ]
    
    if 1 <= test_number <= len(test_cases):
        test_case = test_cases[test_number - 1]
        test_predict(
            payload=test_case["payload"],
            test_name=test_case["name"],
            description=test_case["description"],
            expected=test_case.get("expected")
        )
    else:
        print(f"❌ Test case {test_number} không tồn tại. Chọn từ 1-{len(test_cases)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Chạy một test case cụ thể: python test_predict_cases.py <số>
        try:
            test_num = int(sys.argv[1])
            if not check_api_available():
                print("❌ API không khả dụng!")
                sys.exit(1)
            run_single_test(test_num)
        except ValueError:
            print("❌ Số test case không hợp lệ. Sử dụng: python test_predict_cases.py <1-9>")
    else:
        # Chạy tất cả test cases
        run_all_tests()


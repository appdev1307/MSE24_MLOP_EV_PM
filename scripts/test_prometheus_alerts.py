#!/usr/bin/env python3
"""
Test script để kiểm tra Prometheus alerts hoạt động.

Usage:
    python scripts/test_prometheus_alerts.py
"""

import requests
import time
import json
from typing import List, Dict, Optional

PROMETHEUS_URL = "http://localhost:9090"


def get_alerts() -> List[Dict]:
    """Lấy danh sách alerts từ Prometheus."""
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/alerts", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("alerts", [])
    except Exception as e:
        print(f"❌ Lỗi khi lấy alerts: {e}")
        return []


def get_active_alerts() -> List[Dict]:
    """Lấy chỉ alerts đang FIRING hoặc PENDING."""
    all_alerts = get_alerts()
    return [
        a for a in all_alerts
        if a.get("state") in ["firing", "pending"]
    ]


def check_target_status(job_name: str = "fastapi-inference") -> Optional[bool]:
    """Kiểm tra target có UP không."""
    try:
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": f'up{{job="{job_name}"}}'},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("data", {}).get("result", [])
        if results:
            value = results[0].get("value", [None, "0"])[1]
            return value == "1"
        return None
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra target: {e}")
        return None


def wait_for_alert(alert_name: str, timeout_sec: int = 60) -> bool:
    """Đợi alert xuất hiện trong timeout giây."""
    start = time.time()
    while time.time() - start < timeout_sec:
        alerts = get_active_alerts()
        for alert in alerts:
            labels = alert.get("labels", {})
            if labels.get("alertname") == alert_name:
                print(f"✅ Alert '{alert_name}' đã xuất hiện!")
                return True
        time.sleep(2)
    print(f"⏱️  Timeout: Alert '{alert_name}' không xuất hiện sau {timeout_sec}s")
    return False


def print_alerts():
    """In danh sách alerts đang active."""
    alerts = get_active_alerts()
    
    if not alerts:
        print("✅ Không có alert nào đang active.")
        return
    
    print(f"\n📊 Tìm thấy {len(alerts)} alert(s) đang active:\n")
    
    for i, alert in enumerate(alerts, 1):
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        state = alert.get("state", "unknown")
        
        print(f"{i}. [{state.upper()}] {labels.get('alertname', 'N/A')}")
        print(f"   Severity: {labels.get('severity', 'N/A')}")
        print(f"   Summary: {annotations.get('summary', 'N/A')}")
        print(f"   Description: {annotations.get('description', 'N/A')}")
        print()


def main():
    print("🔍 Kiểm tra Prometheus Alerts\n")
    print("=" * 60)
    
    # Kiểm tra Prometheus có accessible không
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/status/config", timeout=5)
        resp.raise_for_status()
        print("✅ Prometheus đang chạy\n")
    except Exception as e:
        print(f"❌ Không kết nối được Prometheus tại {PROMETHEUS_URL}")
        print(f"   Lỗi: {e}\n")
        print("💡 Đảm bảo Prometheus đang chạy:")
        print("   docker compose up -d prometheus")
        return
    
    # Kiểm tra target status
    print("📡 Kiểm tra target status:")
    status = check_target_status("fastapi-inference")
    if status is True:
        print("   ✅ fastapi-inference: UP\n")
    elif status is False:
        print("   ❌ fastapi-inference: DOWN\n")
    else:
        print("   ⚠️  fastapi-inference: Không xác định được\n")
    
    # In alerts
    print_alerts()
    
    print("=" * 60)
    print("\n💡 Để test alert:")
    print("   1. Dừng FastAPI: docker compose stop fastapi-inference")
    print("   2. Chờ 30-40 giây")
    print("   3. Chạy lại script này: python scripts/test_prometheus_alerts.py")
    print("   4. Bật lại: docker compose start fastapi-inference")


if __name__ == "__main__":
    main()

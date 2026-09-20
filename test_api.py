#!/usr/bin/env python3
"""
Traffic AI Engine - API Test Suite
Validates all core backend endpoints, authentication, and responses.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
TOKEN = None
PASS_COUNT = 0
FAIL_COUNT = 0

def log(msg):
    """Print timestamped message safely with ASCII fallback"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def record_pass(endpoint_desc):
    global PASS_COUNT
    PASS_COUNT += 1
    log(f"  [PASS] {endpoint_desc}")

def record_fail(endpoint_desc, err=""):
    global FAIL_COUNT
    FAIL_COUNT += 1
    log(f"  [FAIL] {endpoint_desc} -> {err}")

def test_auth():
    """Test authentication endpoints"""
    global TOKEN
    log("=== TESTING AUTHENTICATION ===")
    
    # 1. Login with demo superadmin
    payload = {"officer_id": "superadmin", "password": "admin123"}
    try:
        res = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            TOKEN = data.get("access_token")
            user_info = data.get("user", {})
            record_pass(f"POST /auth/login - Logged in as {user_info.get('officer_id')} ({user_info.get('role', {}).get('name')})")
        else:
            record_fail("POST /auth/login", f"Status {res.status_code}: {res.text}")
            return False
    except Exception as e:
        record_fail("POST /auth/login", str(e))
        return False

    # 2. Get current user profile
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        res = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=5)
        if res.status_code == 200:
            user = res.json()
            record_pass(f"GET /auth/me - Current officer: {user.get('officer_id')} - Name: {user.get('name')}")
        else:
            record_fail("GET /auth/me", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /auth/me", str(e))

    return True

def test_cameras():
    """Test camera endpoints"""
    log("=== TESTING CAMERAS ===")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        res = requests.get(f"{BASE_URL}/cameras/", headers=headers, timeout=5)
        if res.status_code == 200:
            cams = res.json()
            record_pass(f"GET /cameras/ - Retrieved {len(cams)} cameras")
            if cams:
                first = cams[0]
                log(f"         Sample Camera: {first.get('camera_id')} ({first.get('name')}) - Status: {first.get('status')}")
        else:
            record_fail("GET /cameras/", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /cameras/", str(e))

    # Test camera snapshot endpoint
    try:
        res = requests.get(f"{BASE_URL}/cameras/CAM01/snapshot", timeout=5)
        if res.status_code == 200 and res.headers.get("content-type", "").startswith("image/"):
            record_pass(f"GET /cameras/CAM01/snapshot - Returned JPEG image ({len(res.content)} bytes)")
        else:
            record_fail("GET /cameras/CAM01/snapshot", f"Status {res.status_code}")
    except Exception as e:
        record_fail("GET /cameras/CAM01/snapshot", str(e))

def test_detection():
    """Test detection and plate endpoints"""
    log("=== TESTING DETECTIONS ===")
    headers = {"Authorization": f"Bearer {TOKEN}"}

    # 1. Detections list
    try:
        res = requests.get(f"{BASE_URL}/detection/detections?limit=10", headers=headers, timeout=5)
        if res.status_code == 200:
            detections = res.json()
            record_pass(f"GET /detection/detections - Retrieved {len(detections)} detections")
        else:
            record_fail("GET /detection/detections", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /detection/detections", str(e))

    # 2. Confidence stats
    try:
        res = requests.get(f"{BASE_URL}/detection/confidence-stats", headers=headers, timeout=5)
        if res.status_code == 200:
            stats = res.json()
            record_pass(f"GET /detection/confidence-stats - Avg confidence: {stats.get('average_confidence', 0):.2f}")
        else:
            record_fail("GET /detection/confidence-stats", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /detection/confidence-stats", str(e))

    # 3. Detections with camera (for FindVehicle UI)
    try:
        res = requests.get(f"{BASE_URL}/detections/with-camera", headers=headers, timeout=5)
        if res.status_code == 200:
            with_cam = res.json()
            record_pass(f"GET /detections/with-camera - Retrieved {len(with_cam)} enriched detections")
        else:
            record_fail("GET /detections/with-camera", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /detections/with-camera", str(e))

def test_search():
    """Test vehicle search endpoints"""
    log("=== TESTING SEARCH ===")
    headers = {"Authorization": f"Bearer {TOKEN}"}

    try:
        res = requests.get(f"{BASE_URL}/search/vehicles?limit=10", headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", []) if isinstance(data, dict) else data
            record_pass(f"GET /search/vehicles - Search returned {len(results)} results")
        else:
            record_fail("GET /search/vehicles", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /search/vehicles", str(e))

    try:
        res = requests.get(f"{BASE_URL}/blacklist", headers=headers, timeout=10)
        if res.status_code == 200:
            flagged = res.json()
            count = len(flagged) if isinstance(flagged, list) else len(flagged.get("blacklist", []))
            record_pass(f"GET /blacklist - Retrieved {count} flagged/blacklist records")
        else:
            record_fail("GET /blacklist", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /blacklist", str(e))

def test_trajectories():
    """Test vehicle trajectory reconstruction endpoints"""
    log("=== TESTING TRAJECTORIES ===")
    headers = {"Authorization": f"Bearer {TOKEN}"}

    try:
        res = requests.get(f"{BASE_URL}/trajectories/journeys?limit=10", headers=headers, timeout=5)
        if res.status_code == 200:
            journeys = res.json()
            count = len(journeys) if isinstance(journeys, list) else len(journeys.get("journeys", []))
            record_pass(f"GET /trajectories/journeys - Retrieved {count} journeys")
        else:
            record_fail("GET /trajectories/journeys", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /trajectories/journeys", str(e))

    try:
        res = requests.get(f"{BASE_URL}/trajectories/map-data", headers=headers, timeout=5)
        if res.status_code == 200:
            record_pass("GET /trajectories/map-data - Spatial map data retrieved")
        else:
            record_fail("GET /trajectories/map-data", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /trajectories/map-data", str(e))

def test_alerts():
    """Test alert management endpoints"""
    log("=== TESTING ALERTS ===")
    headers = {"Authorization": f"Bearer {TOKEN}"}

    try:
        res = requests.get(f"{BASE_URL}/alerts/?limit=10", headers=headers, timeout=5)
        if res.status_code == 200:
            alerts = res.json()
            record_pass(f"GET /alerts/ - Retrieved {len(alerts)} alerts")
        else:
            record_fail("GET /alerts/", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /alerts/", str(e))

def test_analytics():
    """Test analytics & dashboard endpoints"""
    log("=== TESTING ANALYTICS ===")
    headers = {"Authorization": f"Bearer {TOKEN}"}

    try:
        res = requests.get(f"{BASE_URL}/analytics/dashboard", headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            record_pass(f"GET /analytics/dashboard - Total Detections: {data.get('total_detections', 0)}, Active Cameras: {data.get('active_cameras', 0)}")
        else:
            record_fail("GET /analytics/dashboard", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /analytics/dashboard", str(e))

def test_admin():
    """Test administrative endpoints"""
    log("=== TESTING ADMIN ===")
    headers = {"Authorization": f"Bearer {TOKEN}"}

    try:
        res = requests.get(f"{BASE_URL}/admin/users", headers=headers, timeout=10)
        if res.status_code == 200:
            users = res.json()
            record_pass(f"GET /admin/users - Retrieved {len(users)} users")
        else:
            record_fail("GET /admin/users", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /admin/users", str(e))

    try:
        res = requests.get(f"{BASE_URL}/admin/audit-logs?limit=5", headers=headers, timeout=10)
        if res.status_code == 200:
            logs = res.json()
            count = len(logs) if isinstance(logs, list) else len(logs.get("audit_logs", []))
            record_pass(f"GET /admin/audit-logs - Retrieved {count} audit logs")
        else:
            record_fail("GET /admin/audit-logs", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /admin/audit-logs", str(e))

    try:
        res = requests.get(f"{BASE_URL}/admin/blacklist", headers=headers, timeout=5)
        if res.status_code == 200:
            bl = res.json()
            count = len(bl) if isinstance(bl, list) else len(bl.get("blacklist", []))
            record_pass(f"GET /admin/blacklist - Blacklist has {count} entries")
        else:
            record_fail("GET /admin/blacklist", f"Status {res.status_code}: {res.text}")
    except Exception as e:
        record_fail("GET /admin/blacklist", str(e))

def main():
    log("Traffic AI Engine - Comprehensive API Test Suite")
    log("Connecting to backend at http://localhost:8000...")
    print()

    if not test_auth():
        log("Authentication failed. Stopping remaining tests.")
        sys.exit(1)

    print()
    test_cameras()
    print()
    test_detection()
    print()
    test_search()
    print()
    test_trajectories()
    print()
    test_alerts()
    print()
    test_analytics()
    print()
    test_admin()
    print()

    log("=" * 50)
    log(f"TEST SUMMARY: {PASS_COUNT} PASSED, {FAIL_COUNT} FAILED")
    log("=" * 50)

    if FAIL_COUNT > 0:
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        log("Cannot connect to backend at http://localhost:8000. Ensure it is running.")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}")
        sys.exit(1)

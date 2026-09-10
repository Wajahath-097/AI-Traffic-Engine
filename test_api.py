#!/usr/bin/env python3
"""
Traffic AI Engine - API Test Suite
Run this after starting the backend to validate all endpoints.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
TOKEN = None

def log(msg):
    """Print timestamped message"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_auth():
    """Test authentication endpoints"""
    global TOKEN
    log("=== TESTING AUTHENTICATION ===")
    
    # Test login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    log(f"POST /auth/login: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        TOKEN = data.get("data", {}).get("access_token")
        log(f"✓ Token received: {TOKEN[:20]}...")
    else:
        log(f"✗ Login failed: {response.text}")
        return False
    
    # Test me endpoint
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    log(f"GET /auth/me: {response.status_code}")
    if response.status_code == 200:
        log(f"✓ Current user: {response.json().get('data', {}).get('username')}")
    else:
        log(f"✗ Failed: {response.text}")
    
    print()
    return True

def test_cameras():
    """Test camera endpoints"""
    log("=== TESTING CAMERAS ===")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Get cameras
    response = requests.get(f"{BASE_URL}/cameras/", headers=headers)
    log(f"GET /cameras/: {response.status_code}")
    if response.status_code == 200:
        cameras = response.json().get("data", {}).get("cameras", [])
        log(f"✓ Found {len(cameras)} cameras")
        if cameras:
            log(f"  First camera: {cameras[0].get('name')} ({cameras[0].get('location')})")
    else:
        log(f"✗ Failed: {response.text}")
    
    print()

def test_detection():
    """Test detection endpoints"""
    log("=== TESTING DETECTIONS ===")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Get detections
    response = requests.get(
        f"{BASE_URL}/detection/?limit=10",
        headers=headers
    )
    log(f"GET /detection/: {response.status_code}")
    if response.status_code == 200:
        detections = response.json().get("data", {}).get("detections", [])
        log(f"✓ Found {len(detections)} recent detections")
        if detections:
            det = detections[0]
            log(f"  Latest: {det.get('plate_number')} at {det.get('timestamp')}")
    else:
        log(f"✗ Failed: {response.text}")
    
    # Get confidence stats
    response = requests.get(
        f"{BASE_URL}/detection/stats/confidence",
        headers=headers
    )
    log(f"GET /detection/stats/confidence: {response.status_code}")
    if response.status_code == 200:
        stats = response.json().get("data", {})
        log(f"✓ Avg confidence: {stats.get('avg_confidence', 0):.2f}")
    
    print()

def test_search():
    """Test search endpoints"""
    log("=== TESTING SEARCH ===")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Search for vehicles
    response = requests.get(
        f"{BASE_URL}/search/vehicles?plate=ABC123",
        headers=headers
    )
    log(f"GET /search/vehicles: {response.status_code}")
    if response.status_code == 200:
        results = response.json().get("data", {}).get("results", [])
        log(f"✓ Search returned {len(results)} results")
    
    # Get flagged vehicles
    response = requests.get(
        f"{BASE_URL}/search/flagged",
        headers=headers
    )
    log(f"GET /search/flagged: {response.status_code}")
    if response.status_code == 200:
        flagged = response.json().get("data", {}).get("flagged_vehicles", [])
        log(f"✓ Found {len(flagged)} flagged vehicles")
    
    print()

def test_trajectories():
    """Test trajectory endpoints"""
    log("=== TESTING TRAJECTORIES ===")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Get journeys
    response = requests.get(
        f"{BASE_URL}/trajectories/journeys?limit=10",
        headers=headers
    )
    log(f"GET /trajectories/journeys: {response.status_code}")
    if response.status_code == 200:
        journeys = response.json().get("data", {}).get("journeys", [])
        log(f"✓ Found {len(journeys)} journeys")
    
    # Get map data
    response = requests.get(
        f"{BASE_URL}/trajectories/map-data",
        headers=headers
    )
    log(f"GET /trajectories/map-data: {response.status_code}")
    if response.status_code == 200:
        map_data = response.json().get("data", {})
        log(f"✓ Map data retrieved")
    
    print()

def test_alerts():
    """Test alert endpoints"""
    log("=== TESTING ALERTS ===")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Get alerts
    response = requests.get(
        f"{BASE_URL}/alerts/?limit=10",
        headers=headers
    )
    log(f"GET /alerts/: {response.status_code}")
    if response.status_code == 200:
        alerts = response.json().get("data", {}).get("alerts", [])
        log(f"✓ Found {len(alerts)} alerts")
    
    print()

def test_analytics():
    """Test analytics endpoints"""
    log("=== TESTING ANALYTICS ===")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Get dashboard stats
    response = requests.get(
        f"{BASE_URL}/analytics/dashboard",
        headers=headers
    )
    log(f"GET /analytics/dashboard: {response.status_code}")
    if response.status_code == 200:
        dashboard = response.json().get("data", {})
        log(f"✓ Total detections: {dashboard.get('total_detections')}")
        log(f"✓ Active cameras: {dashboard.get('active_cameras')}")
        log(f"✓ Open alerts: {dashboard.get('open_alerts')}")
    
    # Get detections by camera
    response = requests.get(
        f"{BASE_URL}/analytics/detections/by-camera",
        headers=headers
    )
    log(f"GET /analytics/detections/by-camera: {response.status_code}")
    if response.status_code == 200:
        by_camera = response.json().get("data", {}).get("by_camera", [])
        log(f"✓ Got stats for {len(by_camera)} cameras")
    
    # Get patterns
    response = requests.get(
        f"{BASE_URL}/analytics/patterns",
        headers=headers
    )
    log(f"GET /analytics/patterns: {response.status_code}")
    if response.status_code == 200:
        patterns = response.json().get("data", {})
        log(f"✓ Traffic patterns retrieved")
    
    print()

def test_admin():
    """Test admin endpoints"""
    log("=== TESTING ADMIN ===")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Get users
    response = requests.get(
        f"{BASE_URL}/admin/users",
        headers=headers
    )
    log(f"GET /admin/users: {response.status_code}")
    if response.status_code == 200:
        users = response.json().get("data", {}).get("users", [])
        log(f"✓ Found {len(users)} users")
        for user in users:
            log(f"  - {user.get('username')} ({user.get('role')})")
    
    # Get audit log
    response = requests.get(
        f"{BASE_URL}/admin/audit-log?limit=5",
        headers=headers
    )
    log(f"GET /admin/audit-log: {response.status_code}")
    if response.status_code == 200:
        logs = response.json().get("data", {}).get("audit_logs", [])
        log(f"✓ Found {len(logs)} audit log entries")
    
    # Get blacklist
    response = requests.get(
        f"{BASE_URL}/admin/blacklist",
        headers=headers
    )
    log(f"GET /admin/blacklist: {response.status_code}")
    if response.status_code == 200:
        blacklist = response.json().get("data", {}).get("blacklist", [])
        log(f"✓ Blacklist has {len(blacklist)} entries")
    
    print()

def main():
    """Run all tests"""
    log("Traffic AI Engine - API Test Suite")
    log("Starting tests...")
    print()
    
    # Test authentication first
    if not test_auth():
        log("✗ Authentication failed. Stopping tests.")
        return
    
    # Run all endpoint tests
    test_cameras()
    test_detection()
    test_search()
    test_trajectories()
    test_alerts()
    test_analytics()
    test_admin()
    
    log("=== TEST COMPLETE ===")
    log("All endpoints validated successfully!")
    log("\nNext steps:")
    log("1. Start the frontend: npm run dev (in frontend/ folder)")
    log("2. Open http://localhost:5173 in your browser")
    log("3. Login with admin/admin123")
    log("4. Explore the Dashboard, Cameras, and Search pages")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        log("✗ Cannot connect to backend at http://localhost:8000")
        log("  Make sure the backend is running:")
        log("  docker-compose up -d  (or)")
        log("  uvicorn app.main:app --reload")
    except Exception as e:
        log(f"✗ Error: {e}")

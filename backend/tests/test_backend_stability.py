"""
Backend Stability Test Script for TASK 1
Tests all audio API endpoints and verifies backend stability.

Usage:
    1. Start backend: uvicorn api.main:app --reload
    2. Run tests: python test_backend_stability.py
"""

import requests
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
AUDIO_BASE = f"{BASE_URL}/audio"

# Test results tracking
tests_passed = 0
tests_failed = 0


def log(message: str, level: str = "INFO"):
    """Log test messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def test_result(test_name: str, passed: bool, details: str = ""):
    """Record and display test result"""
    global tests_passed, tests_failed
    
    if passed:
        tests_passed += 1
        log(f"✅ PASS: {test_name}", "PASS")
        if details:
            log(f"   {details}", "INFO")
    else:
        tests_failed += 1
        log(f"❌ FAIL: {test_name}", "FAIL")
        if details:
            log(f"   {details}", "ERROR")


def test_1_start_recording_success():
    """Test: Start recording with valid session_id"""
    log("Running Test 1: Start recording success")
    
    try:
        response = requests.post(f"{AUDIO_BASE}/start-record", params={"session_id": "test_001"})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "recording_started" and data.get("session_id") == "test_001":
                test_result("Start recording success", True, f"Response: {data}")
                return True
            else:
                test_result("Start recording success", False, f"Invalid response: {data}")
                return False
        else:
            test_result("Start recording success", False, f"Status code: {response.status_code}, Body: {response.text}")
            return False
    except Exception as e:
        test_result("Start recording success", False, f"Exception: {e}")
        return False


def test_2_start_recording_duplicate():
    """Test: Starting recording twice should fail"""
    log("Running Test 2: Duplicate recording prevention")
    
    try:
        response = requests.post(f"{AUDIO_BASE}/start-record", params={"session_id": "test_002"})
        
        if response.status_code == 400:
            test_result("Duplicate recording prevention", True, f"Correctly rejected: {response.json()}")
            return True
        else:
            test_result("Duplicate recording prevention", False, f"Should return 400, got {response.status_code}")
            return False
    except Exception as e:
        test_result("Duplicate recording prevention", False, f"Exception: {e}")
        return False


def test_3_live_metrics_during_recording():
    """Test: Live metrics endpoint during recording"""
    log("Running Test 3: Live metrics during recording")
    
    errors = []
    try:
        for i in range(10):
            response = requests.get(f"{AUDIO_BASE}/live-metrics", params={"session_id": "test_001"})
            
            if response.status_code != 200:
                errors.append(f"Iteration {i}: Status {response.status_code}")
                continue
            
            data = response.json()
            required_fields = ["amplitude", "is_speech", "duration"]
            for field in required_fields:
                if field not in data:
                    errors.append(f"Iteration {i}: Missing field '{field}'")
            
            time.sleep(0.1)  # 100ms between calls
        
        if not errors:
            test_result("Live metrics during recording", True, "10 calls successful, no errors")
            return True
        else:
            test_result("Live metrics during recording", False, f"Errors: {errors[:3]}")  # Show first 3 errors
            return False
    except Exception as e:
        test_result("Live metrics during recording", False, f"Exception: {e}")
        return False


def test_4_stop_recording_success():
    """Test: Stop recording successfully"""
    log("Running Test 4: Stop recording")
    
    try:
        response = requests.post(f"{AUDIO_BASE}/stop-record", params={"session_id": "test_001"})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "recording_stopped" and "file" in data:
                test_result("Stop recording", True, f"File: {data.get('file')}")
                return True
            else:
                test_result("Stop recording", False, f"Invalid response: {data}")
                return False
        else:
            test_result("Stop recording", False, f"Status code: {response.status_code}, Body: {response.text}")
            return False
    except Exception as e:
        test_result("Stop recording", False, f"Exception: {e}")
        return False


def test_5_status_transitions():
    """Test: Status transitions from processing to done"""
    log("Running Test 5: Status transitions")
    
    try:
        max_wait = 10  # Maximum 10 seconds
        start_time = time.time()
        
        statuses_seen = []
        
        while time.time() - start_time < max_wait:
            response = requests.get(f"{AUDIO_BASE}/status", params={"session_id": "test_001"})
            
            if response.status_code == 200:
                status = response.json().get("status")
                if status not in statuses_seen:
                    statuses_seen.append(status)
                    log(f"Status: {status}")
                
                if status == "done":
                    test_result("Status transitions", True, f"Transitions: {' → '.join(statuses_seen)}")
                    return True
                elif status == "error":
                    test_result("Status transitions", False, f"Processing failed, transitions: {statuses_seen}")
                    return False
            
            time.sleep(0.5)
        
        test_result("Status transitions", False, f"Timeout after {max_wait}s, statuses: {statuses_seen}")
        return False
    except Exception as e:
        test_result("Status transitions", False, f"Exception: {e}")
        return False


def test_6_result_retrieval():
    """Test: Retrieve processing result"""
    log("Running Test 6: Result retrieval")
    
    try:
        response = requests.get(f"{AUDIO_BASE}/latest-result", params={"session_id": "test_001"})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "done" and data.get("result") is not None:
                result = data.get("result")
                required_fields = ["satisfied", "dissatisfied", "confidence"]
                missing = [f for f in required_fields if f not in result]
                
                if not missing:
                    test_result("Result retrieval", True, f"Result: {result}")
                    return True
                else:
                    test_result("Result retrieval", False, f"Missing fields: {missing}")
                    return False
            else:
                test_result("Result retrieval", False, f"Invalid response: {data}")
                return False
        else:
            test_result("Result retrieval", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        test_result("Result retrieval", False, f"Exception: {e}")
        return False


def test_7_invalid_session_id():
    """Test: Error handling for invalid session_id"""
    log("Running Test 7: Invalid session_id handling")
    
    try:
        response = requests.get(f"{AUDIO_BASE}/latest-result", params={"session_id": "nonexistent_session"})
        
        if response.status_code == 404:
            test_result("Invalid session_id handling", True, "Correctly returned 404")
            return True
        else:
            test_result("Invalid session_id handling", False, f"Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        test_result("Invalid session_id handling", False, f"Exception: {e}")
        return False


def test_8_live_metrics_after_stop():
    """Test: Live metrics should return zeros after stop"""
    log("Running Test 8: Live metrics after stop")
    
    try:
        response = requests.get(f"{AUDIO_BASE}/live-metrics", params={"session_id": "test_001"})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("amplitude") == 0.0 and data.get("is_speech") == False and data.get("duration") == 0.0:
                test_result("Live metrics after stop", True, "Returns zeros as expected")
                return True
            else:
                test_result("Live metrics after stop", False, f"Expected zeros, got: {data}")
                return False
        else:
            test_result("Live metrics after stop", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        test_result("Live metrics after stop", False, f"Exception: {e}")
        return False


def run_all_tests():
    """Run all tests in sequence"""
    log("=" * 60)
    log("BACKEND STABILITY TEST SUITE - TASK 1")
    log("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/")
        log(f"Backend is running: {response.json()}")
    except Exception as e:
        log(f"❌ Backend is not running! Start it with: uvicorn api.main:app --reload", "ERROR")
        log(f"Error: {e}", "ERROR")
        return
    
    log("")
    
    # Run tests
    test_1_start_recording_success()
    time.sleep(0.5)
    
    test_2_start_recording_duplicate()
    time.sleep(0.5)
    
    test_3_live_metrics_during_recording()
    time.sleep(0.5)
    
    test_4_stop_recording_success()
    time.sleep(1)
    
    test_5_status_transitions()
    time.sleep(0.5)
    
    test_6_result_retrieval()
    time.sleep(0.5)
    
    test_7_invalid_session_id()
    time.sleep(0.5)
    
    test_8_live_metrics_after_stop()
    
    # Summary
    log("")
    log("=" * 60)
    log("TEST SUMMARY")
    log("=" * 60)
    log(f"✅ Passed: {tests_passed}")
    log(f"❌ Failed: {tests_failed}")
    log(f"Total: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        log("")
        log("🎉 ALL TESTS PASSED! Backend is stable.", "SUCCESS")
        return 0
    else:
        log("")
        log(f"⚠️  {tests_failed} test(s) failed. Please review.", "WARNING")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

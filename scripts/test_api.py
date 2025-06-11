#!/usr/bin/env python3

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/healthz")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_chat():
    """Test chat endpoint"""
    try:
        payload = {
            "message": "I want to enroll in your membership program",
            "session_id": f"test_session_{int(time.time())}"
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        print(f"Chat test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data.get('message', '')[:100]}...")
            return True
        else:
            print(f"Chat error: {response.text}")
            return False
    except Exception as e:
        print(f"Chat test failed: {e}")
        return False

def test_zendesk_upload():
    """Test Zendesk datadump upload"""
    try:
        test_data = [
            {
                "id": "test_123",
                "subject": "Test Membership Question",
                "description": "This is a test ticket",
                "status": "open",
                "priority": "normal",
                "requester_email": "test@example.com",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "tags": ["test", "membership"]
            }
        ]
        
        with open("/tmp/test_zendesk.json", "w") as f:
            json.dump(test_data, f)
        
        with open("/tmp/test_zendesk.json", "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/api/zendesk/datadump", files=files)
        
        print(f"Zendesk upload test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Upload result: {data}")
            return True
        else:
            print(f"Upload error: {response.text}")
            return False
    except Exception as e:
        print(f"Zendesk upload test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing AI Membership Enrollment API...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Chat Endpoint", test_chat),
        ("Zendesk Upload", test_zendesk_upload)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✓ PASS' if result else '✗ FAIL'}")
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

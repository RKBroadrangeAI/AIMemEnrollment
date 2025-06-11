#!/usr/bin/env python3
"""
Comprehensive verification script to test vector dimension fix
"""
import requests
import json
import sys
from qdrant_client import QdrantClient
import os

def test_qdrant_collection():
    """Test Qdrant collection configuration"""
    print("=== Testing Qdrant Collection ===")
    try:
        client = QdrantClient(host='localhost', port=6333)
        collections = client.get_collections()
        
        enrollment_collection = None
        for col in collections.collections:
            if col.name == 'enrollment_data':
                enrollment_collection = col
                break
        
        if not enrollment_collection:
            print("❌ ERROR: enrollment_data collection not found")
            return False
            
        collection_info = client.get_collection('enrollment_data')
        vector_size = collection_info.config.params.vectors.size
        distance = collection_info.config.params.vectors.distance
        
        print(f"✅ Collection exists: enrollment_data")
        print(f"✅ Vector size: {vector_size}")
        print(f"✅ Distance metric: {distance}")
        
        if vector_size != 1536:
            print(f"❌ ERROR: Expected 1536 dimensions, got {vector_size}")
            return False
        
        print("✅ Collection configuration is correct")
        return True
        
    except Exception as e:
        print(f"❌ ERROR testing Qdrant: {e}")
        return False

def test_backend_api():
    """Test backend API endpoints"""
    print("\n=== Testing Backend API ===")
    base_url = "http://localhost:8001"
    
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ Backend server is running")
        else:
            print(f"❌ Backend server not responding: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR connecting to backend: {e}")
        return False
    
    test_session = "verify-vector-fix-test"
    test_messages = [
        "Hello, I want to test the vector dimensions",
        "John Doe",
        "john.doe@test.com",
        "Premium membership"
    ]
    
    for i, message in enumerate(test_messages):
        try:
            print(f"Testing message {i+1}: '{message[:30]}...'")
            response = requests.post(
                f"{base_url}/api/chat",
                headers={"Content-Type": "application/json"},
                json={"message": message, "session_id": test_session}
            )
            
            if response.status_code != 200:
                print(f"❌ ERROR: API returned {response.status_code}")
                print(f"Response: {response.text}")
                
                if "Vector dimension error" in response.text:
                    print("❌ FOUND VECTOR DIMENSION ERROR!")
                    return False
                return False
            
            response_data = response.json()
            print(f"✅ Message {i+1} processed successfully")
            print(f"   Response: {response_data.get('message', '')[:50]}...")
            
        except Exception as e:
            print(f"❌ ERROR testing message {i+1}: {e}")
            return False
    
    try:
        response = requests.get(f"{base_url}/api/session/{test_session}")
        if response.status_code == 200:
            print("✅ Session retrieval successful")
        else:
            print(f"❌ Session retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR testing session retrieval: {e}")
        return False
    
    print("✅ All API tests passed")
    return True

def main():
    print("Vector Dimension Fix Verification Script")
    print("=" * 50)
    
    qdrant_ok = test_qdrant_collection()
    
    api_ok = test_backend_api()
    
    print("\n=== FINAL RESULTS ===")
    if qdrant_ok and api_ok:
        print("✅ ALL TESTS PASSED - Vector dimension error is FIXED")
        print("✅ Qdrant collection has correct 1536 dimensions")
        print("✅ Backend API processes messages without vector errors")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Vector dimension error still exists")
        if not qdrant_ok:
            print("❌ Qdrant collection configuration issue")
        if not api_ok:
            print("❌ Backend API vector processing issue")
        sys.exit(1)

if __name__ == "__main__":
    main()

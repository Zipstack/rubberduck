#!/usr/bin/env python3
"""Test AWS Bedrock proxy error scenarios."""

import json
import requests
import os

def test_no_credentials():
    """Test request without AWS credentials."""
    print("=== Testing: No AWS Credentials ===")
    
    headers = {
        "Content-Type": "application/json"
        # No AWS credentials provided
    }
    
    payload = {
        "prompt": "Hello, how are you?",
        "max_gen_len": 100,
        "temperature": 0
    }
    
    try:
        response = requests.post(
            "http://localhost:8009/model/meta.llama3-2-1b-instruct-v1:0/invoke",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
    
    print()

def test_invalid_credentials():
    """Test request with invalid AWS credentials."""
    print("=== Testing: Invalid AWS Credentials ===")
    
    headers = {
        "Content-Type": "application/json",
        "X-AWS-Access-Key": "AKIAINVALIDKEY123",
        "X-AWS-Secret-Key": "invalid-secret-key-123456789"
    }
    
    payload = {
        "prompt": "Hello, how are you?",
        "max_gen_len": 100,
        "temperature": 0
    }
    
    try:
        response = requests.post(
            "http://localhost:8009/model/meta.llama3-2-1b-instruct-v1:0/invoke",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
    
    print()

def test_invalid_model():
    """Test request with invalid model ID."""
    print("=== Testing: Invalid Model ID ===")
    
    # Get AWS credentials from environment
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("Skipping: AWS credentials not available")
        return
    
    headers = {
        "Content-Type": "application/json",
        "X-AWS-Access-Key": access_key,
        "X-AWS-Secret-Key": secret_key
    }
    
    payload = {
        "prompt": "Hello, how are you?",
        "max_gen_len": 100,
        "temperature": 0
    }
    
    try:
        response = requests.post(
            "http://localhost:8009/model/invalid-model-id/invoke",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
    
    print()

def test_malformed_request():
    """Test request with malformed JSON."""
    print("=== Testing: Malformed Request ===")
    
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("Skipping: AWS credentials not available")
        return
    
    headers = {
        "Content-Type": "application/json",
        "X-AWS-Access-Key": access_key,
        "X-AWS-Secret-Key": secret_key
    }
    
    # Invalid JSON payload
    malformed_json = '{"prompt": "Hello", "invalid": }'
    
    try:
        response = requests.post(
            "http://localhost:8009/model/meta.llama3-2-1b-instruct-v1:0/invoke",
            data=malformed_json,  # Use data instead of json to send malformed JSON
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
    
    print()

if __name__ == "__main__":
    print("Testing AWS Bedrock Proxy Error Scenarios")
    print("=" * 50)
    
    test_no_credentials()
    test_invalid_credentials()
    test_invalid_model()
    test_malformed_request()
    
    print("All error scenario tests completed.")
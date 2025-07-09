#!/usr/bin/env python3
"""Test AWS Bedrock proxy with unsigned request and custom headers."""

import json
import requests
import os

def test_bedrock_unsigned():
    """Test Bedrock proxy with unsigned request."""
    
    # Get AWS credentials from environment
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set")
        return
    
    # Proxy URL
    proxy_url = "http://localhost:8009"
    model_id = "meta.llama3-2-1b-instruct-v1:0"
    endpoint = f"/model/{model_id}/invoke"
    
    # Request payload
    payload = {
        "prompt": "Hello, how are you?",
        "max_gen_len": 100,
        "temperature": 0
    }
    
    # Headers with AWS credentials
    headers = {
        "Content-Type": "application/json",
        "X-AWS-Access-Key": access_key,
        "X-AWS-Secret-Key": secret_key
    }
    
    print(f"Testing unsigned request to: {proxy_url}{endpoint}")
    print(f"Using access key: {access_key[:5]}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{proxy_url}{endpoint}",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response text: {response.text}")
            
        if response.status_code == 200:
            print("\nSuccess!")
        else:
            print(f"\nError: {response.status_code}")
            
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    test_bedrock_unsigned()
#!/usr/bin/env python3
"""Test AWS Bedrock proxy caching functionality."""

import json
import requests
import os
import time

def test_cache_behavior():
    """Test that identical requests are cached."""
    print("=== Testing: Cache Behavior ===")
    
    # Get AWS credentials from environment
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set")
        return
    
    headers = {
        "Content-Type": "application/json",
        "X-AWS-Access-Key": access_key,
        "X-AWS-Secret-Key": secret_key
    }
    
    # Use a simple, deterministic payload for caching test
    payload = {
        "prompt": "What is 2+2?",
        "max_gen_len": 50,
        "temperature": 0  # Deterministic response
    }
    
    endpoint = "http://localhost:8009/model/meta.llama3-2-1b-instruct-v1:0/invoke"
    
    print(f"Making first request (should be cache MISS)...")
    start_time = time.time()
    
    try:
        response1 = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        first_duration = time.time() - start_time
        print(f"First request - Status: {response1.status_code}")
        print(f"First request - Duration: {first_duration:.2f}s")
        
        cache_status = response1.headers.get('X-Cache', 'Unknown')
        print(f"First request - Cache Status: {cache_status}")
        
        if response1.status_code == 200:
            try:
                response1_data = response1.json()
                print(f"First request - Success: Got response")
            except:
                print(f"First request - Response: {response1.text[:200]}...")
        else:
            print(f"First request - Error response: {response1.text[:200]}...")
        
        print("\nWaiting 1 second before second request...")
        time.sleep(1)
        
        print(f"Making second identical request (should be cache HIT)...")
        start_time = time.time()
        
        response2 = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        second_duration = time.time() - start_time
        print(f"Second request - Status: {response2.status_code}")
        print(f"Second request - Duration: {second_duration:.2f}s")
        
        cache_status2 = response2.headers.get('X-Cache', 'Unknown')
        print(f"Second request - Cache Status: {cache_status2}")
        
        # Compare responses
        if response1.status_code == response2.status_code:
            print(f"\n✅ Status codes match: {response1.status_code}")
        else:
            print(f"\n❌ Status codes differ: {response1.status_code} vs {response2.status_code}")
        
        # Check if second request was faster (indicating cache hit)
        if second_duration < first_duration:
            print(f"✅ Second request faster ({second_duration:.2f}s vs {first_duration:.2f}s)")
        else:
            print(f"⚠️ Second request not faster ({second_duration:.2f}s vs {first_duration:.2f}s)")
        
        # Check cache headers
        if cache_status2 == 'HIT':
            print(f"✅ Cache header indicates HIT")
        elif cache_status == 'MISS' and cache_status2 == 'MISS':
            print(f"ℹ️ Both requests show MISS (may be due to error responses)")
        else:
            print(f"⚠️ Unexpected cache status: {cache_status} -> {cache_status2}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")

def test_different_requests_no_cache():
    """Test that different requests are not cached together."""
    print("\n=== Testing: Different Requests (No Cache Sharing) ===")
    
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        print("Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set")
        return
    
    headers = {
        "Content-Type": "application/json",
        "X-AWS-Access-Key": access_key,
        "X-AWS-Secret-Key": secret_key
    }
    
    # Two different payloads
    payload1 = {
        "prompt": "What is 2+2?",
        "max_gen_len": 50,
        "temperature": 0
    }
    
    payload2 = {
        "prompt": "What is 3+3?",
        "max_gen_len": 50,
        "temperature": 0
    }
    
    endpoint = "http://localhost:8009/model/meta.llama3-2-1b-instruct-v1:0/invoke"
    
    try:
        print("Making request with first payload...")
        response1 = requests.post(endpoint, json=payload1, headers=headers, timeout=30)
        cache_status1 = response1.headers.get('X-Cache', 'Unknown')
        print(f"Request 1 - Status: {response1.status_code}, Cache: {cache_status1}")
        
        print("Making request with second payload...")
        response2 = requests.post(endpoint, json=payload2, headers=headers, timeout=30)
        cache_status2 = response2.headers.get('X-Cache', 'Unknown')
        print(f"Request 2 - Status: {response2.status_code}, Cache: {cache_status2}")
        
        if cache_status1 == 'MISS' and cache_status2 == 'MISS':
            print("✅ Different requests correctly show cache MISS")
        else:
            print(f"ℹ️ Cache status: {cache_status1}, {cache_status2}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    print("Testing AWS Bedrock Proxy Caching")
    print("=" * 40)
    
    test_cache_behavior()
    test_different_requests_no_cache()
    
    print("\nCaching tests completed.")
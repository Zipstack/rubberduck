#!/usr/bin/env python3
"""
Debug script to test Rubberduck OpenAI proxy emulation
"""

import os
import json
from openai import OpenAI

def test_direct_openai():
    """Test direct OpenAI API call"""
    print("=== Testing Direct OpenAI API ===")
    
    client = OpenAI()  # Uses default API endpoint
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'hello world' and nothing else."}],
            max_tokens=10,
            temperature=0
        )
        print("✅ Direct OpenAI: SUCCESS")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Usage: {response.usage}")
        print()
        return True
    except Exception as e:
        print(f"❌ Direct OpenAI: FAILED - {e}")
        print()
        return False

def test_rubberduck_proxy():
    """Test Rubberduck proxy"""
    print("=== Testing Rubberduck Proxy ===")
    
    client = OpenAI(
        base_url="http://localhost:8010/v1"  # Point to Rubberduck proxy
    )
    
    try:
        print("Sending request to Rubberduck proxy...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'hello world' and nothing else."}],
            max_tokens=10,
            temperature=0
        )
        print("✅ Rubberduck Proxy: SUCCESS")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Usage: {response.usage}")
        print()
        return True
    except Exception as e:
        print(f"❌ Rubberduck Proxy: FAILED - {e}")
        print(f"Error type: {type(e).__name__}")
        print()
        return False

def test_raw_http():
    """Test raw HTTP request to see exact response"""
    print("=== Testing Raw HTTP Request ===")
    
    import requests
    
    url = "http://localhost:8010/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Accept-Encoding": "identity"  # Disable compression to avoid gzip issues
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say 'hello world' and nothing else."}],
        "max_tokens": 10,
        "temperature": 0
    }
    
    try:
        print(f"Making raw HTTP POST to: {url}")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Try to get raw content first
        try:
            print(f"Raw content length: {len(response.content)} bytes")
            print(f"Response text: {response.text[:500]}...")  # First 500 chars
        except Exception as e:
            print(f"Error reading response: {e}")
            print(f"Raw bytes: {response.content[:100]}...")
        
        print()
        
        if response.status_code == 200:
            try:
                json_resp = response.json()
                print("✅ Raw HTTP: SUCCESS - Valid JSON response")
                if 'choices' in json_resp:
                    print(f"Message: {json_resp['choices'][0]['message']['content']}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Raw HTTP: FAILED - Invalid JSON: {e}")
                return False
        else:
            print(f"❌ Raw HTTP: FAILED - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Raw HTTP: FAILED - {e}")
        print()
        return False

if __name__ == "__main__":
    print("Testing Rubberduck OpenAI Proxy Emulation")
    print("=" * 50)
    print()
    
    # Check if API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not set")
        exit(1)
    
    results = []
    
    # Test direct OpenAI first to verify setup
    results.append(("Direct OpenAI", test_direct_openai()))
    
    # Test raw HTTP to see exact response
    results.append(("Raw HTTP", test_raw_http()))
    
    # Test through OpenAI SDK with proxy
    results.append(("Rubberduck Proxy", test_rubberduck_proxy()))
    
    print("=" * 50)
    print("SUMMARY:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
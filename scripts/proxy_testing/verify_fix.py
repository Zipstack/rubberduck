#!/usr/bin/env python3
"""
Verify the fix by examining the cleaned up headers
"""

import os
import requests

def verify_header_cleanup():
    """Verify that problematic headers have been filtered out"""
    print("=== Verifying Header Cleanup ===")
    
    url = "http://localhost:8010/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Test message"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        print(f"Status: {response.status_code}")
        print("\n✅ Headers successfully received:")
        
        # Check for good headers (should be present)
        good_headers = [
            'content-type', 'openai-organization', 'openai-processing-ms',
            'openai-version', 'x-ratelimit-limit-requests', 'x-request-id'
        ]
        
        # Check for bad headers (should be filtered out)
        bad_headers = [
            'content-encoding', 'content-length', 'transfer-encoding',
            'set-cookie', 'cf-ray', 'cf-cache-status', 'alt-svc'
        ]
        
        present_good = []
        present_bad = []
        
        for key, value in response.headers.items():
            key_lower = key.lower()
            if key_lower in good_headers:
                present_good.append(f"  ✅ {key}: {value}")
            elif key_lower in bad_headers:
                present_bad.append(f"  ❌ {key}: {value}")
            else:
                print(f"  ℹ️  {key}: {value}")
        
        print("\nGood headers present:")
        for header in present_good:
            print(header)
        
        if present_bad:
            print("\n❌ Bad headers that should have been filtered:")
            for header in present_bad:
                print(header)
            return False
        else:
            print("\n✅ All problematic headers successfully filtered!")
            
        # Check if we can parse JSON
        try:
            json_data = response.json()
            print(f"\n✅ JSON parsing successful")
            print(f"Response: {json_data.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')}")
            return True
        except Exception as e:
            print(f"\n❌ JSON parsing failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_cache_behavior():
    """Test that cache hits also have clean headers"""
    print("\n=== Testing Cache Behavior ===")
    
    url = "http://localhost:8010/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }
    
    # Use same data to trigger cache hit
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Cache test"}],
        "max_tokens": 5,
        "temperature": 0  # Ensure deterministic caching
    }
    
    try:
        # First request (should be cache miss)
        print("Making first request (cache miss)...")
        response1 = requests.post(url, headers=headers, json=data)
        cache_status1 = response1.headers.get('x-cache', 'UNKNOWN')
        print(f"First request - X-Cache: {cache_status1}")
        
        # Second request (should be cache hit)
        print("Making second request (cache hit)...")
        response2 = requests.post(url, headers=headers, json=data)
        cache_status2 = response2.headers.get('x-cache', 'UNKNOWN')
        print(f"Second request - X-Cache: {cache_status2}")
        
        # Verify both responses are clean
        for i, response in enumerate([response1, response2], 1):
            print(f"\nResponse {i} headers check:")
            if 'content-encoding' in response.headers:
                print(f"  ❌ content-encoding found: {response.headers['content-encoding']}")
                return False
            else:
                print(f"  ✅ content-encoding properly filtered")
                
            if response.headers.get('server') == 'uvicorn':
                print(f"  ✅ server header is clean: uvicorn")
            else:
                print(f"  ❌ server header issue: {response.headers.get('server')}")
                
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False

if __name__ == "__main__":
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set")
        exit(1)
    
    success1 = verify_header_cleanup()
    success2 = test_cache_behavior()
    
    print("\n" + "="*50)
    print("FINAL RESULTS:")
    print(f"Header cleanup: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Cache behavior: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 Rubberduck OpenAI proxy is working correctly!")
    else:
        print("\n❌ Some issues remain")
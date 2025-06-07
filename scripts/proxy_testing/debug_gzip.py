#!/usr/bin/env python3
"""
Debug gzip issues with Rubberduck proxy
"""

import os
import json
import gzip
import requests

def test_with_manual_gzip_handling():
    """Test with manual gzip handling"""
    print("=== Testing with Manual Gzip Handling ===")
    
    url = "http://localhost:8010/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }
    data = {
        "model": "gpt-4o-mini", 
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5
    }
    
    try:
        # Make request without automatic decompression
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Get raw content
        raw_content = response.content
        print(f"Raw content length: {len(raw_content)} bytes")
        print(f"First 50 bytes: {raw_content[:50]}")
        
        # Check if it's gzipped
        if raw_content.startswith(b'\x1f\x8b'):
            print("Content appears to be gzipped")
            try:
                decompressed = gzip.decompress(raw_content)
                print(f"Decompressed content: {decompressed.decode('utf-8')}")
                
                # Try to parse as JSON
                json_data = json.loads(decompressed.decode('utf-8'))
                print("✅ Manual gzip handling: SUCCESS")
                return True
                
            except Exception as e:
                print(f"❌ Failed to decompress: {e}")
                return False
        else:
            print("Content is not gzipped")
            try:
                text = raw_content.decode('utf-8')
                print(f"Content: {text}")
                json_data = json.loads(text)
                print("✅ Plain text: SUCCESS")
                return True
            except Exception as e:
                print(f"❌ Failed to parse: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_with_no_compression():
    """Test explicitly disabling compression"""
    print("=== Testing with No Compression ===")
    
    import urllib3
    # Disable compression in urllib3
    urllib3.disable_warnings()
    
    url = "http://localhost:8010/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Accept-Encoding": "identity"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5
    }
    
    try:
        # Create session with no compression
        session = requests.Session()
        session.headers.update({"Accept-Encoding": "identity"})
        
        response = session.post(url, headers=headers, json=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content: {response.text}")
        
        if response.status_code == 200:
            json_data = response.json()
            print("✅ No compression: SUCCESS")
            return True
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    print("Debugging Gzip Issues")
    print("=" * 30)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set")
        exit(1)
    
    test_with_manual_gzip_handling()
    print()
    test_with_no_compression()
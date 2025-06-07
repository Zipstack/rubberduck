#!/usr/bin/env python3
"""
Test the specific gzip header issue and propose a fix
"""

import os
import json
import requests

def test_current_issue():
    """Test the current issue to understand exactly what's happening"""
    print("=== Testing Current Issue ===")
    
    url = "http://localhost:8010/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 5
    }
    
    try:
        # Make request with streaming to access raw response
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        print(f"Status: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        # Look at raw content
        raw_content = response.content
        print(f"\nRaw content length: {len(raw_content)}")
        print(f"First 50 bytes: {raw_content[:50]}")
        
        # Check if gzipped
        if raw_content.startswith(b'\x1f\x8b'):
            print("✅ Content is properly gzipped")
            import gzip
            try:
                decompressed = gzip.decompress(raw_content)
                print(f"Decompressed: {decompressed.decode('utf-8')}")
                return True
            except Exception as e:
                print(f"❌ Gzip decompression failed: {e}")
                return False
        else:
            print("❌ Content is not gzipped despite headers claiming it is")
            try:
                print(f"Content as text: {raw_content.decode('utf-8')}")
                return False
            except:
                print("Content is not valid text either")
                return False
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def identify_problematic_headers():
    """Identify which headers are causing issues"""
    print("\n=== Identifying Problematic Headers ===")
    
    # Headers that should NOT be forwarded from upstream to client
    problematic_headers = [
        'content-encoding',  # FastAPI will handle encoding
        'content-length',    # FastAPI will recalculate
        'transfer-encoding', # FastAPI manages transfer
        'connection',        # Connection-specific
        'server',           # Should be uvicorn, not upstream
        'date',             # Should be current request time
        'set-cookie',       # Session-specific to upstream
        'vary',             # Caching directive
        'cache-control',    # Caching directive  
        'etag',             # Entity tag from upstream
        'last-modified',    # From upstream
        'expires',          # From upstream
        'alt-svc',          # Alternative service
        'cf-ray',           # Cloudflare specific
        'cf-cache-status',  # Cloudflare specific
        'x-cache',          # May conflict with our own
        'strict-transport-security',  # Security policy
        'x-content-type-options',     # Security policy
        'x-envoy-upstream-service-time',  # Infrastructure specific
    ]
    
    print("Headers that should be filtered out:")
    for header in problematic_headers:
        print(f"  - {header}")
    
    return problematic_headers

if __name__ == "__main__":
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set")
        exit(1)
    
    test_current_issue()
    identify_problematic_headers()
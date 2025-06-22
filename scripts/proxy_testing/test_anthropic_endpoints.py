#!/usr/bin/env python3
"""
Test if Anthropic proxy endpoints are properly configured
"""

import requests
import json
from rich.console import Console

console = Console()

def test_endpoint(endpoint, description):
    """Test a specific endpoint"""
    url = f"http://localhost:8005{endpoint}"
    headers = {
        "Content-Type": "application/json", 
        "x-api-key": "dummy-key"  # Use dummy key to test routing
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "test"}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        console.print(f"{description}: {response.status_code}")
        
        if response.status_code == 401:
            try:
                error_data = response.json()
                if "authentication_error" in str(error_data):
                    console.print(f"  ✅ Endpoint exists and authenticates properly")
                    return True
            except:
                pass
        elif response.status_code == 200:
            console.print(f"  ✅ Success!")
            return True
        elif response.status_code == 404:
            console.print(f"  ❌ Endpoint not found")
            return False
        
        console.print(f"  Response: {response.text[:200]}")
        return False
        
    except requests.exceptions.ConnectionError:
        console.print(f"  ❌ Cannot connect to proxy")
        return False
    except Exception as e:
        console.print(f"  ❌ Error: {e}")
        return False

def test_anthropic_sdk_routing():
    """Test that the SDK can at least connect to the proxy"""
    console.print("\n=== Testing SDK Connection ===")
    
    try:
        import anthropic
        
        # Test different base URLs
        for base_url in ["http://localhost:8005", "http://localhost:8005/v1"]:
            console.print(f"\nTesting base_url: {base_url}")
            
            client = anthropic.Anthropic(
                api_key="dummy-key",
                base_url=base_url
            )
            
            try:
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "test"}]
                )
                console.print(f"  ✅ SDK Success with {base_url}")
                return True
            except anthropic.AuthenticationError:
                console.print(f"  ✅ SDK connected (auth error expected) with {base_url}")
                return True
            except anthropic.APIConnectionError as e:
                console.print(f"  ❌ SDK connection failed: {e}")
            except Exception as e:
                console.print(f"  ❌ SDK error: {e}")
                
    except ImportError:
        console.print("❌ Anthropic SDK not installed")
        
    return False

def main():
    console.print("🧪 Testing Anthropic Proxy Endpoints", style="bold green")
    
    # Test individual endpoints
    endpoints = [
        ("/messages", "Legacy /messages"),
        ("/v1/messages", "SDK /v1/messages"),
        ("/complete", "Legacy /complete"), 
        ("/v1/complete", "SDK /v1/complete")
    ]
    
    endpoint_results = []
    for endpoint, description in endpoints:
        result = test_endpoint(endpoint, description)
        endpoint_results.append((description, result))
    
    # Test SDK routing
    sdk_works = test_anthropic_sdk_routing()
    
    # Summary
    console.print(f"\n{'='*50}")
    console.print("📊 SUMMARY", style="bold")
    for desc, result in endpoint_results:
        status = "✅ WORKS" if result else "❌ MISSING"
        console.print(f"{desc}: {status}")
    
    console.print(f"SDK Routing: {'✅ WORKS' if sdk_works else '❌ FAILED'}")
    
    if all(result for _, result in endpoint_results) and sdk_works:
        console.print("\n🎉 Anthropic proxy endpoints are properly configured!", style="green")
        console.print("The proxy should now work with the official Anthropic SDK")
    else:
        console.print("\n⚠️  Some endpoints may need attention", style="yellow")

if __name__ == "__main__":
    main()
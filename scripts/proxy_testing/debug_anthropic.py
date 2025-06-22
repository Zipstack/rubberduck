#!/usr/bin/env python3
"""
Debug script for Anthropic proxy issues.
Tests direct API, raw HTTP, and SDK connections to isolate the problem.
"""

import os
import sys
import json
import requests
import httpx
from rich.console import Console
from rich.text import Text

console = Console()

def test_direct_anthropic_api():
    """Test direct connection to Anthropic API"""
    console.print("\n=== Testing Direct Anthropic API ===", style="bold blue")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        console.print("❌ ANTHROPIC_API_KEY not set", style="red")
        return False
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        console.print(f"✅ Direct API Status: {response.status_code}")
        console.print(f"Response Headers: {dict(response.headers)}")
        if response.status_code == 200:
            content = response.json()
            console.print(f"Response: {content.get('content', [{}])[0].get('text', 'N/A')}")
        else:
            console.print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        console.print(f"❌ Direct API failed: {e}", style="red")
        return False

def test_raw_http_to_proxy():
    """Test raw HTTP request to Rubberduck Anthropic proxy"""
    console.print("\n=== Testing Raw HTTP to Rubberduck Proxy ===", style="bold blue")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        console.print("❌ ANTHROPIC_API_KEY not set", style="red")
        return False
    
    url = "http://localhost:8005/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Hello proxy"}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        console.print(f"✅ Proxy HTTP Status: {response.status_code}")
        console.print(f"Response Headers: {dict(response.headers)}")
        if response.status_code == 200:
            content = response.json()
            console.print(f"Response: {content.get('content', [{}])[0].get('text', 'N/A')}")
        else:
            console.print(f"Error: {response.text}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError as e:
        console.print(f"❌ Connection failed: {e}", style="red")
        console.print("💡 Is the Anthropic proxy running on port 8005?", style="yellow")
        return False
    except Exception as e:
        console.print(f"❌ Raw HTTP failed: {e}", style="red")
        return False

def test_anthropic_sdk_direct():
    """Test official Anthropic SDK connecting directly to API"""
    console.print("\n=== Testing Anthropic SDK (Direct) ===", style="bold blue")
    
    try:
        import anthropic
    except ImportError:
        console.print("❌ anthropic package not installed", style="red")
        return False
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        console.print("❌ ANTHROPIC_API_KEY not set", style="red")
        return False
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        console.print("Making request to direct API...")
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello SDK"}]
        )
        
        console.print("✅ SDK Direct API Success")
        console.print(f"Response: {response.content[0].text}")
        return True
        
    except Exception as e:
        console.print(f"❌ SDK Direct API failed: {e}", style="red")
        return False

def test_anthropic_sdk_via_proxy():
    """Test official Anthropic SDK connecting via Rubberduck proxy"""
    console.print("\n=== Testing Anthropic SDK (Via Proxy) ===", style="bold blue")
    
    try:
        import anthropic
    except ImportError:
        console.print("❌ anthropic package not installed", style="red")
        return False
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        console.print("❌ ANTHROPIC_API_KEY not set", style="red")
        return False
    
    try:
        # Configure client to use proxy
        client = anthropic.Anthropic(
            api_key=api_key,
            base_url="http://localhost:8005/v1"  # Point to proxy
        )
        
        console.print("Making request via proxy...")
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello proxy SDK"}]
        )
        
        console.print("✅ SDK Proxy Success")
        console.print(f"Response: {response.content[0].text}")
        return True
        
    except anthropic.APIConnectionError as e:
        console.print(f"❌ SDK Proxy connection failed: {e}", style="red")
        console.print("💡 This suggests the proxy is not responding to SDK requests", style="yellow")
        return False
    except Exception as e:
        console.print(f"❌ SDK Proxy failed: {e}", style="red")
        return False

def test_anthropic_sdk_via_proxy_v1():
    """Test SDK with correct v1 endpoint"""
    console.print("\n=== Testing Anthropic SDK (Via Proxy /v1) ===", style="bold blue")
    
    try:
        import anthropic
    except ImportError:
        console.print("❌ anthropic package not installed", style="red")
        return False
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        console.print("❌ ANTHROPIC_API_KEY not set", style="red")
        return False
    
    try:
        # Try different base URL configurations
        for base_url in ["http://localhost:8005", "http://localhost:8005/v1"]:
            console.print(f"Trying base_url: {base_url}")
            
            client = anthropic.Anthropic(
                api_key=api_key,
                base_url=base_url
            )
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello proxy SDK"}]
            )
            
            console.print(f"✅ SDK Proxy Success with {base_url}")
            console.print(f"Response: {response.content[0].text}")
            return True
            
    except Exception as e:
        console.print(f"❌ SDK Proxy failed: {e}", style="red")
        return False

def test_proxy_endpoints():
    """Test what endpoints are available on the proxy"""
    console.print("\n=== Testing Proxy Endpoints ===", style="bold blue")
    
    # Test basic connectivity
    try:
        response = requests.get("http://localhost:8005/", timeout=5)
        console.print(f"Root endpoint status: {response.status_code}")
    except Exception as e:
        console.print(f"❌ Cannot connect to proxy: {e}", style="red")
        return False
    
    # Test various endpoints that might be available
    endpoints_to_test = [
        "/messages",
        "/v1/messages", 
        "/complete",
        "/v1/complete",
        "/health",
        "/status"
    ]
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    for endpoint in endpoints_to_test:
        url = f"http://localhost:8005{endpoint}"
        try:
            # Try GET first
            response = requests.get(url, timeout=5)
            console.print(f"GET {endpoint}: {response.status_code}")
            
            # Try POST for message endpoints
            if "messages" in endpoint:
                data = {
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Test"}]
                }
                response = requests.post(url, headers=headers, json=data, timeout=10)
                console.print(f"POST {endpoint}: {response.status_code}")
                if response.status_code == 200:
                    console.print(f"✅ Found working endpoint: {endpoint}")
                    return True
                elif response.text:
                    console.print(f"Error response: {response.text[:200]}")
                    
        except Exception as e:
            console.print(f"❌ {endpoint}: {str(e)[:100]}")
    
    return False

def check_proxy_logs_instruction():
    """Provide instructions for checking proxy logs"""
    console.print("\n=== Checking Proxy Logs ===", style="bold blue")
    console.print("💡 To see if requests are reaching Rubberduck:", style="yellow")
    console.print("1. In another terminal, run the Rubberduck backend")
    console.print("2. Watch for log entries when making requests")
    console.print("3. Look for entries like: 'Proxy request: POST /messages'")
    console.print("4. If no logs appear, the request isn't reaching the proxy")

def main():
    console.print("🐛 Anthropic Proxy Debug Script", style="bold green")
    console.print("This script will test various ways of connecting to Anthropic")
    
    # Test sequence
    tests = [
        ("Direct Anthropic API", test_direct_anthropic_api),
        ("Raw HTTP to Proxy", test_raw_http_to_proxy), 
        ("SDK Direct", test_anthropic_sdk_direct),
        ("SDK via Proxy", test_anthropic_sdk_via_proxy),
        ("SDK via Proxy v1", test_anthropic_sdk_via_proxy_v1),
        ("Proxy Endpoints", test_proxy_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        console.print(f"\n{'='*50}")
        try:
            success = test_func()
            results.append((test_name, success))
        except KeyboardInterrupt:
            console.print("\n❌ Test interrupted by user", style="red")
            break
        except Exception as e:
            console.print(f"❌ {test_name} crashed: {e}", style="red")
            results.append((test_name, False))
    
    # Summary
    console.print(f"\n{'='*50}")
    console.print("📊 SUMMARY", style="bold")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        console.print(f"{test_name}: {status}")
    
    check_proxy_logs_instruction()
    
    # Analysis
    console.print("\n🔍 ANALYSIS", style="bold")
    if not any(success for _, success in results[1:]):  # Skip direct API
        console.print("❌ No proxy tests passed - proxy may not be running or configured correctly")
    elif results[1][1] and not results[3][1]:  # Raw HTTP works but SDK doesn't
        console.print("💡 Raw HTTP works but SDK fails - likely an endpoint mismatch")
    elif not results[1][1]:  # Raw HTTP fails
        console.print("💡 Raw HTTP fails - check if proxy is running on port 8005")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        console.print("Usage: python debug_anthropic.py")
        console.print("Environment variables needed:")
        console.print("- ANTHROPIC_API_KEY: Your Anthropic API key")
        console.print("- Proxy should be running on localhost:8005")
        sys.exit(0)
    
    main()
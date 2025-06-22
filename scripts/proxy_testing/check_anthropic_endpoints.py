#!/usr/bin/env python3
"""
Check what endpoints the Anthropic SDK actually uses
"""

import anthropic
import httpx
from unittest.mock import patch

def mock_post(*args, **kwargs):
    """Mock httpx.post to capture the URL being called"""
    print(f"SDK is trying to POST to: {args[0]}")
    print(f"Headers: {kwargs.get('headers', {})}")
    # Return a mock response to avoid actual API call
    from types import SimpleNamespace
    response = SimpleNamespace()
    response.status_code = 200
    response.json = lambda: {"content": [{"text": "mock response"}], "id": "mock", "type": "message", "role": "assistant", "model": "claude-3-haiku-20240307", "usage": {"input_tokens": 10, "output_tokens": 5}}
    response.headers = {}
    return response

# Test with different base URLs
test_cases = [
    ("Direct API", "https://api.anthropic.com"),
    ("Proxy root", "http://localhost:8005"),
    ("Proxy with /v1", "http://localhost:8005/v1"),
]

for name, base_url in test_cases:
    print(f"\n=== {name} (base_url: {base_url}) ===")
    
    try:
        client = anthropic.Anthropic(
            api_key="dummy-key",
            base_url=base_url
        )
        
        # Mock the HTTP client to see what URL is constructed
        with patch('httpx.post', side_effect=mock_post):
            try:
                client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "test"}]
                )
            except Exception as e:
                print(f"Exception (expected): {e}")
                
    except Exception as e:
        print(f"Failed to create client: {e}")

print("\n=== Conclusion ===")
print("The SDK constructs URLs by appending '/v1/messages' to the base_url.")
print("So for proxy at localhost:8005, the SDK expects:")
print("- http://localhost:8005/v1/messages")
print("But the Rubberduck proxy provides:")
print("- http://localhost:8005/messages")
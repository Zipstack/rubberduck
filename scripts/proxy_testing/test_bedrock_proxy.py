#!/usr/bin/env python3
"""
Test script to debug AWS Bedrock proxy issues.
"""

import boto3
import json
import logging
import sys

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

def test_bedrock_proxy(proxy_url=None):
    """Test AWS Bedrock through proxy."""
    
    print(f"Testing AWS Bedrock {'with proxy at ' + proxy_url if proxy_url else 'directly'}")
    
    # Create client - always use real AWS credentials
    # The proxy will pass through the authentication headers to AWS
    client_config = {
        'region_name': 'us-east-1'
    }
    
    if proxy_url:
        client_config['endpoint_url'] = proxy_url
        print(f"Using proxy endpoint: {proxy_url}")
    
    client = boto3.client('bedrock-runtime', **client_config)
    
    # Model to test
    model_id = "meta.llama3-2-1b-instruct-v1:0"
    
    # Test payload - Llama models use different format
    payload = {
        "prompt": "Hello, how are you?",
        "max_gen_len": 100,
        "temperature": 0
    }
    
    try:
        # Enable debug logging for boto3
        boto3.set_stream_logger('', logging.DEBUG)
        
        print(f"\nInvoking model: {model_id}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(payload)
        )
        
        print("\nSuccess!")
        print(f"Response: {response}")
        
        # Parse response body
        body = json.loads(response['body'].read())
        print(f"Response body: {json.dumps(body, indent=2)}")
        
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with proxy if URL provided
    proxy_url = sys.argv[1] if len(sys.argv) > 1 else None
    test_bedrock_proxy(proxy_url)
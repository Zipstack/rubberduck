#!/usr/bin/env python3
"""Test AWS Bedrock proxy with boto3 proxy-aware configuration."""

import boto3
import json
import os
from botocore.config import Config

def test_bedrock_proxy_aware():
    """Test Bedrock with boto3 proxy configuration."""
    
    # Check AWS credentials
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    if not access_key or not secret_key:
        print("Error: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set")
        return
    
    print(f"Using AWS credentials: {access_key[:5]}...")
    print(f"Region: {region}")
    
    # Create Bedrock client with our proxy as endpoint URL
    # This bypasses the standard AWS endpoint and uses our proxy instead
    client = boto3.client(
        'bedrock-runtime',
        endpoint_url='http://localhost:8009',
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    
    model_id = "meta.llama3-2-1b-instruct-v1:0"
    
    # Request payload for Llama model
    request_body = {
        "prompt": "Hello, how are you?",
        "max_gen_len": 100,
        "temperature": 0
    }
    
    print(f"\nTesting boto3 request via endpoint override to model: {model_id}")
    print(f"Request body: {json.dumps(request_body, indent=2)}")
    print("Endpoint URL: http://localhost:8009")
    
    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        print(f"\nSuccess!")
        print(f"Response: {json.dumps(response_body, indent=2)}")
        
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)}")
        
        # Print additional debugging info
        if hasattr(e, 'response'):
            print(f"Error response: {e.response}")

if __name__ == "__main__":
    test_bedrock_proxy_aware()
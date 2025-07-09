#!/usr/bin/env python3
"""Test AWS Bedrock request re-signing logic."""

import json
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

# Test the re-signing logic
def test_resigning():
    # Get AWS credentials
    session = boto3.Session()
    credentials = session.get_credentials()
    
    if not credentials:
        print("No AWS credentials found!")
        return
    
    print(f"Using AWS credentials: {credentials.access_key[:5]}...")
    
    # Create test request
    region = "us-east-1"
    model_id = "meta.llama3-2-1b-instruct-v1:0"
    endpoint = f"/model/{model_id}/invoke"
    url = f"https://bedrock-runtime.{region}.amazonaws.com{endpoint}"
    
    request_data = {
        "prompt": "Hello, how are you?",
        "max_gen_len": 100,
        "temperature": 0
    }
    
    request_body = json.dumps(request_data)
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Rubberduck-Proxy/0.1.0",
        "Accept": "application/json",
        "Host": f"bedrock-runtime.{region}.amazonaws.com"
    }
    
    # Create AWS request for signing
    aws_request = AWSRequest(
        method='POST',
        url=url,
        data=request_body,
        headers=headers
    )
    
    # Sign the request
    signer = SigV4Auth(credentials, 'bedrock', region)
    signer.add_auth(aws_request)
    
    print("\nSigned headers:")
    for k, v in aws_request.headers.items():
        print(f"  {k}: {v}")
    
    print("\nRequest URL:", url)
    print("Request body:", request_body)

if __name__ == "__main__":
    test_resigning()
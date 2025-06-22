# AWS Bedrock Proxy Implementation Guide

## Overview

This document explains the AWS Bedrock proxy implementation in Rubberduck, including the architectural decisions and usage patterns.

## Architecture: API Proxy vs HTTP CONNECT Proxy

### Why Not Traditional HTTP CONNECT Proxy?

Traditional HTTP proxies use the `CONNECT` method to establish tunnels:

```
Client -> CONNECT bedrock-runtime.us-east-1.amazonaws.com:443 HTTP/1.1
Proxy  -> HTTP/1.1 200 Connection established
Client <-> Proxy <-> AWS (encrypted tunnel)
```

**FastAPI Limitation**: FastAPI does not natively support the HTTP `CONNECT` method, making traditional proxy implementation impractical.

**boto3 Expectation**: When using `Config(proxies={'https': 'http://localhost:8009'})`, boto3 attempts to use HTTP CONNECT tunneling, which our FastAPI server cannot handle.

### Our Solution: API Reverse Proxy

Instead, we implemented an **API reverse proxy** that intercepts, processes, and forwards HTTP requests:

```
Client -> HTTP POST /model/{model_id}/invoke
Proxy  -> Process, cache, re-sign, forward
AWS    -> Receive properly signed request
```

## Dual-Mode Authentication

Our Bedrock proxy supports two authentication modes:

### Mode 1: Custom Headers (Recommended) ✅

**How it works**:
1. Client sends unsigned request with credentials in headers
2. Proxy extracts credentials and re-signs request for AWS
3. Full caching, error injection, and logging support

**Usage**:
```python
import requests

headers = {
    "Content-Type": "application/json",
    "X-AWS-Access-Key": "AKIA...",
    "X-AWS-Secret-Key": "your-secret-key",
    "X-AWS-Session-Token": "optional-session-token"  # For STS credentials
}

payload = {
    "prompt": "Hello, how are you?",
    "max_gen_len": 100,
    "temperature": 0
}

response = requests.post(
    "http://localhost:8009/model/meta.llama3-2-1b-instruct-v1:0/invoke",
    json=payload,
    headers=headers
)
```

**Advantages**:
- ✅ Works reliably with all AWS models
- ✅ Full proxy feature support (caching, error injection)
- ✅ Easy to implement in any HTTP client
- ✅ Consistent authentication flow

### Mode 2: boto3 Endpoint Override ⚠️

**How it works**:
1. Client uses boto3 with custom `endpoint_url`
2. boto3 signs request for proxy endpoint (not AWS)
3. Proxy forwards signed request to AWS
4. AWS rejects due to signature mismatch

**Usage**:
```python
import boto3

client = boto3.client(
    'bedrock-runtime',
    endpoint_url='http://localhost:8009',  # Override AWS endpoint
    region_name='us-east-1',
    aws_access_key_id='AKIA...',
    aws_secret_access_key='your-secret-key'
)

response = client.invoke_model(
    modelId='meta.llama3-2-1b-instruct-v1:0',
    body=json.dumps({
        "prompt": "Hello, how are you?",
        "max_gen_len": 100,
        "temperature": 0
    })
)
```

**Limitations**:
- ❌ AWS signature mismatch (signed for localhost, not AWS)
- ❌ Results in `InvalidSignatureException`
- ⚠️ Works for request forwarding but fails authentication

## Implementation Details

### Request Detection (`bedrock.py:81-86`)

```python
auth_header = headers.get("authorization") or headers.get("Authorization", "")

if auth_header and auth_header.startswith("AWS4-HMAC-SHA256"):
    # Mode 2: Forward signed request (limited functionality)
    return await self._forward_signed_request(...)
else:
    # Mode 1: Re-sign with custom headers (recommended)
```

### Custom Headers Processing (`bedrock.py:91-103`)

```python
client_access_key = headers.get("x-aws-access-key") or headers.get("X-AWS-Access-Key")
client_secret_key = headers.get("x-aws-secret-key") or headers.get("X-AWS-Secret-Key")
client_session_token = headers.get("x-aws-session-token") or headers.get("X-AWS-Session-Token")

if client_access_key and client_secret_key:
    credentials = Credentials(
        access_key=client_access_key,
        secret_key=client_secret_key,
        token=client_session_token
    )
```

### Request Re-signing (`bedrock.py:116-137`)

```python
# Create AWS request for signing
aws_request = AWSRequest(
    method='POST',
    url=url,  # https://bedrock-runtime.us-east-1.amazonaws.com/...
    data=request_body,
    headers=api_headers
)

# Sign with correct AWS endpoint
signer = SigV4Auth(credentials, 'bedrock', region)
signer.add_auth(aws_request)
```

## Supported Models and Endpoints

### Endpoints
- `/model/{model_id}/invoke` - Synchronous inference
- `/model/{model_id}/invoke-with-response-stream` - Streaming inference
- `/foundation-models` - List available models
- `/custom-models` - List custom models

### Model Examples
- `anthropic.claude-3-haiku-20240307-v1:0`
- `meta.llama3-2-1b-instruct-v1:0`
- `amazon.titan-text-express-v1`

## Error Handling

### Common Errors

1. **No Credentials**:
```json
{
  "error": {
    "message": "No AWS credentials found. For unsigned requests, provide credentials via X-AWS-Access-Key/X-AWS-Secret-Key headers...",
    "type": "authentication_error"
  }
}
```

2. **Invalid Model**:
```json
{
  "message": "Invocation of model ID meta.llama3-2-1b-instruct-v1:0 with on-demand throughput isn't supported..."
}
```

3. **Signature Mismatch** (Mode 2):
```json
{
  "Error": {
    "Code": "InvalidSignatureException",
    "Message": "The request signature we calculated does not match the signature you provided..."
  }
}
```

## Testing

### Test Custom Headers Approach (Recommended)
```bash
source ~/.zshrc && source venv/bin/activate && python test_bedrock_unsigned.py
```

### Test boto3 Endpoint Override (Limited)
```bash
source ~/.zshrc && source venv/bin/activate && python test_bedrock_proxy_aware.py
```

### Test Error Scenarios
```bash
source ~/.zshrc && source venv/bin/activate && python test_bedrock_errors.py
```
Tests: No credentials, invalid credentials, invalid model, malformed requests

### Test Caching Functionality
```bash
source ~/.zshrc && source venv/bin/activate && python test_bedrock_caching.py
```
Tests: Cache hits/misses, request normalization, error response handling

## Best Practices

1. **Use Custom Headers**: Always prefer the custom headers approach for reliable operation
2. **Secure Credentials**: Never log or expose AWS credentials in headers
3. **Handle Errors**: Implement proper error handling for authentication and model availability
4. **Monitor Usage**: Use Rubberduck's logging to track proxy usage and errors

## Troubleshooting

### boto3 ProxyConnectionError
**Problem**: boto3 tries to use HTTP CONNECT tunneling
**Solution**: Use custom headers approach instead of proxy configuration

### InvalidSignatureException
**Problem**: Signature calculated for wrong endpoint
**Solution**: Use custom headers to let proxy re-sign requests

### Model Not Available
**Problem**: Specific model not accessible in your AWS account
**Solution**: Check AWS Bedrock console for available models and inference profiles

## Future Considerations

### HTTP CONNECT Support
To implement true HTTP CONNECT proxy support would require:
1. Custom ASGI middleware for CONNECT method handling
2. TCP tunneling implementation
3. Raw socket forwarding (beyond FastAPI scope)

**Recommendation**: The current custom headers approach provides all necessary functionality for API-level proxying with the benefits of caching, error injection, and logging.

### Alternative Approaches
- Use dedicated proxy software (Squid, HAProxy) for HTTP CONNECT needs
- Implement separate TCP proxy for tunnel-based scenarios
- Continue with API-level proxying for LLM use cases
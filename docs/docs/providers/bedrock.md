# AWS Bedrock Provider

Learn how to configure and use Rubberduck with AWS Bedrock, including important architectural considerations and authentication methods.

## Architecture Overview

### Why API Reverse Proxy?

Rubberduck implements an **API reverse proxy** rather than a traditional HTTP CONNECT proxy for AWS Bedrock. This architectural decision addresses specific limitations:

**FastAPI CONNECT Limitation:**
- FastAPI does not natively support the HTTP `CONNECT` method
- Traditional proxies require CONNECT tunneling for signed requests
- Our API approach provides full functionality for LLM use cases

**Traditional vs. Our Approach:**
```
Traditional: Client -> CONNECT Proxy -> AWS (encrypted tunnel)
Rubberduck:  Client -> API Proxy -> AWS (request processing & re-signing)
```

### Benefits of Our Approach
- ✅ Full caching, error injection, and logging support
- ✅ Request/response monitoring and analytics
- ✅ Failure simulation capabilities
- ✅ Cost tracking and token usage monitoring
- ✅ Compatible with all Bedrock models and features

## Authentication Methods

Rubberduck supports two authentication modes for AWS Bedrock:

### Mode 1: Custom Headers (Recommended) ✅

**How it works:**
1. Client sends unsigned request with AWS credentials in headers
2. Proxy extracts credentials and re-signs request for AWS
3. Full proxy features work seamlessly

**Usage Example:**
```python
import requests
import json

# AWS credentials
headers = {
    "Content-Type": "application/json",
    "X-AWS-Access-Key": "AKIA...",
    "X-AWS-Secret-Key": "your-secret-key",
    "X-AWS-Session-Token": "optional-session-token"  # For STS credentials
}

# Request payload
payload = {
    "prompt": "Hello, how are you?",
    "max_gen_len": 100,
    "temperature": 0
}

# Make request to Rubberduck proxy
response = requests.post(
    "http://localhost:8009/model/meta.llama3-2-1b-instruct-v1:0/invoke",
    json=payload,
    headers=headers
)

print(response.json())
```

**Advantages:**
- ✅ Works reliably with all AWS Bedrock models
- ✅ Full proxy feature support (caching, error injection, logging)
- ✅ Easy to implement in any HTTP client
- ✅ Consistent authentication flow

### Mode 2: boto3 Endpoint Override ⚠️

**How it works:**
1. Client uses boto3 with custom `endpoint_url`
2. boto3 signs request for proxy endpoint (not AWS)
3. Proxy forwards signed request to AWS
4. AWS rejects due to signature mismatch

**Usage Example:**
```python
import boto3
import json

# Configure boto3 to use Rubberduck proxy
client = boto3.client(
    'bedrock-runtime',
    endpoint_url='http://localhost:8009',  # Rubberduck proxy
    region_name='us-east-1',
    aws_access_key_id='AKIA...',
    aws_secret_access_key='your-secret-key'
)

# This will fail due to signature mismatch
try:
    response = client.invoke_model(
        modelId='meta.llama3-2-1b-instruct-v1:0',
        body=json.dumps({
            "prompt": "Hello, how are you?",
            "max_gen_len": 100,
            "temperature": 0
        })
    )
except Exception as e:
    print(f"Error: {e}")  # InvalidSignatureException
```

**Limitations:**
- ❌ AWS signature mismatch (signed for localhost, not AWS)
- ❌ Results in `InvalidSignatureException`
- ⚠️ Limited functionality due to authentication issues

## Supported Endpoints

### Model Invocation
- `/model/{model_id}/invoke` - Synchronous inference
- `/model/{model_id}/invoke-with-response-stream` - Streaming inference

### Model Management
- `/foundation-models` - List available foundation models
- `/custom-models` - List custom/fine-tuned models

### Example Model IDs
- `anthropic.claude-3-haiku-20240307-v1:0`
- `meta.llama3-2-1b-instruct-v1:0`
- `amazon.titan-text-express-v1`
- `amazon.nova-micro-v1:0`
- `amazon.nova-lite-v1:0`

## Implementation Details

### Request Detection
Rubberduck automatically detects the authentication method:

```python
# Check for existing AWS signature
auth_header = headers.get("authorization") or headers.get("Authorization", "")

if auth_header and auth_header.startswith("AWS4-HMAC-SHA256"):
    # Mode 2: Forward signed request (limited functionality)
    return await self._forward_signed_request(...)
else:
    # Mode 1: Re-sign with custom headers (recommended)
    return await self._resign_request(...)
```

### Custom Headers Processing
The proxy extracts AWS credentials from custom headers:

```python
client_access_key = headers.get("X-AWS-Access-Key")
client_secret_key = headers.get("X-AWS-Secret-Key")
client_session_token = headers.get("X-AWS-Session-Token")  # Optional

if client_access_key and client_secret_key:
    credentials = Credentials(
        access_key=client_access_key,
        secret_key=client_secret_key,
        token=client_session_token
    )
```

### Request Re-signing
For custom headers mode, the proxy re-signs requests:

```python
# Create AWS request for signing
aws_request = AWSRequest(
    method='POST',
    url=f"https://bedrock-runtime.{region}.amazonaws.com/model/{model_id}/invoke",
    data=request_body,
    headers=api_headers
)

# Sign with correct AWS endpoint
signer = SigV4Auth(credentials, 'bedrock', region)
signer.add_auth(aws_request)
```

## Error Handling

### Common Error Responses

**No Credentials Provided:**
```json
{
  "error": {
    "message": "No AWS credentials found. For unsigned requests, provide credentials via X-AWS-Access-Key/X-AWS-Secret-Key headers.",
    "type": "authentication_error"
  }
}
```

**Invalid Model:**
```json
{
  "message": "Invocation of model ID meta.llama3-2-1b-instruct-v1:0 with on-demand throughput isn't supported. Provide 'provisionedModelId' instead."
}
```

**Signature Mismatch (Mode 2):**
```json
{
  "Error": {
    "Code": "InvalidSignatureException",
    "Message": "The request signature we calculated does not match the signature you provided..."
  }
}
```

### Error Troubleshooting

**Authentication Issues:**
1. Verify AWS credentials are correct
2. Check credential permissions for Bedrock access
3. Ensure region matches model availability

**Model Access Issues:**
1. Verify model is enabled in your AWS account
2. Check model regional availability
3. Confirm you have Bedrock permissions

**Network Issues:**
1. Verify Rubberduck proxy is running
2. Check firewall settings
3. Confirm AWS connectivity

## Testing

### Test Custom Headers (Recommended)
```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Run test script
python test_bedrock_unsigned.py
```

### Test boto3 Override (Limited)
```bash
# Run boto3 test (will show signature mismatch)
python test_bedrock_proxy_aware.py
```

### Test Error Scenarios
```bash
# Test various error conditions
python test_bedrock_errors.py
```

### Test Caching
```bash
# Test cache behavior
python test_bedrock_caching.py
```

## Best Practices

### Recommended Approach
1. **Always use custom headers method** for reliable operation
2. **Set credentials via environment variables** for security
3. **Implement proper error handling** for authentication and model availability
4. **Monitor usage** through Rubberduck's logging features

### Security Considerations
1. **Never log AWS credentials** in headers or request bodies
2. **Use IAM roles** when possible instead of access keys
3. **Rotate credentials regularly**
4. **Monitor for unusual access patterns**

### Performance Optimization
1. **Enable caching** for repeated requests
2. **Use appropriate regions** to minimize latency
3. **Monitor request patterns** to optimize cache hit rates
4. **Set reasonable timeout values**

## Limitations & Future Considerations

### Current Limitations
- boto3 proxy mode has signature mismatch issues
- Traditional HTTP CONNECT tunneling not supported
- Custom implementation required for perfect boto3 compatibility

### Potential Solutions
To implement true HTTP CONNECT proxy support would require:
1. Custom ASGI middleware for CONNECT method handling
2. TCP tunneling implementation
3. Raw socket forwarding (beyond FastAPI scope)

### Recommendation
The current custom headers approach provides all necessary functionality for API-level proxying with full benefits of caching, error injection, and logging. This is the recommended approach for most use cases.

### Alternative Approaches
For environments requiring HTTP CONNECT tunneling:
- Use dedicated proxy software (Squid, HAProxy)
- Implement separate TCP proxy for tunnel-based scenarios
- Continue with API-level proxying for LLM use cases (recommended)

## Next Steps

After setting up AWS Bedrock:

1. **[Learn proxy management](/usage/managing-proxies)** - Control your Bedrock proxies
2. **[Monitor requests](/logging)** - Track Bedrock usage and costs
3. **Configure failure simulation** - Test resilience
4. **[Explore the testing client](/testing-client)** - Load test your Bedrock integration

---

Need help with Bedrock setup? Check the test scripts in `scripts/proxy_testing/` for working examples.
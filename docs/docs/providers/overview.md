# Provider-Specific Notes

This section contains important configuration notes and guidelines for each supported LLM provider.

## Supported Providers

Rubberduck supports the following LLM providers with full SDK compatibility:

- **[AWS Bedrock](/providers/bedrock)** - Amazon's managed LLM service
- **OpenAI** - GPT models and completions API
- **Anthropic** - Claude models via Messages API
- **Azure OpenAI** - Microsoft-hosted OpenAI models
- **Google Vertex AI** - Google's AI platform
- **Deepseek** - Deepseek's language models

## General Provider Guidelines

### Authentication
- All providers require API keys or credentials passed through in requests
- Rubberduck never stores or logs API keys for security
- Authentication is transparently passed to the upstream provider

### Request Compatibility
- Rubberduck maintains full compatibility with official SDKs
- No code changes required in your applications
- Simply change the base URL to point to your Rubberduck proxy

### Response Handling
- Responses are returned exactly as received from providers
- Headers, status codes, and error formats are preserved
- Caching is applied transparently without affecting response format

## Provider-Specific Considerations

### AWS Bedrock
AWS Bedrock requires special handling due to its signature-based authentication system. See the [detailed Bedrock guide](/providers/bedrock) for:
- Dual-mode authentication options
- Custom headers approach (recommended)
- Limitations with traditional proxy methods
- Testing and troubleshooting

### OpenAI
- Full compatibility with OpenAI Python SDK
- Supports both chat completions and legacy completions
- Works with all GPT models and embeddings

### Anthropic
- Full compatibility with Anthropic Python SDK
- Supports Claude-3 family and newer models
- Messages API integration

### Azure OpenAI
- Compatible with Azure OpenAI Python SDK
- Supports Azure-specific model deployments
- Handles Azure authentication requirements

### Google Vertex AI
- Compatible with google-generativeai library
- Supports Gemini and PaLM model families
- Handles Google Cloud authentication

### Deepseek
- OpenAI-compatible API structure
- Full SDK compatibility with base URL override
- Supports chat and code completion models

## Common Integration Patterns

### Basic Usage
```python
# Instead of:
client = Provider(api_key="your-key")

# Use:
client = Provider(
    api_key="your-key",
    base_url="http://localhost:8001"  # Your proxy port
)
```

### Error Handling
```python
try:
    response = client.create_completion(...)
except ProviderError as e:
    # Handle both proxy and provider errors
    print(f"Request failed: {e}")
```

### Monitoring Integration
```python
import time
start_time = time.time()
response = client.create_completion(...)
end_time = time.time()

print(f"Request took {end_time - start_time:.2f}s")
# Check Rubberduck logs for detailed metrics
```

## Troubleshooting

### Common Issues
1. **Authentication Failures**: Verify API keys are correct and have proper permissions
2. **Network Timeouts**: Check provider connectivity and proxy health
3. **Model Availability**: Ensure models are available in your provider account
4. **Rate Limiting**: Monitor proxy logs for rate limit responses

### Provider-Specific Troubleshooting
- **AWS Bedrock**: Check AWS credentials and model access permissions
- **Azure OpenAI**: Verify deployment names and API versions
- **Google Vertex AI**: Ensure proper project and region configuration

For detailed provider-specific troubleshooting, see the individual provider guides.
# Using Proxies

Learn how to integrate Rubberduck proxies with your applications and SDKs for seamless LLM provider switching and testing.

## Integration Overview

Rubberduck proxies are designed to be drop-in replacements for direct LLM provider connections. Simply change your base URL to point to your Rubberduck proxy, and everything else remains the same.

## Basic Integration Pattern

### Standard Approach
```python
# Direct provider connection
client = ProviderSDK(
    api_key="your-api-key",
    # base_url defaults to provider's endpoint
)

# Rubberduck proxy connection  
client = ProviderSDK(
    api_key="your-api-key",
    base_url="http://localhost:8001"  # Your proxy port
)
```

## Provider-Specific Examples

### OpenAI Integration

```python
import openai

# Using Rubberduck proxy
client = openai.OpenAI(
    api_key="your-openai-api-key",
    base_url="http://localhost:8001"
)

# Chat completion (same as direct OpenAI)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=150
)

print(response.choices[0].message.content)
```

### Anthropic Integration

```python
import anthropic

# Using Rubberduck proxy
client = anthropic.Anthropic(
    api_key="your-anthropic-api-key",
    base_url="http://localhost:8002"
)

# Create message (same as direct Anthropic)
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    temperature=0.7,
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)

print(response.content[0].text)
```

### AWS Bedrock Integration

```python
import requests
import json

# Bedrock requires custom headers approach
headers = {
    "Content-Type": "application/json",
    "X-AWS-Access-Key": "AKIA...",
    "X-AWS-Secret-Key": "your-secret-key",
}

payload = {
    "prompt": "Hello, how are you?",
    "max_gen_len": 100,
    "temperature": 0.7
}

response = requests.post(
    "http://localhost:8003/model/meta.llama3-2-1b-instruct-v1:0/invoke",
    json=payload,
    headers=headers
)

result = response.json()
print(result)
```

## Advanced Usage Patterns

### Environment-Based Configuration

```python
import os
import openai

# Configure based on environment
if os.getenv("USE_RUBBERDUCK", "false").lower() == "true":
    base_url = f"http://localhost:{os.getenv('RUBBERDUCK_PORT', '8001')}"
else:
    base_url = None  # Use default OpenAI endpoint

client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=base_url
)
```

### Error Handling and Retries

```python
import openai
import time
from openai import OpenAI

def make_request_with_retry(client, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**kwargs)
            return response
        except openai.RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except openai.APIError as e:
            print(f"API error: {e}")
            raise

# Usage
client = OpenAI(
    api_key="your-key",
    base_url="http://localhost:8001"
)

response = make_request_with_retry(
    client,
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Multi-Provider Fallback

```python
import openai
import anthropic

class MultiProviderClient:
    def __init__(self):
        self.openai_client = openai.OpenAI(
            api_key="openai-key",
            base_url="http://localhost:8001"  # OpenAI proxy
        )
        self.anthropic_client = anthropic.Anthropic(
            api_key="anthropic-key", 
            base_url="http://localhost:8002"  # Anthropic proxy
        )
    
    def chat_completion(self, message, provider="openai"):
        try:
            if provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": message}]
                )
                return response.choices[0].message.content
            elif provider == "anthropic":
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": message}]
                )
                return response.content[0].text
        except Exception as e:
            print(f"Error with {provider}: {e}")
            # Fallback to other provider
            if provider == "openai":
                return self.chat_completion(message, "anthropic")
            else:
                return self.chat_completion(message, "openai")

# Usage
client = MultiProviderClient()
response = client.chat_completion("Hello!")
```

## Configuration Management

### Using Configuration Files

```python
# config.yaml
providers:
  openai:
    base_url: "http://localhost:8001"
    api_key_env: "OPENAI_API_KEY"
  anthropic:
    base_url: "http://localhost:8002" 
    api_key_env: "ANTHROPIC_API_KEY"

# client.py
import yaml
import os

def load_config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def create_openai_client():
    config = load_config()
    openai_config = config['providers']['openai']
    
    return openai.OpenAI(
        api_key=os.getenv(openai_config['api_key_env']),
        base_url=openai_config['base_url']
    )
```

### Dynamic Proxy Selection

```python
import random
import openai

# Multiple OpenAI proxies for load balancing
OPENAI_PROXIES = [
    "http://localhost:8001",
    "http://localhost:8002", 
    "http://localhost:8003"
]

def create_balanced_client():
    proxy_url = random.choice(OPENAI_PROXIES)
    return openai.OpenAI(
        api_key="your-key",
        base_url=proxy_url
    )

# Usage
client = create_balanced_client()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Monitoring Integration

### Request Timing

```python
import time
import openai

class TimedClient:
    def __init__(self, base_url=None):
        self.client = openai.OpenAI(
            api_key="your-key",
            base_url=base_url
        )
        self.request_times = []
    
    def timed_request(self, **kwargs):
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(**kwargs)
            end_time = time.time()
            request_time = end_time - start_time
            self.request_times.append(request_time)
            print(f"Request completed in {request_time:.2f}s")
            return response
        except Exception as e:
            end_time = time.time()
            request_time = end_time - start_time
            print(f"Request failed after {request_time:.2f}s: {e}")
            raise
    
    def get_average_time(self):
        if self.request_times:
            return sum(self.request_times) / len(self.request_times)
        return 0

# Usage
client = TimedClient("http://localhost:8001")
response = client.timed_request(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(f"Average request time: {client.get_average_time():.2f}s")
```

### Custom Headers for Tracking

```python
import openai

# Custom client with request tracking
class TrackedClient:
    def __init__(self, base_url, user_id=None):
        self.client = openai.OpenAI(
            api_key="your-key",
            base_url=base_url,
            default_headers={
                "X-User-ID": user_id or "unknown",
                "X-App-Version": "1.0.0"
            }
        )
    
    def chat_completion(self, **kwargs):
        return self.client.chat.completions.create(**kwargs)

# Usage
client = TrackedClient("http://localhost:8001", user_id="user123")
response = client.chat_completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Best Practices

### Connection Management

```python
import openai
from contextlib import contextmanager

@contextmanager
def llm_client(provider="openai", proxy_port=8001):
    """Context manager for LLM clients"""
    if provider == "openai":
        client = openai.OpenAI(
            api_key="your-key",
            base_url=f"http://localhost:{proxy_port}"
        )
    # Add other providers as needed
    
    try:
        yield client
    finally:
        # Cleanup if needed
        pass

# Usage
with llm_client("openai", 8001) as client:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
```

### Async Usage

```python
import asyncio
import openai

async def async_chat_completion():
    client = openai.AsyncOpenAI(
        api_key="your-key",
        base_url="http://localhost:8001"
    )
    
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    
    return response.choices[0].message.content

# Usage
async def main():
    result = await async_chat_completion()
    print(result)

asyncio.run(main())
```

## Troubleshooting

### Common Issues

**Connection Refused:**
- Verify proxy is running and accessible
- Check firewall settings
- Confirm correct port number

**Authentication Errors:**
- Verify API keys are correct
- Check provider-specific authentication requirements
- Ensure credentials have proper permissions

**Timeout Issues:**
- Increase client timeout settings
- Check proxy configuration
- Monitor provider response times

### Debugging Tools

```python
import logging
import openai

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Create client with debug info
client = openai.OpenAI(
    api_key="your-key",
    base_url="http://localhost:8001",
    max_retries=3,
    timeout=30.0
)

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
except Exception as e:
    logging.error(f"Request failed: {e}")
    # Check Rubberduck logs for more details
```

## Next Steps

After integrating proxies with your applications:

1. **[Monitor your requests](/logging)** - Track performance and usage
2. **Configure failure simulation** - Test resilience
3. **[Explore the testing client](/testing-client)** - Load test your integrations
4. **Set up alerts** - Monitor for issues

---

Need provider-specific integration help? Check our [Provider-Specific Notes](/providers/overview) for detailed examples.
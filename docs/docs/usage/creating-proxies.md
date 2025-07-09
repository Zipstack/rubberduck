# Creating Proxies

Learn how to create and configure LLM proxy instances in Rubberduck to connect to your favorite providers.

## Overview

Rubberduck proxies are individual instances that connect to specific LLM providers. Each proxy runs on its own port and can be configured independently with different settings for caching, failure simulation, and monitoring.

## Creating Your First Proxy

### 1. Navigate to the Proxies Page

From the main dashboard, click on **"Proxies"** in the sidebar navigation.

<div className="screenshot">

![Proxies Management](/img/proxies-management.png)

</div>

### 2. Click "Create Proxy"

Click the blue **"Create Proxy"** button in the top-right corner of the Proxies page.

### 3. Configure Your Proxy

A modal dialog will appear with the following configuration options:

<div className="screenshot">

![Create Proxy Modal](/img/create-proxy-modal.png)

</div>

#### Required Fields

**Proxy Name** (Required)
- Choose a descriptive name for your proxy
- Example: "My OpenAI Proxy", "Production Claude", "Test Bedrock"
- This name will appear in the dashboard and logs

**Provider** (Required)
- Select from the supported providers:
  - **OpenAI** - GPT models and completions
  - **Anthropic** - Claude models
  - **Azure OpenAI** - Microsoft-hosted OpenAI models
  - **AWS Bedrock** - Amazon's managed LLM service
  - **Google Vertex AI** - Google's AI platform
  - **Deepseek** - Deepseek's language models

#### Optional Fields

**Port** (Optional)
- Specify a custom port number for your proxy
- If left empty, Rubberduck will automatically assign an available port
- Range: 8001-9999 (avoiding conflicts with the main server)

**Description** (Optional)
- Add notes about this proxy's purpose
- Examples: "Used for production chat features", "Testing new prompts", "Research experiments"

### 4. Create the Proxy

Click the **"Create Proxy"** button to create your new proxy instance.

## Supported Providers

### OpenAI
- **Models**: GPT-4, GPT-3.5-turbo, GPT-3.5-turbo-instruct, and newer models
- **Endpoints**: Chat completions and legacy completions
- **Authentication**: API key required in requests

### Anthropic (Claude)
- **Models**: Claude-3 Haiku, Sonnet, Opus and newer versions
- **Endpoints**: Messages API
- **Authentication**: API key required in requests

### Azure OpenAI
- **Models**: Azure-hosted OpenAI models
- **Endpoints**: Chat completions with Azure-specific paths
- **Authentication**: Azure API key required

### AWS Bedrock
- **Models**: Claude, Llama, Titan, Nova and other Bedrock models
- **Endpoints**: Model invocation with streaming support
- **Authentication**: AWS credentials (see [Bedrock-specific guide](/providers/bedrock))

### Google Vertex AI
- **Models**: Gemini Pro, Gemini Ultra, and PaLM models
- **Endpoints**: Vertex AI generate content API
- **Authentication**: Google Cloud credentials

### Deepseek
- **Models**: Deepseek Chat and Code models
- **Endpoints**: OpenAI-compatible chat completions
- **Authentication**: Deepseek API key

## Provider-Specific Configuration

### OpenAI Configuration
When creating an OpenAI proxy, your applications can use it like this:

```python
import openai

client = openai.OpenAI(
    api_key="your-openai-api-key",
    base_url="http://localhost:8001"  # Your proxy port
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Anthropic Configuration
For Anthropic proxies:

```python
import anthropic

client = anthropic.Anthropic(
    api_key="your-anthropic-api-key",
    base_url="http://localhost:8002"  # Your proxy port
)

response = client.messages.create(
    model="claude-3-sonnet-20240229",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### AWS Bedrock Configuration
Bedrock requires special configuration. See our [Bedrock-specific guide](/providers/bedrock) for detailed setup instructions.

## Port Management

### Automatic Port Assignment
- Rubberduck automatically assigns ports starting from 8001
- Ports are incremented for each new proxy
- Conflicts are automatically avoided

### Custom Port Assignment
- You can specify a custom port during creation
- Useful for consistent development environments
- Rubberduck will warn if the port is already in use

### Port Ranges
- **Reserved**: Ports 8000 (backend) and 5173 (frontend)
- **Available**: Ports 8001-9999 for proxy instances
- **Recommended**: Leave port assignment to automatic for simplicity

## After Creation

Once your proxy is created, you'll see it in the proxies list with:

- **Status indicator**: Green dot for running, gray for stopped
- **Provider and port information**
- **Action buttons**: Start, Stop, Configure, Actions menu
- **Quick stats**: Current RPM and status

## Best Practices

### Naming Conventions
- Use descriptive names that indicate purpose
- Include provider name for clarity
- Examples: "OpenAI-Production", "Claude-Research", "Bedrock-Testing"

### Organization
- Create separate proxies for different environments (dev, staging, prod)
- Use one proxy per provider to avoid configuration conflicts
- Group related proxies with consistent naming

### Security
- Never include API keys in proxy names or descriptions
- Use environment variables for sensitive configuration
- Regularly rotate API keys used with proxies

## Common Issues

### Port Conflicts
**Problem**: "Port already in use" error
**Solution**: Use automatic port assignment or choose a different port

### Provider Authentication
**Problem**: Authentication failures with LLM providers
**Solution**: Verify API keys are correct and have proper permissions

### Network Access
**Problem**: Cannot reach the proxy endpoint
**Solution**: Check firewall settings and ensure the proxy is running

## Next Steps

After creating your proxy:

1. **[Learn to manage proxies](/usage/managing-proxies)** - Start, stop, and configure your proxies
2. **[Use your proxy](/usage/using-proxies)** - Integrate with your applications
3. **[Monitor requests](/logging)** - Track usage and performance
4. **Configure failure simulation** - Test resilience

---

Ready to start using your proxy? Check out the [Managing Proxies](/usage/managing-proxies) guide next.
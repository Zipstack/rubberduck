---
sidebar_position: 1
slug: /
---

# Introduction

Welcome to **Rubberduck** – a local LLM caching reverse proxy with advanced testing capabilities designed for developers building LLM-powered applications.

<div className="screenshot">

![Dashboard Overview](/img/dashboard-overview.png)

</div>

## What is Rubberduck?

Rubberduck is a powerful reverse proxy server that sits between your applications and LLM providers, offering:

- **Caching** to reduce costs and improve performance
- **Failure simulation** to test your application's resilience  
- **Comprehensive monitoring** to track usage and performance
- **Multi-provider support** for testing across different LLM services

## Top Features

### 🔄 **LLM Provider Emulation**
- **Universal compatibility**: Works with OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Google Vertex AI, and Deepseek
- **Perfect SDK integration**: No code changes needed - just point your existing SDKs to Rubberduck
- **Transparent passthrough**: Headers and authentication flow through seamlessly

### 💾 **Intelligent Caching**
- **SHA-256 cache keys**: Based on normalized request content for perfect cache hits
- **Selective caching**: Only successful responses (2xx) are cached
- **Manual invalidation**: Clear cache per proxy instance when needed
- **Upstream respect**: Honors provider caching headers

### 🧪 **Advanced Failure Simulation**
- **Timeout injection**: Test with fixed delays or indefinite hangs
- **Error injection**: Configure specific HTTP error codes (429, 500, 400) with individual failure rates
- **IP filtering**: Allow/block lists with CIDR and wildcard support
- **Rate limiting**: Simulate provider rate limits with requests per minute controls

### 📊 **Comprehensive Monitoring**
- **Real-time dashboards**: Live metrics for all proxy instances
- **Detailed logging**: Request metadata, latency, cache status, and costs
- **Export capabilities**: CSV/JSON export for analysis
- **Cost tracking**: Monitor token usage and estimated costs

### 🎨 **Beautiful Web Interface**
- **Stripe-inspired design**: Clean, modern, and responsive UI
- **Live updates**: Real-time status and metrics
- **Intuitive management**: Easy proxy creation and configuration
- **Advanced filtering**: Search and filter logs with multiple criteria

## Where Rubberduck Excels

### 🚀 **Development & Testing**
Perfect for developers who need to:
- Test LLM application resilience under various failure conditions
- Optimize costs through intelligent caching
- Debug and monitor LLM interactions
- Load test applications without hitting provider rate limits

### 🏢 **Team Environments**
Ideal for teams that want to:
- Share cached responses across development environments
- Monitor team-wide LLM usage and costs
- Test applications against multiple providers
- Simulate production failure scenarios safely

### 🔬 **Research & Analysis**
Excellent for researchers who need to:
- Compare performance across different LLM providers
- Analyze request patterns and response characteristics
- Cache expensive research queries
- Export detailed usage data for analysis

## Getting Started

Ready to improve your LLM development workflow? Let's get you set up:

1. **[Install Rubberduck](/installation)** - Set up the backend and frontend
2. **[Create your first proxy](/usage/creating-proxies)** - Connect to your favorite LLM provider
3. **[Start monitoring](/logging)** - Track requests and optimize performance

## Default Access

Rubberduck creates a default admin user on first startup:
- **Email**: `admin@example.com`
- **Password**: `admin`

This allows immediate access without registration, perfect for getting started quickly.

---

**Ready to dive in?** Start with our [Installation Guide](/installation) to get Rubberduck running in minutes.

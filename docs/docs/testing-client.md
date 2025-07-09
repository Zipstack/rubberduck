# Testing Client Guide

The Rubberduck testing client is a comprehensive load testing tool designed specifically for LLM proxies. Located at `scripts/proxy_testing/tester.py`, it provides advanced features for testing proxy performance, reliability, and behavior under various conditions.

## Overview

The testing client is a single-file Python CLI that fires controllable requests at LLM proxy servers. It supports all major providers, measures comprehensive metrics, and provides detailed reporting capabilities.

### Key Features

- **Multi-Provider Support**: Test OpenAI, Anthropic, AWS Bedrock, Azure OpenAI, Google Vertex AI, and Deepseek
- **Load Testing Capabilities**: Configurable concurrency and request volumes
- **Intelligent Data Management**: Maximum sentence uniqueness and diversity tracking
- **Comprehensive Metrics**: Latency statistics, success rates, and percentile analysis
- **Flexible Output Formats**: Table, JSON, and CSV reporting
- **Interactive & Non-Interactive Modes**: CLI automation and guided setup
- **Direct & Proxy Testing**: Test providers directly or through Rubberduck proxies

## Installation & Setup

### Prerequisites

The testing client requires several Python packages. Install them in the testing environment:

```bash
cd scripts/proxy_testing
pip install -r requirements.txt
```

**Required Packages:**
- `typer` - CLI framework
- `questionary` - Interactive prompts
- `rich` - Terminal formatting
- `requests` - HTTP client
- `openai` - OpenAI SDK
- `anthropic` - Anthropic SDK
- `boto3` - AWS SDK
- `google-generativeai` - Google AI SDK (optional)

### API Key Configuration

Set environment variables for the providers you want to test:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# AWS Bedrock
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."

# Azure OpenAI
export AZURE_OPENAI_API_KEY="..."

# Google Vertex AI
export GOOGLE_API_KEY="..."

# Deepseek
export DEEPSEEK_API_KEY="sk-..."
```

### Seed Data Setup

Create test data files in the `unstructured_data/` directory:

```
unstructured_data/
├── chat_prompts.txt
├── code_completion.txt
└── creative_writing.txt
```

**File Format:**
```
### Prompt
You are a helpful assistant. Please respond to the following:

---

How do I implement a binary search algorithm?

What are the benefits of using Docker containers?

Explain the concept of machine learning in simple terms.
```

The `---` delimiter separates the prompt template from the individual test sentences.

## Usage Modes

### Interactive Mode

Launch without parameters for guided setup:

```bash
python tester.py
```

The interactive mode walks you through:
1. **Provider Selection**: Choose from available providers
2. **Model Selection**: Pick from provider-specific models
3. **Request Volume**: Select number of requests (1, 5, 10, 25, 50, 100)
4. **Concurrency Level**: Choose concurrent request count (1, 5, 10)
5. **Data Selection**: Single-file or all-files mode

### Non-Interactive Mode

Use command-line parameters for automation:

```bash
# Test OpenAI through Rubberduck proxy
python tester.py \
  --provider openai \
  --model gpt-4 \
  --num-requests 50 \
  --concurrency 5 \
  --proxy-url http://localhost:8001 \
  --log-file results.jsonl

# Test Anthropic directly (no proxy)
python tester.py \
  --provider anthropic \
  --model claude-3-sonnet-20240229 \
  --num-requests 25 \
  --concurrency 3 \
  --output-format json

# Test AWS Bedrock through proxy with custom headers
python tester.py \
  --provider aws-bedrock \
  --model amazon.nova-micro-v1:0 \
  --num-requests 10 \
  --proxy-url http://localhost:8009 \
  --json-response
```

## Configuration Options

### Core Parameters

**Provider & Model:**
```bash
--provider, -p        # LLM provider (openai, anthropic, aws-bedrock, etc.)
--model, -m          # Model name (gpt-4, claude-3-sonnet-20240229, etc.)
```

**Load Testing:**
```bash
--num-requests, -n   # Number of requests to send (default: 1)
--concurrency, -c    # Concurrent request count (default: 1)
--timeout, -t        # Request timeout in seconds (default: 30)
```

**Data Management:**
```bash
--data-dir, -d       # Seed data directory (default: ./unstructured_data)
--selection-mode, -s # single-file or all-files (default: single-file)
```

**Connection:**
```bash
--proxy-url, -u      # Rubberduck proxy URL (omit for direct connection)
--api-key, -k        # Override API key (uses env vars by default)
```

**Output & Logging:**
```bash
--output-format, -o  # table, json, or csv (default: table)
--log-file, -l       # Log file path for detailed results
--json-response, -j  # Include full JSON responses in logs
```

**Mode Control:**
```bash
--interactive/--no-interactive, -i  # Force interactive/non-interactive mode
```

### Advanced Configuration

**Models Configuration File:**
The `models.json` file defines available models per provider:

```json
{
  "openai": [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-instruct"
  ],
  "anthropic": [
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307"
  ],
  "aws-bedrock": [
    "amazon.nova-micro-v1:0",
    "amazon.nova-lite-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "meta.llama3-2-1b-instruct-v1:0"
  ]
}
```

## Testing Scenarios

### Basic Functionality Test

Test basic proxy connectivity and response handling:

```bash
python tester.py \
  --provider openai \
  --model gpt-4 \
  --num-requests 5 \
  --proxy-url http://localhost:8001
```

### Load Testing

Test proxy performance under sustained load:

```bash
python tester.py \
  --provider anthropic \
  --model claude-3-sonnet-20240229 \
  --num-requests 100 \
  --concurrency 10 \
  --proxy-url http://localhost:8002 \
  --log-file anthropic_load_test.jsonl
```

### Multi-Provider Comparison

Compare performance across different providers:

```bash
# Test OpenAI
python tester.py --provider openai --model gpt-4 --num-requests 25 --proxy-url http://localhost:8001 --output-format json > openai_results.json

# Test Anthropic
python tester.py --provider anthropic --model claude-3-sonnet-20240229 --num-requests 25 --proxy-url http://localhost:8002 --output-format json > anthropic_results.json

# Test Bedrock
python tester.py --provider aws-bedrock --model amazon.nova-micro-v1:0 --num-requests 25 --proxy-url http://localhost:8009 --output-format json > bedrock_results.json
```

### Failure Resilience Testing

Test proxy behavior under failure conditions by configuring failure simulation in Rubberduck:

```bash
# Test with high error rate configured in proxy
python tester.py \
  --provider openai \
  --model gpt-4 \
  --num-requests 50 \
  --concurrency 5 \
  --proxy-url http://localhost:8001 \
  --log-file failure_test.jsonl \
  --json-response
```

### Cache Performance Testing

Test cache hit rates with repeated requests:

```bash
# First run to populate cache
python tester.py --provider openai --model gpt-4 --num-requests 10 --proxy-url http://localhost:8001

# Second run to test cache hits (should be faster)
python tester.py --provider openai --model gpt-4 --num-requests 10 --proxy-url http://localhost:8001 --selection-mode single-file
```

## Data Management Features

### Sentence Uniqueness Tracking

The testing client maximizes sentence diversity to provide realistic testing scenarios:

**Single-File Mode:**
- Uses one randomly selected data file
- Maximizes uniqueness within that file's sentences
- Reports unique vs. repeated sentence usage

**All-Files Mode:**
- Aggregates sentences from all data files
- Maximizes uniqueness across the entire dataset
- Provides larger sentence pool for extensive testing

### Example Output:
```
Using file: chat_prompts.txt (45 unique sentences available)
Used 25 unique sentences, 0 repeated sentences
All 25 sentences are unique!
```

## Metrics & Reporting

### Comprehensive Metrics

The testing client tracks detailed performance metrics:

**Request Metrics:**
- Total requests sent
- Success count (2xx/3xx responses)
- Failure count (4xx/5xx/exceptions)
- Total response bytes

**Latency Statistics:**
- Minimum, average, median, maximum latency
- 95th and 99th percentile response times
- Only successful requests included in latency stats

### Output Formats

#### Table Format (Default)
```
┌─────────────────┬──────────┐
│ Metric          │ Value    │
├─────────────────┼──────────┤
│ Total Requests  │ 50       │
│ Successful      │ 48       │
│ Failed          │ 2        │
│ Total Bytes     │ 125,340  │
│ Min Latency     │ 245.67ms │
│ Avg Latency     │ 1,234.56ms│
│ Median Latency  │ 1,100.23ms│
│ 95th Percentile │ 2,345.67ms│
│ 99th Percentile │ 2,567.89ms│
│ Max Latency     │ 2,678.90ms│
└─────────────────┴──────────┘
```

#### JSON Format
```json
{
  "total_requests": 50,
  "success_count": 48,
  "failure_count": 2,
  "total_bytes": 125340,
  "latency_stats": {
    "min_ms": 245.67,
    "avg_ms": 1234.56,
    "median_ms": 1100.23,
    "p95_ms": 2345.67,
    "p99_ms": 2567.89,
    "max_ms": 2678.90
  }
}
```

#### CSV Format
```csv
total_requests,success_count,failure_count,total_bytes,min_ms,avg_ms,median_ms,p95_ms,p99_ms,max_ms
50,48,2,125340,245.67,1234.56,1100.23,2345.67,2567.89,2678.90
```

### Detailed Logging

Enable detailed logging with `--log-file` and `--json-response`:

```jsonl
{"request_id": 1, "status_code": "200", "latency_ms": 1234.56, "response": "...", "error": null}
{"request_id": 2, "status_code": "429", "latency_ms": 567.89, "response": null, "error": "Rate limit exceeded"}
{"request_id": 3, "status_code": "EXC", "latency_ms": 0.0, "response": null, "error": "Connection timeout"}

=== SUMMARY ===
{
  "total_requests": 50,
  "success_count": 47,
  "failure_count": 3,
  ...
}
```

## Provider-Specific Features

### AWS Bedrock Integration

The testing client uses the **custom headers approach** for AWS Bedrock:

```python
# Automatic credential detection from environment
headers = {
    "Content-Type": "application/json",
    "X-AWS-Access-Key": os.getenv('AWS_ACCESS_KEY_ID'),
    "X-AWS-Secret-Key": os.getenv('AWS_SECRET_ACCESS_KEY'),
    "X-AWS-Session-Token": os.getenv('AWS_SESSION_TOKEN')  # Optional
}
```

**Model-Specific Request Formatting:**
- **Nova Models**: Use `messages` format with `schemaVersion`
- **Other Models**: Use traditional `prompt` format

### Azure OpenAI Integration

Requires Azure-specific endpoint configuration:

```bash
python tester.py \
  --provider azure-openai \
  --model gpt-4 \
  --proxy-url https://your-resource.openai.azure.com \
  --api-key your-azure-key
```

### Google Vertex AI Integration

Supports Google's generative AI models:

```bash
pip install google-generativeai
python tester.py \
  --provider vertex-ai \
  --model gemini-pro \
  --proxy-url http://localhost:8004
```

## Best Practices

### Load Testing Strategy

**Gradual Ramp-Up:**
```bash
# Start with low load
python tester.py --provider openai --model gpt-4 --num-requests 5 --concurrency 1 --proxy-url http://localhost:8001

# Increase gradually
python tester.py --provider openai --model gpt-4 --num-requests 25 --concurrency 5 --proxy-url http://localhost:8001

# Full load test
python tester.py --provider openai --model gpt-4 --num-requests 100 --concurrency 10 --proxy-url http://localhost:8001
```

**Performance Baseline:**
1. Test direct provider connection (no `--proxy-url`)
2. Test through Rubberduck proxy with same parameters
3. Compare latency and success rates

### Data Management

**Diverse Test Data:**
- Create multiple data files for different use cases
- Include various prompt types (chat, completion, coding)
- Use realistic sentence lengths and complexity

**File Organization:**
```
unstructured_data/
├── chat_conversations.txt    # Conversational prompts
├── code_completion.txt       # Programming tasks
├── creative_writing.txt      # Creative prompts
├── technical_qa.txt          # Technical questions
└── multilingual.txt          # Non-English content
```

### Result Analysis

**Automated Testing Pipeline:**
```bash
#!/bin/bash
# test_all_providers.sh

providers=("openai" "anthropic" "aws-bedrock")
models=("gpt-4" "claude-3-sonnet-20240229" "amazon.nova-micro-v1:0")
ports=("8001" "8002" "8009")

for i in "${!providers[@]}"; do
    provider="${providers[i]}"
    model="${models[i]}"
    port="${ports[i]}"
    
    echo "Testing $provider..."
    python tester.py \
        --provider "$provider" \
        --model "$model" \
        --num-requests 25 \
        --concurrency 5 \
        --proxy-url "http://localhost:$port" \
        --output-format json \
        --no-interactive > "${provider}_results.json"
done
```

## Troubleshooting

### Common Issues

**Connection Errors:**
```
Error connecting to proxy: ConnectionError
```
- Verify proxy is running and accessible
- Check proxy URL and port
- Confirm firewall settings

**Authentication Failures:**
```
Request failed: 401 Unauthorized
```
- Verify API keys are set correctly
- Check environment variable names
- Confirm API key permissions

**Timeout Issues:**
```
Request failed: Request timeout
```
- Increase `--timeout` value
- Check provider response times
- Monitor proxy performance

**Import Errors:**
```
ModuleNotFoundError: No module named 'google.generativeai'
```
- Install missing packages: `pip install google-generativeai`
- Use virtual environment for clean dependencies

### Debugging Features

**Verbose Logging:**
```bash
python tester.py \
  --provider openai \
  --model gpt-4 \
  --num-requests 5 \
  --proxy-url http://localhost:8001 \
  --json-response \
  --log-file debug.jsonl
```

**Request Tracing:**
Monitor individual request progression:
```
Request 1/50 (ID: 1) - 200 (1234.56ms)
Request 2/50 (ID: 2) - 429 (567.89ms) - Rate limit exceeded
Request 3/50 (ID: 3) - EXC (0.00ms) - Connection timeout
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Proxy Load Test
on: [push, pull_request]

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
          
      - name: Install dependencies
        run: |
          cd scripts/proxy_testing
          pip install -r requirements.txt
          
      - name: Start Rubberduck
        run: |
          # Start Rubberduck backend
          python manage.py runserver &
          sleep 10
          
      - name: Run load tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd scripts/proxy_testing
          python tester.py \
            --provider openai \
            --model gpt-3.5-turbo \
            --num-requests 10 \
            --concurrency 2 \
            --proxy-url http://localhost:8001 \
            --output-format json \
            --no-interactive > results.json
            
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: scripts/proxy_testing/results.json
```

## Next Steps

After mastering the testing client:

1. **Configure failure simulation** - Test resilience scenarios
2. **[Monitor proxy performance](/logging)** - Track metrics during tests
3. **Set up automated testing** - Create CI/CD pipelines
4. **Analyze cache behavior** - Optimize cache strategies

---

The testing client is a powerful tool for validating proxy performance and reliability. Use it regularly to ensure your Rubberduck deployment meets performance requirements under various load conditions.
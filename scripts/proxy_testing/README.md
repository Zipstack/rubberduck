# LLM Proxy Load-Test Script

A comprehensive testing script that can test both direct LLM provider APIs and the Rubberduck LLM proxy. Supports multiple providers and generates detailed performance metrics.

## Features

- **Multi-Provider Support**: OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Google Vertex AI, Deepseek
- **Flexible Data Sources**: Single-file or all-files selection modes
- **Rich Metrics**: Latency percentiles, success/failure rates, throughput analysis
- **Multiple Output Formats**: Table, JSON, CSV
- **Interactive & Non-Interactive Modes**: CLI-friendly for automation

## Setup

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Direct Provider Testing (Default)
By default, the script connects directly to provider APIs:

```bash
# Interactive mode - connects directly to selected provider
python tester.py -n 10

# Direct connection to OpenAI
python tester.py -p openai -m gpt-4o-mini -n 50

# Direct connection to Anthropic  
python tester.py -p anthropic -m claude-3-haiku-20240307 -n 25
```

### Proxy Testing
Use `--proxy-url` to test through a proxy server:

```bash
# Test through local Rubberduck proxy
python tester.py -p openai -m gpt-4o -n 50 --proxy-url http://localhost:8000

# Test through proxy with logging
python tester.py -p anthropic -m claude-3-sonnet-20240229 -n 100 \
    -j -o json -l test_results.log --proxy-url http://localhost:8001
```

### Advanced Usage
```bash
# CSV output for analysis
python tester.py -p openai -m gpt-4o-mini -n 200 -o csv > results.csv

# Use all data files with rate limiting
python tester.py -p deepseek -m deepseek-chat -n 50 -s all-files -t 60

# Compare proxy vs direct performance
python tester.py -p openai -m gpt-4o-mini -n 20 -o json > direct.json
python tester.py -p openai -m gpt-4o-mini -n 20 -o json --proxy-url http://localhost:8000 > proxy.json
```

## Configuration

### Environment Variables
Set appropriate API keys:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `AZURE_OPENAI_API_KEY`
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
- `GOOGLE_API_KEY`
- `DEEPSEEK_API_KEY`

### models.json
Edit `models.json` to add/remove available models for each provider.

## Data Format

Place test data files in `unstructured_data/` directory. Each file should follow this format:

```
### Prompt
Your extraction prompt here...
---

First test sentence.

Second test sentence.

Third test sentence.
```

## Output Metrics

- **Request Counts**: Total, successful, failed
- **Latency Statistics**: Min, avg, median, p95, p99, max
- **Throughput**: Total bytes transferred
- **Error Analysis**: Exception details and HTTP status codes

## Exit Codes

- `0`: Success (proxy reachable, even with request errors)
- `1`: Proxy connection failure
- `2`: Invalid arguments in non-interactive mode
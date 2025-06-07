# LLM Proxy Load‑Test Script Specification

## 1 — Purpose

A **single‑file Python 3.10 CLI** (`tester.py`) that fires a controllable number of requests at an LLM‑proxy server which mimics six major providers. It reads natural‑language seed data, assembles requests, measures latency, and prints / saves a summary table.

Supported providers (exactly one per run):

* OpenAI
* Anthropic
* Azure OpenAI
* AWS Bedrock
* Google Vertex AI (Gemini models)
* Deepseek

## 2 — Directory & File Layout

```
project/
├── tester.py            # main script (single file)
├── models.json          # provider→[model] mapping (editable)
├── unstructured_data/   # seed data files (sample below)
│   ├── programming_languages_varied.txt
│   └── …
```

## 3 — Seed‑Data File Format

Each file follows this template:

```
### Prompt
<EXTRACTION PROMPT AS MARKDOWN>
---

<sentence 1>

<sentence 2>
…
```

* **Exactly one blank line** separates each sentence.
* The script **strips** the header (`### Prompt` → delimiter `---`) when building the payload.

### Example (abridged)

```text
### Prompt
You will receive one descriptive snippet. Parse it and return **only** JSON that fits this schema exactly:
{
  "language_name": "string",
  "designer": "string",
  "first_release_year": "number",
  "tiobe_rank_May_2025": "number",
  "primary_paradigm": "string"
}
---

Back in 1986, Adrian Martin unveiled JavaScript. …

Cooked up by Jordan White in 2003, Chronos …
```

## 4 — CLI Interface (Typer)

| Flag            | Long                               | Default                 | Notes                        |
| --------------- | ---------------------------------- | ----------------------- | ---------------------------- |
| `-p`            | `--provider`                       | *None*                  | Menu if interactive          |
| `-m`            | `--model`                          | *None*                  | Menu after provider          |
| `-n`            | `--num-requests`                   | **1**                   |                              |
| `-d`            | `--data-dir`                       | `./unstructured_data`   |                              |
| `-s`            | `--selection-mode`                 | `single-file`           | `single-file` or `all-files` |
| `-l`            | `--log-file`                       | console only            |                              |
| `-j`            | `--json-response`                  | *False*                 | Log raw JSON per request     |
| `-o`            | `--output-format`                  | `table`                 | `table`, `json`, `csv`       |
| `-i`            | `--interactive / --no-interactive` | auto (TTY)              |                              |
| `-k`            | `--api-key`                        | env var                 |                              |
| `-u`            | `--proxy-url`                      | `http://localhost:8000` |                              |
| `-t`            | `--timeout`                        | **30** seconds          |                              |
| `--models-file` |                                    | `./models.json`         |                              |

Non‑interactive mode (piped output or `--no-interactive`) **requires** `--provider` and `--model`; otherwise exit 2.

## 5 — Runtime Flow

1. **Arg parse** (Typer). Detect TTY for default interactive mode.
2. **Provider / model** resolved via menu (Questionary) if missing.
3. **Load models.json** → verify chosen model belongs to provider.
4. **Open unstructured data dir** → build iterator yielding `(prompt, sentence)` according to `selection‑mode`:

   * *single‑file*: pick a random file once, then random sentence per request.
   * *all-files*: choose random file each time.
5. **Create provider client** (see §6) with `temperature=0`, API key from CLI or env, and `base_url`=proxy.
6. **Loop N times** (sequential). For each:

   * Compose `payload = <prompt> + "\n\n" + <sentence>`.
   * Record `t0`; send request via provider’s *default completion* method.
   * Capture status code (or SDK exception), latency, and response size.
   * Optionally write raw JSON.
7. On SDK/network error *after* connecting → log as failure; continue.
8. **Summary**: min/avg/median/p95/p99/max latency, total bytes, success/failure count. Render with Rich→table; or JSON/CSV to stdout / log‑file.
9. **Exit codes**: 

   * `0` if proxy reachable (even with request errors)
   * `1` if initial connect to proxy fails

## 6 — Provider SDK Integration

| Provider                                                                               | PyPI pkg         | Client example (temperature = 0)                                                                                                                                                      | API key env            | Base‑URL override    |
| -------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | -------------------- |
| OpenAI                                                                                 | `openai`         | `client = OpenAI(api_key=KEY, base_url=URL)`<br>`resp = client.completions.create(model=model, prompt=payload, temperature=0)`                                                        | `OPENAI_API_KEY`       | `base_url` arg       |
| Anthropic                                                                              | `anthropic`      | `client = anthropic.Anthropic(api_key=KEY, base_url=URL)`<br>`resp = client.completions.create(model=model, prompt=payload, temperature=0)`                                           | `ANTHROPIC_API_KEY`    | `base_url` arg       |
| Azure OpenAI                                                                           | `openai`         | `client = AzureOpenAI(api_key=KEY, azure_endpoint=URL, api_version="2024-02-01-preview")`<br>`resp = client.completions.create(model=model, prompt=payload, temperature=0)`           | `AZURE_OPENAI_API_KEY` | `azure_endpoint` arg |
| AWS Bedrock                                                                            | `boto3`          | `brt = boto3.client("bedrock-runtime", endpoint_url=URL, region_name="us-east-1")`<br>`resp = brt.invoke_model(modelId=model, body=json.dumps({"prompt": payload, "temperature":0}))` | std AWS creds          | `endpoint_url` arg   |
| GCP Vertex AI                                                                          | `google-genai`   | \`\`\`python                                                                                                                                                                          |                        |                      |
| import google.generativeai as genai                                                    |                  |                                                                                                                                                                                       |                        |                      |
| genai.configure(api\_key=KEY, api\_endpoint=URL)                                       |                  |                                                                                                                                                                                       |                        |                      |
| model = genai.GenerativeModel(model\_name=model, generation\_config={"temperature":0}) |                  |                                                                                                                                                                                       |                        |                      |
| resp = model.generate\_content(payload)                                                |                  |                                                                                                                                                                                       |                        |                      |
| \`\`\`                                                                                 | `GOOGLE_API_KEY` | `api_endpoint`                                                                                                                                                                        |                        |                      |
| Deepseek                                                                               | `openai`         | `client = OpenAI(api_key=KEY, base_url=URL)`                                                                                                                                          | `DEEPSEEK_API_KEY`     | `base_url` arg       |

All calls are **synchronous**; no retries.

## 7 — models.json

Located in project root; overridable. Structure:

```json
{
  "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo-0125"],
  "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
  "azure-openai": ["gpt-4o", "gpt-35-turbo"],
  "aws-bedrock": ["anthropic.claude-v2", "meta.llama3-70b-instruct-v1:0"],
  "vertex-ai": ["gemini-1.5-pro-preview-0409", "gemini-1.0-pro"],
  "deepseek": ["deepseek-chat", "deepseek-coder"]
}
```

*(Latest list as of June 2025; edit freely.)*

## 8 — Dependencies (PyPI)

```
openai>=1.24.0
anthropic>=0.25.0
boto3>=1.34.0
google-genai>=0.4.1
azure-openai>=1.4.0
rich>=13.7.0
typer[all]>=0.12.0
questionary>=2.0.1
httpx>=0.27.0   # for size calculations if needed
```

> **Note**: official SDKs pull in their own transitive deps; pin as needed.

## 9 — Usage Examples

```bash
# Interactive (TTY)
python tester.py -n 10

# Non‑interactive, JSON summary, log raw JSON to file
python tester.py -p openai -m gpt-4o -n 50 -j -o json -l run.log
```

## 10 — Future Ideas (out of scope now)

* Add concurrency & progress bar
* Retry/backoff switches
* P95 latency graph via Rich‑plot

# Prompt‑Plan for Agentic Coding Tool

## High‑Level Goal

Generate **tester.py**—a Python 3.10 CLI that implements the full behaviour described in *spec.md*.

---

## Steps for the Agent

1. **Read `spec.md` thoroughly** and parse sections 2‑9 for requirements.
2. **Create `tester.py`** in the project root.
3. **Import dependencies**:

   ```python
   import json, os, random, time, statistics
   from typing import List
   import typer, questionary
   from rich.console import Console
   from rich.table import Table
   from rich import box
   # provider SDKs
   from openai import OpenAI, AzureOpenAI
   import anthropic, boto3, google.generativeai as genai
   ```
4. **Define CLI with Typer**:

   * Flags exactly as in §4 of *spec.md*.
   * Auto‑complete provider names from `models.json`.
5. **Interactive Menus (Questionary)**:

   * Provider menu first → model menu populated from chosen provider list.
   * When `--selection-mode` not given interactively, toggle via list.
6. **Load `models.json`** (path from arg or default). Verify model exists.
7. **Seed Data Loader**:

   * Build two iterators depending on selection mode.
   * For each sentence, return `(prompt, sentence)`.
8. **Provider Clients** (helper factory):

   * Map provider → client instance & `send_request()` closure using overrides in §6.
   * All requests pass `temperature=0` and single string `payload`.
9. **Metrics Recorder**:

   * Capture `status_code` (or "EXC"), `latency_ms`, `bytes`.
10. **Sequential Loop** from 1 to `num_requests`:

    * Compose payload.
    * Send; handle exceptions.
    * Optionally `json.dumps(resp)` to log.
11. **Summary Builder**:

    * Compute min/avg/median/p95/p99/max latency; success/error counts; total bytes.
    * Render Rich table **or** produce JSON/CSV per `--output-format`.
12. **Logging**:

    * Console always; file when `--log-file` given (append mode).
13. **Timeouts & Errors**:

    * `httpx.Timeout(timeout)` or SDK equivalent.
    * On connect failure to proxy: print error, `sys.exit(1)`.
14. **Exit Codes** per §5.
15. **Docstring & `if __name__ == "__main__": app()` entry.**

---

## Deliverables

* `tester.py` (≈ 300–400 LOC) compliant with *spec.md*.
* `models.json` initial content copied verbatim from spec §7.
* *No* extra files.

## Hints & Tips for the Agent

* Use **Typer’s** `typer.Option(envvar=…)` to map `--api-key` flag to env.
* Use **statistics.quantiles** with `n=100` to get p95/p99 after sorting latencies.
* For Rich table: `box.SIMPLE` plus `Console().print(table)`.
* Always open seed files with `encoding="utf‑8"`.
* Use `time.perf_counter()` for high‑res timings.
* Response size: `len(json.dumps(resp))` when JSON‑logging enabled, else `len(str(resp))`.
* Keep helper functions inside `tester.py`; no submodules.

---

### End of Prompt‑Plan

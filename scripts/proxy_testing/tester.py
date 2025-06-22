#!/usr/bin/env python3
"""
LLM Proxy Load-Test Script

A single-file Python CLI that fires controllable requests at an LLM-proxy server
which mimics six major providers. Reads natural-language seed data, assembles 
requests, measures latency, and prints/saves summary tables.
"""

import json
import os
import random
import sys
import time
import statistics
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Iterator

import typer
import questionary
from rich.console import Console
from rich.table import Table
from rich import box
import requests

# Provider SDKs
from openai import OpenAI, AzureOpenAI
import anthropic
import boto3

# Optional import for Google GenAI
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    genai = None

app = typer.Typer(help="LLM Proxy Load-Test Script")
console = Console()


class MetricsRecorder:
    """Records and computes metrics for requests."""
    
    def __init__(self):
        self.results = []
        self.success_count = 0
        self.failure_count = 0
        self.total_bytes = 0
    
    def record(self, status_code: str, latency_ms: float, response_bytes: int):
        """Record a single request result."""
        self.results.append({
            'status_code': status_code,
            'latency_ms': latency_ms,
            'bytes': response_bytes
        })
        
        # Consider 2xx and 3xx as success, 4xx, 5xx, and EXC as failures
        if status_code == "EXC":
            self.failure_count += 1
        elif isinstance(status_code, str) and status_code.isdigit():
            status_int = int(status_code)
            if 200 <= status_int < 400:
                self.success_count += 1
            else:
                self.failure_count += 1
        else:
            # Non-numeric status codes (other than EXC) treated as success for backwards compatibility
            self.success_count += 1
        
        self.total_bytes += response_bytes
    
    def get_summary(self) -> Dict[str, Any]:
        """Compute summary statistics."""
        if not self.results:
            return {
                'total_requests': 0,
                'success_count': 0,
                'failure_count': 0,
                'total_bytes': 0,
                'latency_stats': {}
            }
        
        # Only include successful requests (2xx/3xx) in latency statistics
        def is_successful_status(status_code):
            if status_code == "EXC":
                return False
            if isinstance(status_code, str) and status_code.isdigit():
                status_int = int(status_code)
                return 200 <= status_int < 400
            return True  # Non-numeric status codes treated as success for backwards compatibility
        
        latencies = [r['latency_ms'] for r in self.results if is_successful_status(r['status_code'])]
        
        if latencies:
            latencies.sort()
            stats = {
                'min_ms': min(latencies),
                'avg_ms': statistics.mean(latencies),
                'median_ms': statistics.median(latencies),
                'max_ms': max(latencies)
            }
            
            # Calculate percentiles
            if len(latencies) >= 20:  # Need enough data points for percentiles
                quantiles = statistics.quantiles(latencies, n=100)
                stats['p95_ms'] = quantiles[94]  # 95th percentile (0-indexed)
                stats['p99_ms'] = quantiles[98]  # 99th percentile
            else:
                stats['p95_ms'] = stats['max_ms']
                stats['p99_ms'] = stats['max_ms']
        else:
            stats = {
                'min_ms': 0,
                'avg_ms': 0,
                'median_ms': 0,
                'p95_ms': 0,
                'p99_ms': 0,
                'max_ms': 0
            }
        
        return {
            'total_requests': len(self.results),
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'total_bytes': self.total_bytes,
            'latency_stats': stats
        }


class SeedDataLoader:
    """Loads and manages seed data from unstructured data files."""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.files = list(self.data_dir.glob("*.txt"))
        
        if not self.files:
            console.print(f"[red]No .txt files found in {data_dir}[/red]")
            sys.exit(1)
    
    def _parse_file(self, file_path: Path) -> Tuple[str, List[str]]:
        """Parse a seed data file and return (prompt, sentences)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split on the delimiter
            parts = content.split('---', 1)
            if len(parts) != 2:
                console.print(f"[yellow]Warning: {file_path.name} missing '---' delimiter[/yellow]")
                return "", []
            
            # Extract prompt (remove ### Prompt header)
            prompt_section = parts[0].strip()
            if prompt_section.startswith('### Prompt'):
                prompt = prompt_section[len('### Prompt'):].strip()
            else:
                prompt = prompt_section
            
            # Extract sentences (split by double newlines)
            sentences_section = parts[1].strip()
            sentences = [s.strip() for s in sentences_section.split('\n\n') if s.strip()]
            
            return prompt, sentences
            
        except Exception as e:
            console.print(f"[red]Error parsing {file_path.name}: {e}[/red]")
            return "", []
    
    def get_iterator(self, selection_mode: str) -> Iterator[Tuple[str, str]]:
        """Get an iterator that yields (prompt, sentence) pairs."""
        if selection_mode == "single-file":
            # Pick one random file and use it for all requests
            chosen_file = random.choice(self.files)
            prompt, sentences = self._parse_file(chosen_file)
            
            if not sentences:
                console.print(f"[red]No sentences found in {chosen_file.name}[/red]")
                sys.exit(1)
            
            while True:
                yield prompt, random.choice(sentences)
        
        elif selection_mode == "all-files":
            # Parse all files upfront
            file_data = {}
            for file_path in self.files:
                prompt, sentences = self._parse_file(file_path)
                if sentences:
                    file_data[file_path] = (prompt, sentences)
            
            if not file_data:
                console.print("[red]No valid files with sentences found[/red]")
                sys.exit(1)
            
            while True:
                chosen_file = random.choice(list(file_data.keys()))
                prompt, sentences = file_data[chosen_file]
                yield prompt, random.choice(sentences)
        
        else:
            raise ValueError(f"Invalid selection mode: {selection_mode}")
    
    def generate_unique_data(self, selection_mode: str, num_requests: int) -> List[Tuple[str, str]]:
        """Generate data for requests with maximum sentence uniqueness."""
        if selection_mode == "single-file":
            # Pick one random file and maximize sentence uniqueness within it
            chosen_file = random.choice(self.files)
            prompt, sentences = self._parse_file(chosen_file)
            
            if not sentences:
                console.print(f"[red]No sentences found in {chosen_file.name}[/red]")
                sys.exit(1)
            
            console.print(f"[cyan]Using file: {chosen_file.name} ({len(sentences)} unique sentences available)[/cyan]")
            
            # Create list of all available (prompt, sentence) pairs
            available_pairs = [(prompt, sentence) for sentence in sentences]
            
            # Generate data with maximum uniqueness
            result = []
            used_sentences = set()
            
            for i in range(num_requests):
                # First, try to get unused sentences
                unused_pairs = [pair for pair in available_pairs if pair[1] not in used_sentences]
                
                if unused_pairs:
                    # Pick randomly from unused sentences
                    chosen_pair = random.choice(unused_pairs)
                    used_sentences.add(chosen_pair[1])
                    result.append(chosen_pair)
                else:
                    # All sentences used, pick randomly from all (but track for stats)
                    chosen_pair = random.choice(available_pairs)
                    result.append(chosen_pair)
            
            unique_count = len(used_sentences)
            repeat_count = num_requests - unique_count
            
            if repeat_count > 0:
                console.print(f"[yellow]Used {unique_count} unique sentences, {repeat_count} repeated sentences[/yellow]")
            else:
                console.print(f"[green]All {unique_count} sentences are unique![/green]")
            
            return result
        
        elif selection_mode == "all-files":
            # Parse all files and maximize uniqueness across all files
            file_data = {}
            total_sentences = 0
            
            for file_path in self.files:
                prompt, sentences = self._parse_file(file_path)
                if sentences:
                    file_data[file_path] = (prompt, sentences)
                    total_sentences += len(sentences)
            
            if not file_data:
                console.print("[red]No valid files with sentences found[/red]")
                sys.exit(1)
            
            console.print(f"[cyan]Using {len(file_data)} files ({total_sentences} unique sentences available)[/cyan]")
            
            # Create list of all available (prompt, sentence) pairs from all files
            available_pairs = []
            for file_path, (prompt, sentences) in file_data.items():
                for sentence in sentences:
                    available_pairs.append((prompt, sentence))
            
            # Generate data with maximum uniqueness
            result = []
            used_sentences = set()
            
            for i in range(num_requests):
                # First, try to get unused sentences
                unused_pairs = [pair for pair in available_pairs if pair[1] not in used_sentences]
                
                if unused_pairs:
                    # Pick randomly from unused sentences
                    chosen_pair = random.choice(unused_pairs)
                    used_sentences.add(chosen_pair[1])
                    result.append(chosen_pair)
                else:
                    # All sentences used, pick randomly from all
                    chosen_pair = random.choice(available_pairs)
                    result.append(chosen_pair)
            
            unique_count = len(used_sentences)
            repeat_count = num_requests - unique_count
            
            if repeat_count > 0:
                console.print(f"[yellow]Used {unique_count} unique sentences, {repeat_count} repeated sentences[/yellow]")
            else:
                console.print(f"[green]All {unique_count} sentences are unique![/green]")
            
            return result
        
        else:
            raise ValueError(f"Invalid selection mode: {selection_mode}")


class ProviderClient:
    """Factory for creating provider-specific clients."""
    
    @staticmethod
    def create_client(provider: str, model: str, api_key: str, proxy_url: Optional[str], timeout: int):
        """Create a provider-specific client."""
        
        if provider == "openai":
            # Connect directly to OpenAI if no proxy URL specified
            if proxy_url is None:
                client = OpenAI(
                    api_key=api_key,
                    timeout=timeout
                )
            else:
                client = OpenAI(
                    api_key=api_key,
                    base_url=f"{proxy_url}/v1",
                    timeout=timeout
                )
            
            def send_request(payload: str) -> Tuple[str, Any]:
                try:
                    # Use chat completions for modern models, completions for legacy models
                    if model in ["gpt-3.5-turbo-instruct"]:
                        resp = client.completions.create(
                            model=model,
                            prompt=payload,
                            temperature=0,
                            max_tokens=1000
                        )
                    else:
                        resp = client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": payload}],
                            temperature=0,
                            max_tokens=1000
                        )
                    return "200", resp
                except Exception as e:
                    return "EXC", str(e)
            
            return send_request
        
        elif provider == "anthropic":
            # Connect directly to Anthropic if no proxy URL specified
            if proxy_url is None:
                client = anthropic.Anthropic(api_key=api_key)
            else:
                client = anthropic.Anthropic(
                    api_key=api_key,
                    base_url=proxy_url
                )
            
            def send_request(payload: str) -> Tuple[str, Any]:
                try:
                    resp = client.messages.create(
                        model=model,
                        messages=[{"role": "user", "content": payload}],
                        temperature=0,
                        max_tokens=1000
                    )
                    return "200", resp
                except Exception as e:
                    return "EXC", str(e)
            
            return send_request
        
        elif provider == "azure-openai":
            if proxy_url is None:
                raise ValueError("Azure OpenAI requires --proxy-url to specify the Azure endpoint")
            
            client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=proxy_url,
                api_version="2024-02-01-preview",
                timeout=timeout
            )
            
            def send_request(payload: str) -> Tuple[str, Any]:
                try:
                    # Use chat completions for modern models, completions for legacy models
                    if model in ["gpt-35-turbo-instruct"]:
                        resp = client.completions.create(
                            model=model,
                            prompt=payload,
                            temperature=0,
                            max_tokens=1000
                        )
                    else:
                        resp = client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": payload}],
                            temperature=0,
                            max_tokens=1000
                        )
                    return "200", resp
                except Exception as e:
                    return "EXC", str(e)
            
            return send_request
        
        elif provider == "aws-bedrock":
            # Connect directly to AWS Bedrock if no proxy URL specified
            if proxy_url is None:
                client = boto3.client('bedrock-runtime', region_name='us-east-1')
                
                def send_request(payload: str) -> Tuple[str, Any]:
                    try:
                        # Prepare request body based on model type
                        if model.startswith("amazon.nova"):
                            # Nova models use messages format with schemaVersion
                            body = {
                                "schemaVersion": "messages-v1",
                                "messages": [{"role": "user", "content": [{"text": payload}]}],
                                "inferenceConfig": {
                                    "temperature": 0,
                                    "maxTokens": 1000
                                }
                            }
                        else:
                            # Other models use prompt format
                            body = {
                                "prompt": payload,
                                "temperature": 0,
                                "max_tokens_to_sample": 1000
                            }
                        
                        resp = client.invoke_model(
                            modelId=model,
                            body=json.dumps(body)
                        )
                        return "200", resp
                    except Exception as e:
                        return "EXC", str(e)
            else:
                # Use custom headers approach for proxy connections
                # Get AWS credentials from environment
                aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
                aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                aws_session_token = os.getenv('AWS_SESSION_TOKEN')
                
                if not aws_access_key or not aws_secret_key:
                    raise ValueError("AWS credentials required: set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
                
                def send_request(payload: str) -> Tuple[str, Any]:
                    try:
                        # Prepare headers with AWS credentials
                        headers = {
                            "Content-Type": "application/json",
                            "X-AWS-Access-Key": aws_access_key,
                            "X-AWS-Secret-Key": aws_secret_key
                        }
                        
                        # Add session token if available (for STS credentials)
                        if aws_session_token:
                            headers["X-AWS-Session-Token"] = aws_session_token
                        
                        # Prepare request body based on model type
                        if model.startswith("amazon.nova"):
                            # Nova models use messages format with schemaVersion
                            body = {
                                "schemaVersion": "messages-v1",
                                "messages": [{"role": "user", "content": [{"text": payload}]}],
                                "inferenceConfig": {
                                    "temperature": 0,
                                    "maxTokens": 1000
                                }
                            }
                        else:
                            # Other models use prompt format
                            body = {
                                "prompt": payload,
                                "temperature": 0,
                                "max_tokens_to_sample": 1000
                            }
                        
                        # Make request to proxy with custom headers
                        endpoint = f"/model/{model}/invoke"
                        url = f"{proxy_url.rstrip('/')}{endpoint}"
                        
                        response = requests.post(
                            url,
                            json=body,
                            headers=headers,
                            timeout=timeout
                        )
                        
                        # Return status and response
                        if response.status_code == 200:
                            return "200", response.json()
                        else:
                            return str(response.status_code), response.text
                            
                    except Exception as e:
                        return "EXC", str(e)
            
            return send_request
        
        elif provider == "vertex-ai":
            if not HAS_GENAI:
                raise ValueError("google-generativeai package not installed. Install with: pip install google-generativeai")
            
            # Connect directly to Google AI if no proxy URL specified
            if proxy_url is None:
                genai.configure(api_key=api_key)
            else:
                genai.configure(
                    api_key=api_key,
                    api_endpoint=proxy_url
                )
            
            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config={"temperature": 0}
            )
            
            def send_request(payload: str) -> Tuple[str, Any]:
                try:
                    resp = model_instance.generate_content(payload)
                    return "200", resp
                except Exception as e:
                    return "EXC", str(e)
            
            return send_request
        
        elif provider == "deepseek":
            # Connect directly to Deepseek if no proxy URL specified
            if proxy_url is None:
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com",
                    timeout=timeout
                )
            else:
                client = OpenAI(
                    api_key=api_key,
                    base_url=proxy_url,
                    timeout=timeout
                )
            
            def send_request(payload: str) -> Tuple[str, Any]:
                try:
                    resp = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": payload}],
                        temperature=0,
                        max_tokens=1000
                    )
                    return "200", resp
                except Exception as e:
                    return "EXC", str(e)
            
            return send_request
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")


def load_models(models_file: str) -> Dict[str, List[str]]:
    """Load the models.json configuration."""
    try:
        with open(models_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading {models_file}: {e}[/red]")
        sys.exit(1)


def get_api_key(provider: str, provided_key: Optional[str]) -> str:
    """Get API key from CLI arg or environment."""
    if provided_key:
        return provided_key
    
    env_vars = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "azure-openai": "AZURE_OPENAI_API_KEY",
        "aws-bedrock": "AWS_ACCESS_KEY_ID",  # AWS uses different auth
        "vertex-ai": "GOOGLE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY"
    }
    
    env_var = env_vars.get(provider)
    if env_var:
        key = os.getenv(env_var)
        if key:
            return key
    
    if provider == "aws-bedrock":
        # For AWS, we'll use default credentials
        return "dummy"
    
    console.print(f"[red]No API key found for {provider}. Set {env_var} or use --api-key[/red]")
    sys.exit(1)


def send_single_request(
    request_id: int,
    client_func,
    payload: str,
    json_response: bool,
    log_file_handle=None,
    lock=None
) -> Tuple[int, str, float, int, Optional[str]]:
    """Send a single request and return the results with optional error message."""
    try:
        
        # Send request with timing
        start_time = time.perf_counter()
        status_code, response = client_func(payload)
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000
        
        # Calculate response size
        if status_code != "EXC":
            if json_response:
                response_bytes = len(json.dumps(str(response)))
            else:
                response_bytes = len(str(response))
        else:
            response_bytes = len(str(response))
        
        # Log raw JSON if requested (with thread safety)
        if json_response and log_file_handle and lock:
            log_entry = {
                "request_id": request_id,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "response": str(response) if status_code != "EXC" else None,
                "error": str(response) if status_code == "EXC" else None
            }
            with lock:
                log_file_handle.write(json.dumps(log_entry) + "\n")
                log_file_handle.flush()
        
        # Return with error message for EXC and HTTP error codes (4xx, 5xx)
        if status_code == "EXC":
            error_msg = str(response)
        elif isinstance(status_code, str) and status_code.isdigit():
            status_int = int(status_code)
            if status_int >= 400:  # 4xx and 5xx errors
                error_msg = str(response)
            else:
                error_msg = None
        else:
            error_msg = None
        return request_id, status_code, latency_ms, response_bytes, error_msg
        
    except Exception as e:
        # Handle any exceptions in the request
        return request_id, "EXC", 0.0, len(str(e)), str(e)


def render_summary(summary: Dict[str, Any], output_format: str) -> str:
    """Render summary in the specified format."""
    if output_format == "json":
        return json.dumps(summary, indent=2)
    
    elif output_format == "csv":
        stats = summary['latency_stats']
        return (
            "total_requests,success_count,failure_count,total_bytes,"
            "min_ms,avg_ms,median_ms,p95_ms,p99_ms,max_ms\n"
            f"{summary['total_requests']},{summary['success_count']},"
            f"{summary['failure_count']},{summary['total_bytes']},"
            f"{stats['min_ms']:.2f},{stats['avg_ms']:.2f},"
            f"{stats['median_ms']:.2f},{stats['p95_ms']:.2f},"
            f"{stats['p99_ms']:.2f},{stats['max_ms']:.2f}"
        )
    
    else:  # table format
        table = Table(title="Load Test Summary", box=box.SIMPLE)
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Requests", str(summary['total_requests']))
        table.add_row("Successful", str(summary['success_count']))
        table.add_row("Failed", str(summary['failure_count']))
        table.add_row("Total Bytes", f"{summary['total_bytes']:,}")
        
        stats = summary['latency_stats']
        table.add_row("Min Latency", f"{stats['min_ms']:.2f} ms")
        table.add_row("Avg Latency", f"{stats['avg_ms']:.2f} ms")
        table.add_row("Median Latency", f"{stats['median_ms']:.2f} ms")
        table.add_row("95th Percentile", f"{stats['p95_ms']:.2f} ms")
        table.add_row("99th Percentile", f"{stats['p99_ms']:.2f} ms")
        table.add_row("Max Latency", f"{stats['max_ms']:.2f} ms")
        
        return table


@app.command()
def main(
    provider: Optional[str] = typer.Option(None, "-p", "--provider", help="LLM provider"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model name"),
    num_requests: Optional[int] = typer.Option(None, "-n", "--num-requests", help="Number of requests"),
    concurrency: Optional[int] = typer.Option(None, "-c", "--concurrency", help="Number of concurrent requests"),
    data_dir: str = typer.Option("./unstructured_data", "-d", "--data-dir", help="Seed data directory"),
    selection_mode: str = typer.Option("single-file", "-s", "--selection-mode", help="single-file or all-files"),
    log_file: Optional[str] = typer.Option(None, "-l", "--log-file", help="Log file path"),
    json_response: bool = typer.Option(False, "-j", "--json-response", help="Log raw JSON responses"),
    output_format: str = typer.Option("table", "-o", "--output-format", help="table, json, or csv"),
    interactive: Optional[bool] = typer.Option(None, "-i", "--interactive/--no-interactive", help="Interactive mode"),
    api_key: Optional[str] = typer.Option(None, "-k", "--api-key", help="API key"),
    proxy_url: Optional[str] = typer.Option(None, "-u", "--proxy-url", help="Proxy URL (if not specified, connects directly to provider)"),
    timeout: int = typer.Option(30, "-t", "--timeout", help="Request timeout in seconds"),
    models_file: str = typer.Option("./models.json", "--models-file", help="Models configuration file")
):
    """LLM Proxy Load-Test Script
    
    By default, connects directly to provider APIs. 
    Use --proxy-url to test through a proxy server."""
    
    # Determine if we're in interactive mode
    if interactive is None:
        interactive = sys.stdout.isatty()
    
    # Load models configuration
    models_config = load_models(models_file)
    
    # Provider selection
    if not provider:
        if not interactive:
            console.print("[red]--provider required in non-interactive mode[/red]")
            sys.exit(2)
        
        provider = questionary.select(
            "Select provider:",
            choices=list(models_config.keys())
        ).ask()
    
    if provider not in models_config:
        console.print(f"[red]Unknown provider: {provider}[/red]")
        sys.exit(1)
    
    # Model selection
    if not model:
        if not interactive:
            console.print("[red]--model required in non-interactive mode[/red]")
            sys.exit(2)
        
        model = questionary.select(
            f"Select model for {provider}:",
            choices=models_config[provider]
        ).ask()
    
    if model not in models_config[provider]:
        console.print(f"[red]Model {model} not available for {provider}[/red]")
        sys.exit(1)
    
    # Number of requests selection (interactive only)
    if interactive and num_requests is None:
        num_requests_choice = questionary.select(
            "Number of requests to send:",
            choices=["1", "5", "10", "25", "50", "100"]
        ).ask()
        if num_requests_choice:
            num_requests = int(num_requests_choice)
    
    # Set default if still None
    if num_requests is None:
        num_requests = 1
    
    # Concurrency selection (interactive only)
    if interactive and concurrency is None:
        concurrency_choice = questionary.select(
            "Number of concurrent requests:",
            choices=["1", "5", "10"]
        ).ask()
        if concurrency_choice:
            concurrency = int(concurrency_choice)
    
    # Set default if still None
    if concurrency is None:
        concurrency = 1
    
    # Selection mode (interactive only - ask if not already specified)
    if interactive and selection_mode == "single-file":
        mode_choice = questionary.select(
            "Selection mode:",
            choices=["single-file", "all-files"]
        ).ask()
        if mode_choice:
            selection_mode = mode_choice
    
    # Get API key
    api_key_resolved = get_api_key(provider, api_key)
    
    # Initialize components
    if proxy_url is None:
        console.print(f"[cyan]Starting load test: {provider}/{model} with {num_requests} requests, concurrency: {concurrency} (direct connection)[/cyan]")
    else:
        console.print(f"[cyan]Starting load test: {provider}/{model} with {num_requests} requests, concurrency: {concurrency} via proxy {proxy_url}[/cyan]")
    
    
    try:
        # Test proxy connectivity
        seed_loader = SeedDataLoader(data_dir)
        client_func = ProviderClient.create_client(provider, model, api_key_resolved, proxy_url, timeout)
        metrics = MetricsRecorder()
        
        # Open log file if specified
        log_file_handle = None
        if log_file:
            log_file_handle = open(log_file, 'a', encoding='utf-8')
        
        # Thread lock for log file writing
        lock = threading.Lock() if log_file_handle else None
        
        # Generate unique data pairs to maximize sentence diversity
        data_pairs = seed_loader.generate_unique_data(selection_mode, num_requests)
        
        # Pre-generate all payloads
        payloads = []
        for prompt, sentence in data_pairs:
            payload = f"{prompt}\n\n{sentence}"
            payloads.append(payload)
        
        # Concurrent request execution
        if concurrency == 1:
            # Sequential execution (no threading overhead)
            for i in range(num_requests):
                console.print(f"[blue]Request {i+1}/{num_requests}[/blue]", end="")
                
                request_id, status_code, latency_ms, response_bytes, error_msg = send_single_request(
                    i + 1, client_func, payloads[i], json_response, log_file_handle, lock
                )
                
                # Record metrics
                metrics.record(status_code, latency_ms, response_bytes)
                
                if error_msg:
                    console.print(f" - {status_code} ({latency_ms:.2f}ms) - [red]{error_msg}[/red]")
                else:
                    console.print(f" - {status_code} ({latency_ms:.2f}ms)")
        else:
            # Concurrent execution using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                # Submit all requests with pre-generated payloads
                future_to_id = {
                    executor.submit(
                        send_single_request, 
                        i + 1, 
                        client_func, 
                        payloads[i], 
                        json_response, 
                        log_file_handle, 
                        lock
                    ): i + 1 for i in range(num_requests)
                }
                
                # Process completed requests
                completed_count = 0
                for future in as_completed(future_to_id):
                    completed_count += 1
                    request_id = future_to_id[future]
                    
                    try:
                        req_id, status_code, latency_ms, response_bytes, error_msg = future.result()
                        
                        # Record metrics
                        metrics.record(status_code, latency_ms, response_bytes)
                        
                        if error_msg:
                            console.print(f"[blue]Request {completed_count}/{num_requests} (ID: {req_id})[/blue] - {status_code} ({latency_ms:.2f}ms) - [red]{error_msg}[/red]")
                        else:
                            console.print(f"[blue]Request {completed_count}/{num_requests} (ID: {req_id})[/blue] - {status_code} ({latency_ms:.2f}ms)")
                        
                    except Exception as e:
                        console.print(f"[red]Request {request_id} failed: {e}[/red]")
                        metrics.record("EXC", 0.0, len(str(e)))
        
        # Generate and display summary
        summary = metrics.get_summary()
        rendered_summary = render_summary(summary, output_format)
        
        if output_format == "table":
            console.print("\n")
            console.print(rendered_summary)
        else:
            print(rendered_summary)
        
        # Write summary to log file
        if log_file_handle:
            log_file_handle.write(f"\n=== SUMMARY ===\n")
            log_file_handle.write(render_summary(summary, "json"))
            log_file_handle.write(f"\n")
            log_file_handle.close()
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error connecting to proxy: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    app()
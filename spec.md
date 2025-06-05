# Rubberduck: Developer Specification

## Overview

Rubberduck is a local LLM caching reverse proxy server designed to emulate major LLM providers such as OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, and Google Vertex AI. It provides caching, failure simulation, rate limiting, per-user proxy instances, and detailed logging. Please note that Rubberduck's clients will use SDKs of various LLM providers to connect to it. Meaning, the emulation needs to be good enough for the various official LLM APIs.

## Architecture

* **Backend**: Python + FastAPI
* **Frontend**: React + Tailwind UI
* **Database**: SQLite
* **Authentication**: FastAPI Users (email/password + social login via Google/GitHub)
* **LLM Provider Modules**: Modular Python files in `providers/`, auto-registered
* **Proxy Binding**: One proxy per thread, bound to a unique host port

---

## Features

### Caching

* Only successful responses from upstream LLMs are cached
* Cache key: hash of the normalized (sorted JSON) request body
* Manual invalidation only, via UI, scoped to a single proxy instance
* Cache does not interfere with upstream provider's caching headers

### LLM Emulation

* Emulates real request/response behavior, including headers, status codes, and error formats
* Passes through Authorization headers with no validation
* All request parameters are client-controlled
* No prompt/response bodies are stored in logs

### Failure Simulation

* Configurable per proxy
* Types:

  * **Timeouts**: fixed delay or indefinite hang (user-defined)
  * **Error injection**: selectable error codes (e.g. 429, 500, 400), each with individual failure rate
  * **IP allow/block list**: exact IPs, CIDR ranges, and wildcards
  * **Rate limiting**: requests per minute (RPM)
* Failures override request forwarding; failed responses are not cached

### Rate Limiting

* Configurable RPM per proxy instance
* On limit exceeded: proxy mimics upstream LLM behavior (usually HTTP 429)

### Authentication

* Login via email/password and social (Google/GitHub), controlled by env vars
* Email verification required
* Password reset supported
* No role-based permissions; all users manage their own proxies

### Proxy Lifecycle

* Auto-start proxy threads on app restart using DB state
* UI allows:

  * Start/Stop
  * Graceful stop (waits for in-flight requests to finish)
  * Force stop
* Ports:

  * Auto-assigned and stored
  * User-editable
  * Startup failure (e.g. port conflict) shown in UI

### UI Structure

Beautiful, sleek and modern, Stripe-like UI.

* Pages:

  * Dashboard (live system stats)
  * Proxies (manage per-user proxy instances)
  * Logs (streaming + filtering)
  * Users (optional future extension)
  * Settings (global config)

---

## Logging

* Logs request metadata:

  * Timestamp
  * Proxy ID
  * IP address
  * Prompt hash
  * Status code
  * Latency
  * Cache hit/miss
  * Simulated failure type (if any)
  * Token usage and cost (if available)
* Logs are viewable in UI (live stream + filters)
* Exportable (CSV/JSON)
* Purgeable by date range

### Metrics

* Persisted roll-ups (e.g. 1-min/15-min hourly):

  * Total RPM
  * Cache hit rate
  * Error rate
  * Cost (if available)
  * Running/stopped proxy count
  * In-flight request count

---

## Proxy Configuration

* Required fields: name, provider, model name (display only)
* Optional fields: port number (auto-assigned if not provided)
* Optional: description, tags
* No advanced model configs; all details expected to be in incoming requests

## Data Handling

* Request/response bodies never stored
* API keys never stored or shown in UI
* Only logs and metrics retained

---

## Error Handling

* Upstream LLM errors are transparently forwarded
* Simulated failures override request
* Port binding conflicts shown in UI
* Email verification and reset via SendGrid (configurable)

---

## Health Monitoring

* `/healthz` endpoint returns:

  * Status 200 OK
  * JSON payload: app version, DB status, running proxy count

---

## Testing Plan

### Unit Tests

* Caching logic and key normalization
* LLM provider forwarding and response wrapping
* Failure simulation paths (timeouts, errors, rate limits)
* Port conflict detection and assignment

### Integration Tests

* Start proxy, issue valid and invalid requests
* Verify cache hit/miss behavior
* Simulate errors and confirm response integrity
* Authentication flows (signup, login, password reset)
* Log ingestion and export

### UI Tests

* Proxy lifecycle controls (start/stop/force stop)
* Cache invalidation buttons
* Log stream filters
* Form validations (signup, proxy creation)

---

## Future Considerations

* Role-based access
* Proxy archiving
* Global search
* Cloning proxy instances
* Dynamic plugin loading

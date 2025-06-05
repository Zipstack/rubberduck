### Project Blueprint Breakdown  
**Backend-First Approach:** Build core infrastructure → proxy logic → UI integration → testing.
**TDD:** Always test thoroughly before moving on to the next step.

#### Chunk 1: Backend Foundation  
1. **FastAPI Setup & Health Endpoint**
   - Install dependencies
   - Create `/healthz` endpoint
   - Add version/DB status checks

2. **SQLite Database Setup**
   - Define SQLAlchemy models: `User`, `Proxy`, `LogEntry`, `Metrics`
   - Schema migrations (Alembic)

3. **Authentication**
   - FastAPI Users integration
   - Email/password + Social auth options
   - Email verification flow

---

#### Chunk 2: Core Proxy Functionality  
1. **LLM Provider Module System**  
   - Base provider interface  
   - OpenAI emulation module  
   - Dynamic plugin loader  

2. **Reverse Proxy Engine**  
   - Request forwarding with auth passthrough  
   - Response normalization  
   - Port binding per proxy instance  

3. **Caching System**  
   - SHA-256 cache keys (normalized JSON)  
   - SQLite cache storage  
   - Invalidation endpoints  

---

#### Chunk 3: Failure Simulation  
1. **Error Injection Framework**  
   - HTTP error code simulator (429/500/400)  
   - Per-proxy failure rate configuration  

2. **IP Filtering**  
   - CIDR/wildcard allow/block lists  
   - Pre-request validation hooks  

3. **Timeout Mechanisms**  
   - Configurable delay/hang simulation  
   - Async request timeout handling  

---

#### Chunk 4: Monitoring & UI  
1. **Logging Pipeline**  
   - Request metadata capture  
   - Streaming log endpoint  
   - CSV/JSON exporters  

2. **Metrics System**  
   - Rolling aggregates (1m/15m/1h)  
   - Cost calculation hooks  

3. **React UI Framework**  
   - Tailwind UI component setup  
   - Proxy dashboard skeleton  

---

#### Chunk 5: Testing & Security  
1. **Test Harness**  
   - Provider module unit tests  
   - Cache integrity tests  
   - Failure simulation scenarios  

2. **Security Hardening**  
   - API key passthrough validation  
   - Request body sanitization  
   - Rate limit stress tests  

---

### Iterative Implementation Prompts  
Each prompt:  
1. Builds on previous work  
2. Includes test instructions  
3. Specifies integration points  

---

### Prompt Series  
```text
**Prompt 1: FastAPI Foundation** ✅ DONE  
Create project scaffold:  
1. Install FastAPI/uvicorn/sqlalchemy ✅ 
2. Generate `main.py` with: ✅ 
   - `/healthz` endpoint returning 200  
   - Placeholder JSON: `{"status": "ok", "version": "0.1.0"}`  
3. Write pytest: ✅ 
   - Verify 200 response  
   - Check JSON structure  
4. Create `docker-compose.yml` with Python image ✅  
```  

```text
**Prompt 2: SQLite ORM Models** ✅ DONE  
Define SQLAlchemy models:  
1. `User` table (id, email, hashed_password, is_verified) ✅  
2. `Proxy` table (id, name, port, status, user_id FK) ✅  
3. `LogEntry` table (timestamp, proxy_id, status_code, latency) ✅  
4. Initialize Alembic migrations ✅  
5. Write tests: ✅  
   - Model creation/retrieval  
   - Foreign key constraints  
```  

```text
**Prompt 3: Authentication Core** ✅ DONE  
Integrate FastAPI-Users:  
1. Configure SQLiteUserDatabase ✅  
2. Implement: ✅  
   - `/auth/register` (email+password)  
   - `/auth/jwt/login`  
3. Add social logins stubs (Google/GitHub) ✅  
4. Test: ✅  
   - User registration flow  
   - JWT token issuance  
   - Protected endpoint access  
```  

```text
**Prompt 4: Provider Module System** ✅ DONE  
Create provider interface:  
1. `providers/base.py` with abstract methods: ✅  
   - `normalize_request()`  
   - `forward_request()`  
2. `providers/openai.py` implementing: ✅  
   - Request/response translation  
   - Error format emulation  
3. Auto-registry via `__init__.py`: ✅  
   - Scan `providers/*.py`  
   - Expose `PROVIDERS = {"openai": OpenAIModule}`  
4. Tests: ✅  
   - Module registration  
   - Request normalization  
```  

```text
**Prompt 5: Proxy Engine** ✅ DONE  
Build request forwarder:  
1. Endpoint `POST /v1/chat/completions` that: ✅  
   - Identifies provider from path  
   - Passes Authorization header untouched  
   - Calls `PROVIDERS[provider].forward_request()`  
2. Port binding manager: ✅  
   - Assign unique port per proxy  
   - Store in `Proxy` table  
3. Tests: ✅  
   - Request passthrough to mock provider  
   - Port conflict handling  
```  

```text
**Prompt 6: Caching System** ✅ DONE  
Implement response cache:  
1. Pre-request hook: ✅  
   - Generate SHA-256 key (sorted JSON body)  
   - Check `cache_db` for hit  
2. Post-response hook: ✅  
   - Store 2xx responses  
3. Invalidation endpoint: ✅  
   - `DELETE /cache/{proxy_id}`  
4. Tests: ✅  
   - Cache hit/miss behavior  
   - Storage exclusion of non-2xx  
   - Manual invalidation  
```  

```text
**Prompt 7: Failure Injection** ✅ DONE  
Add error simulation:  
1. Middleware for: ✅  
   - Timeouts (asyncio.sleep)  
   - Error codes (raise HTTPException)  
2. Config struct: ✅  
   `{ "timeout_sec": 5, "error_rates": {"429": 0.1} }`  
3. IP filtering: ✅  
   - Pre-execution CIDR check  
4. Tests: ✅  
   - Timeout measurement  
   - Error rate sampling  
   - IP blocklist enforcement  
```  

```text
**Prompt 8: Logging Pipeline** ✅ DONE  
Create audit system:  
1. Logging middleware capturing: ✅  
   - Timestamp, proxy_id, IP  
   - Status code, latency, cache_status  
2. `LogEntry` ORM integration ✅  
3. CSV export endpoint: ✅  
   - `GET /logs?export=csv`  
4. Tests: ✅  
   - Log entry creation  
   - Field validation  
   - Export format integrity  
```  

```text
**Prompt 9: UI Dashboard**  
Build React foundation:  
1. Vite+React+Tailwind UI setup  
2. Dashboard page showing:  
   - Running/stopped proxies count  
   - Cache hit rate card  
3. Proxy management stub:  
   - "Create Proxy" button  
4. Tests:  
   - Component rendering  
   - Mock API data display  
```  

```text
**Prompt 10: End-to-End Wiring**  
Integrate subsystems:  
1. Connect UI to `/proxies` endpoint  
2. Add proxy start/stop handlers:  
   - Update `Proxy.status`  
   - Bind/close ports  
3. Log streaming to UI console  
4. Test:  
   - Full proxy lifecycle  
   - Real-time log updates  
   - Cache interaction from UI  
```  

---

### Verification Checklist  
- [ ] Each prompt builds on previous artifacts  
- [ ] All code paths covered by tests  
- [ ] No orphaned components  
- [ ] Integration points explicitly defined  
- [ ] Security checks at subsystem boundaries  

**Next Steps:**  
1. Execute prompts sequentially  
2. Validate test coverage after each step  
3. Measure step completion time (target: <2hrs/step)  
4. Adjust granularity based on implementation friction
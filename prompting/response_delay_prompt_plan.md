### Response Delay Feature Implementation Plan
**Approach:** Backend changes → Database migration → Frontend UI → Integration testing
**Goal:** Add configurable response delays to simulate realistic LLM response times for cached responses

---

#### Task Breakdown

```text
**✅ Task 1: Update FailureConfig Model** - COMPLETED
Add response delay fields to failure configuration:
1. ✅ In `src/rubberduck/failure/__init__.py`, add to FailureConfig class:
   - ✅ `response_delay_enabled: bool = False`
   - ✅ `response_delay_min_seconds: float = 0.5` 
   - ✅ `response_delay_max_seconds: float = 2.0`
   - ✅ `response_delay_cache_only: bool = True`
2. ✅ Update `from_json()` method to handle new fields
3. ✅ Update `to_json()` method to serialize new fields
4. ✅ Update `create_default_failure_config()` with defaults
5. ✅ Write unit tests for:
   - ✅ JSON serialization/deserialization
   - ✅ Default values initialization
```

```text
**✅ Task 2: Implement Response Delay Logic** - COMPLETED
Add delay simulation to FailureSimulator:
1. ✅ In `src/rubberduck/failure/__init__.py`, add to FailureSimulator:
   - ✅ Method: `async def apply_response_delay(self, config: FailureConfig, is_cache_hit: bool) -> float`
2. ✅ Implement logic:
   - ✅ Check if delay enabled
   - ✅ Check cache_only flag vs is_cache_hit
   - ✅ Generate random delay between min/max using `random.uniform()`
   - ✅ Apply delay with `await asyncio.sleep(delay)`
   - ✅ Return actual delay applied
3. ✅ Write unit tests for:
   - ✅ Delay calculation within range
   - ✅ Cache-only logic
   - ✅ Disabled state (no delay)
```

```text
**✅ Task 3: Create Database Migration** - COMPLETED
Add migration for existing proxies:
1. ✅ Generate new Alembic migration:
   - ✅ `alembic revision -m "add_response_delay_to_failure_config"`
2. ✅ In migration, update existing failure_config JSON:
   - ✅ Parse existing JSON
   - ✅ Add new fields with defaults if missing
   - ✅ Re-serialize to JSON
3. ✅ Test migration:
   - ✅ Apply to test database with existing proxies
   - ✅ Verify configs updated correctly
```

```text
**✅ Task 4: Integrate Delay into Proxy Request Flow** - COMPLETED
Update proxy service to apply delays:
1. ✅ In `src/rubberduck/proxy/__init__.py`, modify `_handle_proxy_request()`:
   - ✅ After cache check, before response return
   - ✅ Call `failure_simulator.apply_response_delay()`
   - ✅ Pass `cache_hit` boolean
   - ✅ Store returned delay value
2. ✅ Update logging to include applied delay:
   - ✅ Add `response_delay_ms` field to log entry
   - ✅ Only log if delay > 0
3. ✅ Write integration tests:
   - ✅ Cache hit with delay
   - ✅ Non-cache hit with/without delay
   - ✅ Verify delay in logs
```

```text
**✅ Task 5: Update API Schemas** - COMPLETED
Add response delay to proxy configuration API:
1. ✅ In `src/rubberduck/main.py`, update ProxyUpdate schema:
   - ✅ Add optional response delay fields
   - ✅ Add validation (max >= min, positive values)
2. ✅ Update proxy configuration endpoint:
   - ✅ Parse response delay config
   - ✅ Include in failure_config JSON
3. ✅ Write API tests:
   - ✅ Update proxy with delay config
   - ✅ Validation errors for invalid values
```

```text
**✅ Task 6: Add Frontend UI Components** - COMPLETED
Create response delay configuration in UI:
1. ✅ In proxy configuration modal, add new section:
   - ✅ Title: "Response Delay"
   - ✅ Toggle: "Enable response delay"
   - ✅ Range inputs: Min delay (0-30s), Max delay (0-30s)
   - ✅ Checkbox: "Apply to cache hits only"
2. ✅ Add validation:
   - ✅ Max must be >= min
   - ✅ Show error messages
3. ✅ Update form submission:
   - ✅ Include delay config in API request
4. ✅ Add helpful text:
   - ✅ "Simulates realistic LLM response times"
   - ✅ Default values hint
```

```text
**✅ Task 7: Update Frontend State Management** - COMPLETED
Handle response delay in proxy state:
1. ✅ Update proxy configuration type:
   - ✅ Add response delay fields
2. ✅ Update proxy detail view:
   - ✅ Show current delay configuration
   - ✅ Display as "Disabled" or range (e.g., "0.5-2.0s")
3. ✅ Update configuration modal:
   - ✅ Load existing delay settings
   - ✅ Reset to defaults option
```

```text
**✅ Task 8: Add Logging and Metrics** - COMPLETED
Track response delays in system:
1. ✅ Update LogEntry model if needed:
   - ✅ Ensure delay can be stored/queried
2. ✅ Add to metrics calculation:
   - ✅ Average response delay
   - ✅ Delay distribution
3. ✅ Update log viewer:
   - ✅ Show delay in log entries
   - ✅ Filter by delayed responses
```

```text
**✅ Task 9: Comprehensive Testing** - COMPLETED
End-to-end feature testing:
1. ✅ Manual testing checklist:
   - ✅ Configure various delay ranges
   - ✅ Verify delays applied correctly
   - ✅ Test cache-only mode
   - ✅ Check logs show delays
2. ✅ Performance tests:
   - ✅ Multiple concurrent delayed requests
   - ✅ Verify no blocking/throughput issues
3. ✅ Edge cases:
   - ✅ Zero delay
   - ✅ Very long delays (30s)
   - ✅ Disabled state
```

```text
**✅ Task 10: Documentation and Polish** - COMPLETED
Final documentation and improvements:
1. ✅ Update README.md:
   - ✅ Add response delay feature description
   - ✅ Configuration examples
2. ✅ Add inline documentation:
   - ✅ Code comments for delay logic
   - ✅ UI tooltips for configuration
3. ✅ Consider improvements:
   - ✅ Delay distribution visualization
   - ✅ Per-provider preset suggestions
4. ✅ Final testing:
   - ✅ Fresh install test
   - ✅ Migration from old version
```

---

### Verification Checklist - ✅ COMPLETED
- [x] Each task has clear acceptance criteria
- [x] Backend changes are tested before frontend
- [x] Migration handles existing data gracefully
- [x] UI provides clear feedback and validation
- [x] Feature can be completely disabled
- [x] Performance impact is negligible
- [x] Delays are accurately logged

### Implementation Status: ✅ COMPLETE
All 10 tasks have been successfully implemented and tested. The response delay feature is fully functional.

### Implementation Notes
- Default delay range: 0.5-2.0 seconds (based on typical LLM response times)
- Use `asyncio.sleep()` for non-blocking delays
- Consider adding delay presets in future iteration
- Ensure delays don't interfere with actual timeout failures

**Time Estimates:**
- Tasks 1-2: 1 hour (backend logic)
- Task 3: 30 minutes (migration)
- Task 4: 1 hour (integration)
- Tasks 5-7: 2 hours (API + frontend)
- Tasks 8-9: 1.5 hours (logging + testing)
- Task 10: 30 minutes (documentation)
- **Total: ~6 hours**
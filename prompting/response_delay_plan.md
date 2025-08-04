# Response Delay Implementation Plan

## Overview
Add a configurable response delay feature to simulate realistic LLM response times when serving cached responses. This feature ensures that cache hits don't return instantaneously, which could reveal to clients that they're hitting a cache rather than the actual LLM.

## Goals
1. Add response delay configuration to the proxy failure configuration
2. Implement delay logic that applies only to cache hits
3. Allow configurable delay ranges (min/max) for realistic variation
4. Update UI to include response delay configuration options
5. Ensure delays are properly logged and don't interfere with other failure simulations

## Implementation Steps

### Step 1: Update FailureConfig Model
- Add response delay configuration fields to `FailureConfig` class in `src/rubberduck/failure/__init__.py`
- Fields to add:
  - `response_delay_enabled: bool = False`
  - `response_delay_min_seconds: float = 0.5` (minimum delay in seconds)
  - `response_delay_max_seconds: float = 2.0` (maximum delay in seconds)
  - `response_delay_cache_only: bool = True` (apply delay only to cache hits)
- Update `from_json()` and `to_json()` methods to handle new fields

### Step 2: Create Response Delay Logic
- Add method to `FailureSimulator` class: `async def apply_response_delay(self, config: FailureConfig, is_cache_hit: bool)`
- Logic:
  - Check if delay is enabled
  - If `response_delay_cache_only` is True, only apply delay for cache hits
  - Generate random delay between min and max seconds
  - Use `asyncio.sleep()` to implement the delay
  - Return the actual delay applied (for logging purposes)

### Step 3: Update Database Migration
- Create new Alembic migration to ensure existing proxies get default response delay config
- Migration should update any existing `failure_config` JSON to include new fields with defaults

### Step 4: Integrate Delay into Proxy Request Flow
- Update `ProxyService._handle_proxy_request()` in `src/rubberduck/proxy/__init__.py`
- After cache check but before returning response:
  - Call `failure_simulator.apply_response_delay()` 
  - Pass whether this is a cache hit
  - Log the applied delay in the request log

### Step 5: Update Frontend Configuration UI
- Add new section "Response Delay" to the proxy configuration modal
- Components to add:
  - Toggle: "Enable response delay"
  - Slider/Input: "Minimum delay (seconds)" - range 0-10s
  - Slider/Input: "Maximum delay (seconds)" - range 0-10s
  - Checkbox: "Apply to cache hits only" (default: checked)
- Validation: Ensure max >= min

### Step 6: Update API Endpoints
- Update `ProxyUpdate` schema in `src/rubberduck/main.py` to include response delay fields
- Ensure configuration is properly serialized/deserialized

### Step 7: Add Tests
- Unit tests for:
  - Response delay calculation logic
  - Delay application based on cache hit status
  - Configuration serialization/deserialization
- Integration tests for:
  - End-to-end proxy request with delay
  - Verifying delays are logged correctly
  - Ensuring delays don't interfere with other failure simulations

### Step 8: Update Documentation
- Add response delay feature to README
- Document configuration options
- Add examples of realistic delay ranges for different LLM providers

## Technical Considerations

1. **Performance**: Delays should use `asyncio.sleep()` to avoid blocking
2. **Accuracy**: Use `time.perf_counter()` for precise delay measurement
3. **Interaction with timeouts**: Response delays should not trigger client timeouts
4. **Metrics**: Include actual delay applied in log entries
5. **Default values**: Research typical LLM response times for realistic defaults

## UI/UX Considerations

1. **Preset options**: Provide preset delay ranges for common LLMs (GPT-4, Claude, etc.)
2. **Visual feedback**: Show estimated delay range in UI
3. **Warning**: Alert users if delay settings might cause client timeouts
4. **Live preview**: Show example delay distribution graph

## Testing Strategy

1. **Manual testing**:
   - Configure various delay ranges
   - Verify cache hits have appropriate delays
   - Ensure non-cache hits respect `cache_only` setting

2. **Automated testing**:
   - Measure actual delays vs configured ranges
   - Test edge cases (0 delay, very long delays)
   - Verify delay logging accuracy

3. **Performance testing**:
   - Ensure delays don't impact proxy throughput
   - Verify multiple concurrent requests handle delays correctly

## Success Criteria

1. Cache hits can be configured to have realistic response delays
2. Delays are configurable per proxy instance
3. Delays are properly logged for analysis
4. UI provides intuitive configuration options
5. Feature doesn't impact performance or introduce bugs
6. Documentation clearly explains the feature and use cases
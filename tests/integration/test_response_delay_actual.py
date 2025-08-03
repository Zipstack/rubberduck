import pytest
import time
import asyncio
from rubberduck.failure import FailureConfig, FailureSimulator


class TestResponseDelayActual:
    """Integration tests with actual delays to verify real behavior.
    
    These tests use real asyncio.sleep() calls to ensure the actual implementation works.
    They should be minimal and fast to avoid slowing down the test suite.
    """
    
    def setup_method(self):
        """Set up test fixtures."""
        self.simulator = FailureSimulator()
    
    @pytest.mark.asyncio
    async def test_actual_delay_applied(self):
        """Test that actual delays are applied correctly (integration test)."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.05,  # Very short delay for testing
            response_delay_max_seconds=0.05,  # Fixed delay for predictability
            response_delay_cache_only=True
        )
        
        start_time = time.perf_counter()
        delay = await self.simulator.apply_response_delay(config, is_cache_hit=True)
        end_time = time.perf_counter()
        actual_time = end_time - start_time
        
        # Verify actual delay was applied
        assert delay > 0.04  # Allow small tolerance
        assert delay < 0.08  # Allow some variance
        assert actual_time > 0.04  # Actual wall time should also reflect delay
        assert actual_time < 0.08
    
    @pytest.mark.asyncio
    async def test_no_delay_when_disabled(self):
        """Test that no actual delay occurs when disabled."""
        config = FailureConfig(
            response_delay_enabled=False,
            response_delay_min_seconds=1.0,  # Large value should be ignored
            response_delay_max_seconds=2.0,
            response_delay_cache_only=True
        )
        
        start_time = time.perf_counter()
        delay = await self.simulator.apply_response_delay(config, is_cache_hit=True)
        end_time = time.perf_counter()
        actual_time = end_time - start_time
        
        # Should return immediately
        assert delay == 0.0
        assert actual_time < 0.01  # Should be nearly instant
    
    @pytest.mark.asyncio
    async def test_concurrent_delays_non_blocking(self):
        """Test that concurrent delays don't block each other."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.05,
            response_delay_max_seconds=0.05,
            response_delay_cache_only=False
        )
        
        async def delayed_request():
            return await self.simulator.apply_response_delay(config, is_cache_hit=True)
        
        # Run 3 concurrent delayed requests
        start_time = time.perf_counter()
        delays = await asyncio.gather(
            delayed_request(),
            delayed_request(),
            delayed_request()
        )
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # All delays should be applied
        for delay in delays:
            assert 0.04 <= delay <= 0.08
        
        # Total time should be close to single delay (concurrent execution)
        # Not 3x the delay (which would indicate blocking behavior)
        assert total_time < 0.1  # Should be much less than 3 * 0.05 = 0.15


if __name__ == "__main__":
    pytest.main([__file__])
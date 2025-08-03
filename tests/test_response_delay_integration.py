import pytest
import time
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from rubberduck.failure import FailureConfig, FailureSimulator


class TestResponseDelayIntegration:
    """Test response delay integration with the failure simulator."""
    
    @pytest.fixture
    def simulator(self):
        """Create a FailureSimulator instance."""
        return FailureSimulator()
    
    @pytest.mark.asyncio
    async def test_delay_functionality_works_correctly(self, simulator):
        """Test that the delay functionality works as expected in practical scenarios."""
        
        # Test 1: Cache hit with delay enabled
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.1,
            response_delay_max_seconds=0.2,
            response_delay_cache_only=True
        )
        
        start_time = time.perf_counter()
        delay = await simulator.apply_response_delay(config, is_cache_hit=True)
        elapsed = time.perf_counter() - start_time
        
        assert 0.1 <= delay <= 0.25
        assert 0.1 <= elapsed <= 0.25
        
        # Test 2: Non-cache hit with cache_only=True (should not delay)
        start_time = time.perf_counter()
        delay = await simulator.apply_response_delay(config, is_cache_hit=False)
        elapsed = time.perf_counter() - start_time
        
        assert delay == 0.0
        assert elapsed < 0.01
        
        # Test 3: Non-cache hit with cache_only=False (should delay)
        config.response_delay_cache_only = False
        
        start_time = time.perf_counter()
        delay = await simulator.apply_response_delay(config, is_cache_hit=False)
        elapsed = time.perf_counter() - start_time
        
        assert 0.1 <= delay <= 0.25
        assert 0.1 <= elapsed <= 0.25
    
    @pytest.mark.asyncio
    async def test_delay_with_multiple_concurrent_requests(self, simulator):
        """Test that delays work correctly with concurrent requests."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.05,
            response_delay_max_seconds=0.1,
            response_delay_cache_only=False
        )
        
        async def make_request():
            return await simulator.apply_response_delay(config, is_cache_hit=True)
        
        # Run 5 concurrent requests
        start_time = time.perf_counter()
        delays = await asyncio.gather(*[make_request() for _ in range(5)])
        total_elapsed = time.perf_counter() - start_time
        
        # Each delay should be in range
        for delay in delays:
            assert 0.05 <= delay <= 0.12  # Allow small tolerance
        
        # Total time should be roughly the max delay (since they run concurrently)
        assert total_elapsed <= 0.15  # Should not be sum of all delays
    
    @pytest.mark.asyncio
    async def test_delay_edge_cases(self, simulator):
        """Test edge cases for delay functionality."""
        
        # Test with zero delay range
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.0,
            response_delay_max_seconds=0.0,
            response_delay_cache_only=False
        )
        
        delay = await simulator.apply_response_delay(config, is_cache_hit=True)
        assert delay >= 0.0
        assert delay <= 0.01  # Should be very small
        
        # Test with very small delay
        config.response_delay_min_seconds = 0.001
        config.response_delay_max_seconds = 0.002
        
        delay = await simulator.apply_response_delay(config, is_cache_hit=True)
        assert 0.001 <= delay <= 0.005  # Allow some tolerance for precision
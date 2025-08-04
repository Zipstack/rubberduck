import pytest
import asyncio
import time
from rubberduck.failure import FailureConfig, FailureSimulator


class TestResponseDelayLogic:
    """Test response delay implementation in FailureSimulator."""
    
    @pytest.fixture
    def simulator(self):
        """Create a FailureSimulator instance."""
        return FailureSimulator()
    
    @pytest.mark.asyncio
    async def test_delay_disabled(self, simulator):
        """Test that no delay is applied when disabled."""
        config = FailureConfig(
            response_delay_enabled=False,
            response_delay_min_seconds=1.0,
            response_delay_max_seconds=2.0
        )
        
        start_time = time.perf_counter()
        delay = await simulator.apply_response_delay(config, is_cache_hit=True)
        elapsed = time.perf_counter() - start_time
        
        assert delay == 0.0
        assert elapsed < 0.1  # Should return immediately
    
    @pytest.mark.asyncio
    async def test_delay_cache_only_with_cache_hit(self, simulator):
        """Test that delay is applied for cache hits when cache_only is True."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.1,
            response_delay_max_seconds=0.2,
            response_delay_cache_only=True
        )
        
        delay = await simulator.apply_response_delay(config, is_cache_hit=True)
        
        assert 0.1 <= delay <= 0.3  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_delay_cache_only_without_cache_hit(self, simulator):
        """Test that no delay is applied for non-cache hits when cache_only is True."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=1.0,
            response_delay_max_seconds=2.0,
            response_delay_cache_only=True
        )
        
        start_time = time.perf_counter()
        delay = await simulator.apply_response_delay(config, is_cache_hit=False)
        elapsed = time.perf_counter() - start_time
        
        assert delay == 0.0
        assert elapsed < 0.1  # Should return immediately
    
    @pytest.mark.asyncio
    async def test_delay_always_applied(self, simulator):
        """Test that delay is applied to all requests when cache_only is False."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.1,
            response_delay_max_seconds=0.2,
            response_delay_cache_only=False
        )
        
        # Test with cache hit
        delay1 = await simulator.apply_response_delay(config, is_cache_hit=True)
        assert 0.1 <= delay1 <= 0.3
        
        # Test without cache hit
        delay2 = await simulator.apply_response_delay(config, is_cache_hit=False)
        assert 0.1 <= delay2 <= 0.3
    
    @pytest.mark.asyncio
    async def test_delay_within_range(self, simulator):
        """Test that delays are within the configured range."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.5,
            response_delay_max_seconds=1.0,
            response_delay_cache_only=False
        )
        
        # Run multiple times to test randomness
        delays = []
        for _ in range(10):
            delay = await simulator.apply_response_delay(config, is_cache_hit=True)
            delays.append(delay)
        
        # All delays should be within range (with small tolerance)
        for delay in delays:
            assert 0.5 <= delay <= 1.1
        
        # Check that we get some variation
        assert min(delays) < 0.7  # Some should be near the minimum
        assert max(delays) > 0.8  # Some should be near the maximum
    
    @pytest.mark.asyncio
    async def test_delay_with_same_min_max(self, simulator):
        """Test that delay works correctly when min equals max."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.5,
            response_delay_max_seconds=0.5,
            response_delay_cache_only=False
        )
        
        delay = await simulator.apply_response_delay(config, is_cache_hit=True)
        
        # Should be very close to 0.5
        assert 0.48 <= delay <= 0.52
    
    @pytest.mark.asyncio
    async def test_delay_accuracy(self, simulator):
        """Test that actual delay matches requested delay closely."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.2,
            response_delay_max_seconds=0.3,
            response_delay_cache_only=False
        )
        
        start_time = time.perf_counter()
        delay = await simulator.apply_response_delay(config, is_cache_hit=True)
        total_elapsed = time.perf_counter() - start_time
        
        # The returned delay should match the total elapsed time
        assert abs(delay - total_elapsed) < 0.01  # Within 10ms
        
        # And both should be in the configured range
        assert 0.2 <= delay <= 0.35
        assert 0.2 <= total_elapsed <= 0.35
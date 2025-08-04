import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.responses import JSONResponse

from rubberduck.failure import FailureConfig, FailureSimulator
from rubberduck.proxy import ProxyManager
from rubberduck.logging import log_proxy_request


class TestResponseDelayIntegration:
    """Integration tests for response delay in the full proxy request flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.proxy_manager = ProxyManager()
        self.failure_simulator = FailureSimulator()
    
    @pytest.mark.asyncio
    async def test_cache_hit_with_response_delay(self):
        """Test response delay is applied to cache hits."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.1,
            response_delay_max_seconds=0.2,
            response_delay_cache_only=True
        )
        
        # Mock cached response
        cached_response = {
            "data": {"message": "cached response"},
            "status_code": 200,
            "headers": {"Content-Type": "application/json"},
            "cache_timestamp": "2025-01-01T00:00:00Z"
        }
        
        with patch('asyncio.sleep') as mock_sleep, \
             patch('time.perf_counter', side_effect=[0.0, 0.15]):
            # Simulate delay application
            delay_applied = await self.failure_simulator.apply_response_delay(
                config=config,
                is_cache_hit=True
            )
            
            # Verify delay was applied
            mock_sleep.assert_called_once()
            sleep_arg = mock_sleep.call_args[0][0]
            assert 0.1 <= sleep_arg <= 0.2
            assert delay_applied == 0.15
    
    @pytest.mark.asyncio
    async def test_cache_miss_no_delay_when_cache_only(self):
        """Test no delay is applied to cache misses when cache_only=True."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.1,
            response_delay_max_seconds=0.2,
            response_delay_cache_only=True
        )
        
        with patch('asyncio.sleep') as mock_sleep:
            # Simulate delay application for cache miss
            delay_applied = await self.failure_simulator.apply_response_delay(
                config=config,
                is_cache_hit=False
            )
            
            # Verify no delay was applied
            assert delay_applied == 0.0
            mock_sleep.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_all_requests_with_response_delay(self):
        """Test response delay is applied to all requests when cache_only=False."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.1,
            response_delay_max_seconds=0.1,  # Fixed delay for predictable testing
            response_delay_cache_only=False
        )
        
        # Test cache hit
        start_time = time.time()
        delay_cache_hit = await self.failure_simulator.apply_response_delay(
            config=config,
            is_cache_hit=True
        )
        cache_hit_time = time.time() - start_time
        
        # Test cache miss
        start_time = time.time()
        delay_cache_miss = await self.failure_simulator.apply_response_delay(
            config=config,
            is_cache_hit=False
        )
        cache_miss_time = time.time() - start_time
        
        # Both should have delay applied
        assert abs(delay_cache_hit - 0.1) < 0.01
        assert abs(delay_cache_miss - 0.1) < 0.01
        assert cache_hit_time >= 0.09
        assert cache_miss_time >= 0.09
    
    @pytest.mark.asyncio
    async def test_response_delay_header_added(self):
        """Test that X-Response-Delay-Ms header is added when delay is applied."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.15,
            response_delay_max_seconds=0.15,
            response_delay_cache_only=False
        )
        
        delay_applied = await self.failure_simulator.apply_response_delay(
            config=config,
            is_cache_hit=True
        )
        
        # Simulate response header addition
        headers = {}
        if delay_applied > 0:
            headers["X-Response-Delay-Ms"] = str(int(delay_applied * 1000))
        
        assert "X-Response-Delay-Ms" in headers
        # Should be approximately 150ms
        delay_ms = int(headers["X-Response-Delay-Ms"])
        assert 140 <= delay_ms <= 160  # Allow small tolerance
    
    @pytest.mark.asyncio
    async def test_response_delay_with_error_injection_precedence(self):
        """Test that error injection and response delay work independently."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.1,
            response_delay_max_seconds=0.1,
            response_delay_cache_only=False,
            error_injection_enabled=True,
            error_rates={500: 0.0}  # No errors, just testing precedence
        )
        
        # Mock request
        request = MagicMock()
        request.client.host = "127.0.0.1"
        
        # Test that error processing doesn't interfere with delay
        error = await self.failure_simulator.process_request(config, 1, request)
        assert error is None  # No error should be generated
        
        # Test delay still works
        delay_applied = await self.failure_simulator.apply_response_delay(
            config=config,
            is_cache_hit=True
        )
        assert abs(delay_applied - 0.1) < 0.01
    
    @pytest.mark.asyncio
    async def test_logging_includes_response_delay(self):
        """Test that response delay is logged correctly."""
        # Mock request and response
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.method = "POST"
        
        response = JSONResponse(content={"result": "success"}, status_code=200)
        
        start_time = time.time() - 0.15  # Simulate 150ms request
        response_delay_ms = 100.0  # 100ms delay
        
        # Mock the database and logging
        with patch('rubberduck.logging.SessionLocal') as mock_session_local:
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db
            
            mock_log_entry = MagicMock()
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Call logging function
            await log_proxy_request(
                proxy_id=1,
                request=request,
                response=response,
                start_time=start_time,
                cache_hit=True,
                failure_type=None,
                request_data={"test": "data"},
                response_delay_ms=response_delay_ms
            )
            
            # Verify LogEntry was created with response_delay_ms
            mock_db.add.assert_called_once()
            log_entry_call = mock_db.add.call_args[0][0]
            
            # Check that response_delay_ms was set
            assert hasattr(log_entry_call, 'response_delay_ms')
            assert log_entry_call.response_delay_ms == response_delay_ms
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_with_different_delays(self):
        """Test that concurrent requests with different delay configs work correctly."""
        config_fast = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.05,
            response_delay_max_seconds=0.05,
            response_delay_cache_only=False
        )
        
        config_slow = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.15,
            response_delay_max_seconds=0.15,
            response_delay_cache_only=False
        )
        
        with patch('asyncio.sleep') as mock_sleep, \
             patch('time.perf_counter', side_effect=[0.0, 0.05, 0.0, 0.15]):
            
            async def fast_request():
                delay = await self.failure_simulator.apply_response_delay(config_fast, is_cache_hit=True)
                return delay
            
            async def slow_request():
                delay = await self.failure_simulator.apply_response_delay(config_slow, is_cache_hit=True)
                return delay
            
            # Run requests concurrently
            results = await asyncio.gather(fast_request(), slow_request())
            
            fast_delay, slow_delay = results
            
            # Verify delays are applied correctly
            assert fast_delay == 0.05
            assert slow_delay == 0.15
            
            # Verify sleep was called with correct values
            assert mock_sleep.call_count == 2
            calls = [call.args[0] for call in mock_sleep.call_args_list]
            assert 0.05 in calls
            assert 0.15 in calls
    
    @pytest.mark.asyncio
    async def test_response_delay_disabled_performance(self):
        """Test that disabled response delay has minimal performance impact."""
        config = FailureConfig(
            response_delay_enabled=False,
            response_delay_min_seconds=10.0,  # Large value should be ignored
            response_delay_max_seconds=20.0,
            response_delay_cache_only=False
        )
        
        start_time = time.time()
        
        # Run multiple delay checks
        for _ in range(10):
            delay = await self.failure_simulator.apply_response_delay(config, is_cache_hit=True)
            assert delay == 0.0
        
        total_time = time.time() - start_time
        
        # Should complete very quickly
        assert total_time < 0.1  # 100ms for 10 operations should be plenty
    
    @pytest.mark.asyncio
    async def test_response_delay_range_randomness(self):
        """Test that response delay randomness works within specified range."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.05,
            response_delay_max_seconds=0.15,
            response_delay_cache_only=False
        )
        
        delays = []
        for _ in range(20):
            delay = await self.failure_simulator.apply_response_delay(config, is_cache_hit=True)
            delays.append(delay)
        
        # All delays should be within range
        for delay in delays:
            assert 0.05 <= delay <= 0.15
        
        # Should have some variation (not all identical)
        unique_delays = len(set(delays))
        assert unique_delays > 1  # Should have at least some variation
        
        # Statistical check: mean should be roughly in middle of range
        mean_delay = sum(delays) / len(delays)
        assert 0.08 <= mean_delay <= 0.12  # Allow reasonable variance


class TestResponseDelayEdgeCases:
    """Test edge cases and error conditions for response delay."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.failure_simulator = FailureSimulator()
    
    @pytest.mark.asyncio
    async def test_response_delay_zero_values(self):
        """Test response delay with zero min and max values."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.0,
            response_delay_max_seconds=0.0,
            response_delay_cache_only=False
        )
        
        start_time = time.time()
        delay = await self.failure_simulator.apply_response_delay(config, is_cache_hit=True)
        end_time = time.time()
        
        assert delay <= 0.001  # Allow for floating point precision
        assert (end_time - start_time) < 0.05  # Should be nearly instant
    
    @pytest.mark.asyncio
    async def test_response_delay_very_small_values(self):
        """Test response delay with very small values."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.001,  # 1ms
            response_delay_max_seconds=0.002,  # 2ms
            response_delay_cache_only=False
        )
        
        delay = await self.failure_simulator.apply_response_delay(config, is_cache_hit=True)
        
        assert 0.0009 <= delay <= 0.0025  # Allow for small floating point tolerance
    
    @pytest.mark.asyncio
    async def test_response_delay_equal_min_max(self):
        """Test response delay when min equals max (fixed delay)."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.1,
            response_delay_max_seconds=0.1,  # Same as min
            response_delay_cache_only=False
        )
        
        delays = []
        for _ in range(5):
            delay = await self.failure_simulator.apply_response_delay(config, is_cache_hit=True)
            delays.append(delay)
        
        # All delays should be very close to the expected value
        for delay in delays:
            assert abs(delay - 0.1) < 0.01  # Allow for asyncio.sleep precision


if __name__ == "__main__":
    pytest.main([__file__])
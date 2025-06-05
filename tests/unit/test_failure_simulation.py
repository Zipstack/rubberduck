import pytest
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request, HTTPException
from rubberduck.failure import FailureConfig, FailureSimulator, create_default_failure_config

class TestFailureConfig:
    """Test FailureConfig dataclass functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = FailureConfig()
        
        assert config.timeout_enabled is False
        assert config.timeout_seconds is None
        assert config.timeout_rate == 0.0
        assert config.error_injection_enabled is False
        assert config.error_rates == {}
        assert config.ip_filtering_enabled is False
        assert config.ip_allowlist == []
        assert config.ip_blocklist == []
        assert config.rate_limiting_enabled is False
        assert config.requests_per_minute == 60
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        config = FailureConfig(
            timeout_enabled=True,
            timeout_seconds=5.0,
            timeout_rate=0.1,
            error_injection_enabled=True,
            error_rates={429: 0.2, 500: 0.1},
            ip_filtering_enabled=True,
            ip_allowlist=["192.168.1.0/24"],
            ip_blocklist=["10.0.0.1"],
            rate_limiting_enabled=True,
            requests_per_minute=30
        )
        
        # Serialize to JSON
        json_str = config.to_json()
        
        # Deserialize from JSON
        restored_config = FailureConfig.from_json(json_str)
        
        assert restored_config.timeout_enabled == config.timeout_enabled
        assert restored_config.timeout_seconds == config.timeout_seconds
        assert restored_config.timeout_rate == config.timeout_rate
        assert restored_config.error_injection_enabled == config.error_injection_enabled
        assert restored_config.error_rates == config.error_rates
        assert restored_config.ip_filtering_enabled == config.ip_filtering_enabled
        assert restored_config.ip_allowlist == config.ip_allowlist
        assert restored_config.ip_blocklist == config.ip_blocklist
        assert restored_config.rate_limiting_enabled == config.rate_limiting_enabled
        assert restored_config.requests_per_minute == config.requests_per_minute
    
    def test_json_deserialization_invalid(self):
        """Test handling of invalid JSON."""
        config = FailureConfig.from_json("invalid json")
        assert isinstance(config, FailureConfig)
        assert config.timeout_enabled is False  # Should use defaults
        
        config = FailureConfig.from_json(None)
        assert isinstance(config, FailureConfig)
        assert config.timeout_enabled is False
    
    def test_create_default_failure_config(self):
        """Test default configuration creation."""
        config = create_default_failure_config()
        
        assert config.timeout_enabled is False
        assert config.timeout_seconds == 5.0
        assert config.timeout_rate == 0.0
        assert config.error_injection_enabled is False
        assert 429 in config.error_rates
        assert 500 in config.error_rates
        assert config.error_rates[429] == 0.0
        assert config.error_rates[500] == 0.0


class TestFailureSimulator:
    """Test FailureSimulator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.simulator = FailureSimulator()
    
    def test_ip_filtering_exact_match(self):
        """Test IP filtering with exact IP matches."""
        # Test allowlist
        config = FailureConfig(
            ip_filtering_enabled=True,
            ip_allowlist=["192.168.1.100", "10.0.0.1"]
        )
        
        assert self.simulator._check_ip_filtering(config, "192.168.1.100") is True
        assert self.simulator._check_ip_filtering(config, "10.0.0.1") is True
        assert self.simulator._check_ip_filtering(config, "192.168.1.101") is False
        
        # Test blocklist
        config = FailureConfig(
            ip_filtering_enabled=True,
            ip_blocklist=["192.168.1.100", "10.0.0.1"]
        )
        
        assert self.simulator._check_ip_filtering(config, "192.168.1.100") is False
        assert self.simulator._check_ip_filtering(config, "10.0.0.1") is False
        assert self.simulator._check_ip_filtering(config, "192.168.1.101") is True
    
    def test_ip_filtering_cidr(self):
        """Test IP filtering with CIDR notation."""
        # Test allowlist with CIDR
        config = FailureConfig(
            ip_filtering_enabled=True,
            ip_allowlist=["192.168.1.0/24"]
        )
        
        assert self.simulator._check_ip_filtering(config, "192.168.1.1") is True
        assert self.simulator._check_ip_filtering(config, "192.168.1.254") is True
        assert self.simulator._check_ip_filtering(config, "192.168.2.1") is False
        assert self.simulator._check_ip_filtering(config, "10.0.0.1") is False
        
        # Test blocklist with CIDR
        config = FailureConfig(
            ip_filtering_enabled=True,
            ip_blocklist=["10.0.0.0/8"]
        )
        
        assert self.simulator._check_ip_filtering(config, "10.1.1.1") is False
        assert self.simulator._check_ip_filtering(config, "10.255.255.255") is False
        assert self.simulator._check_ip_filtering(config, "192.168.1.1") is True
    
    def test_ip_filtering_wildcard(self):
        """Test IP filtering with wildcard."""
        config = FailureConfig(
            ip_filtering_enabled=True,
            ip_allowlist=["*"]
        )
        
        assert self.simulator._check_ip_filtering(config, "192.168.1.1") is True
        assert self.simulator._check_ip_filtering(config, "10.0.0.1") is True
    
    def test_ip_filtering_disabled(self):
        """Test that IP filtering is bypassed when disabled."""
        config = FailureConfig(
            ip_filtering_enabled=False,
            ip_blocklist=["192.168.1.1"]
        )
        
        # Should allow all IPs when filtering is disabled
        assert self.simulator._check_ip_filtering(config, "192.168.1.1") is True
        assert self.simulator._check_ip_filtering(config, "10.0.0.1") is True
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        config = FailureConfig(
            rate_limiting_enabled=True,
            requests_per_minute=5
        )
        
        proxy_id = 1
        
        # First 5 requests should be allowed
        for i in range(5):
            assert self.simulator._check_rate_limiting(config, proxy_id) is True
        
        # 6th request should be rate limited
        assert self.simulator._check_rate_limiting(config, proxy_id) is False
        
        # Additional requests should also be rate limited
        assert self.simulator._check_rate_limiting(config, proxy_id) is False
    
    def test_rate_limiting_disabled(self):
        """Test that rate limiting is bypassed when disabled."""
        config = FailureConfig(
            rate_limiting_enabled=False,
            requests_per_minute=1
        )
        
        proxy_id = 1
        
        # Should allow many requests when rate limiting is disabled
        for i in range(10):
            assert self.simulator._check_rate_limiting(config, proxy_id) is True
    
    def test_rate_limiting_multiple_proxies(self):
        """Test that rate limiting is per-proxy."""
        config = FailureConfig(
            rate_limiting_enabled=True,
            requests_per_minute=2
        )
        
        proxy1_id = 1
        proxy2_id = 2
        
        # Use up quota for proxy 1
        assert self.simulator._check_rate_limiting(config, proxy1_id) is True
        assert self.simulator._check_rate_limiting(config, proxy1_id) is True
        assert self.simulator._check_rate_limiting(config, proxy1_id) is False
        
        # Proxy 2 should still have its quota
        assert self.simulator._check_rate_limiting(config, proxy2_id) is True
        assert self.simulator._check_rate_limiting(config, proxy2_id) is True
        assert self.simulator._check_rate_limiting(config, proxy2_id) is False
    
    def test_error_simulation_disabled(self):
        """Test that no errors are generated when disabled."""
        config = FailureConfig(
            error_injection_enabled=False,
            error_rates={429: 1.0, 500: 1.0}  # 100% rate should still not trigger
        )
        
        # Run multiple times to ensure no errors are generated
        for i in range(10):
            error = self.simulator._simulate_error(config)
            assert error is None
    
    def test_error_simulation_enabled(self):
        """Test error simulation with various rates."""
        # Test 100% error rate
        config = FailureConfig(
            error_injection_enabled=True,
            error_rates={429: 1.0}
        )
        
        error = self.simulator._simulate_error(config)
        assert error is not None
        assert error.status_code == 429
        assert "Simulated Error" in error.detail
        
        # Test 0% error rate
        config = FailureConfig(
            error_injection_enabled=True,
            error_rates={500: 0.0}
        )
        
        # Run multiple times to ensure no errors
        for i in range(10):
            error = self.simulator._simulate_error(config)
            assert error is None
    
    @pytest.mark.asyncio
    async def test_timeout_simulation_disabled(self):
        """Test that no timeout occurs when disabled."""
        config = FailureConfig(
            timeout_enabled=False,
            timeout_seconds=10.0,
            timeout_rate=1.0
        )
        
        start_time = time.time()
        await self.simulator._simulate_timeout(config)
        end_time = time.time()
        
        # Should return immediately
        assert (end_time - start_time) < 0.1
    
    @pytest.mark.asyncio
    async def test_timeout_simulation_no_trigger(self):
        """Test timeout simulation when rate is 0."""
        config = FailureConfig(
            timeout_enabled=True,
            timeout_seconds=5.0,
            timeout_rate=0.0  # Never trigger
        )
        
        start_time = time.time()
        await self.simulator._simulate_timeout(config)
        end_time = time.time()
        
        # Should return immediately when rate is 0
        assert (end_time - start_time) < 0.1
    
    @pytest.mark.asyncio
    async def test_timeout_simulation_fixed_delay(self):
        """Test timeout simulation with fixed delay."""
        config = FailureConfig(
            timeout_enabled=True,
            timeout_seconds=0.1,  # Short delay for testing
            timeout_rate=1.0  # Always trigger
        )
        
        start_time = time.time()
        await self.simulator._simulate_timeout(config)
        end_time = time.time()
        
        # Should delay for approximately the configured time
        assert (end_time - start_time) >= 0.09  # Allow small tolerance
        assert (end_time - start_time) < 0.2   # But not too long
    
    @pytest.mark.asyncio
    async def test_process_request_ip_blocked(self):
        """Test request processing with IP blocking."""
        config = FailureConfig(
            ip_filtering_enabled=True,
            ip_blocklist=["192.168.1.100"]
        )
        
        # Mock request
        request = MagicMock()
        request.client.host = "192.168.1.100"
        
        error = await self.simulator.process_request(config, 1, request)
        
        assert error is not None
        assert error.status_code == 403
        assert "blocked" in error.detail.lower()
    
    @pytest.mark.asyncio
    async def test_process_request_rate_limited(self):
        """Test request processing with rate limiting."""
        config = FailureConfig(
            rate_limiting_enabled=True,
            requests_per_minute=1
        )
        
        # Mock request
        request = MagicMock()
        request.client.host = "127.0.0.1"
        
        proxy_id = 99
        
        # First request should succeed
        error = await self.simulator.process_request(config, proxy_id, request)
        assert error is None
        
        # Second request should be rate limited
        error = await self.simulator.process_request(config, proxy_id, request)
        assert error is not None
        assert error.status_code == 429
        assert "rate limit" in error.detail.lower()
    
    @pytest.mark.asyncio
    async def test_process_request_all_checks_pass(self):
        """Test request processing when all checks pass."""
        config = FailureConfig(
            ip_filtering_enabled=True,
            ip_allowlist=["127.0.0.1"],
            rate_limiting_enabled=True,
            requests_per_minute=10,
            timeout_enabled=False,
            error_injection_enabled=False
        )
        
        # Mock request
        request = MagicMock()
        request.client.host = "127.0.0.1"
        
        error = await self.simulator.process_request(config, 1, request)
        
        # Should pass all checks
        assert error is None
    
    @pytest.mark.asyncio
    async def test_process_request_no_client_info(self):
        """Test request processing when client info is missing."""
        config = FailureConfig(
            ip_filtering_enabled=True,
            ip_allowlist=["127.0.0.1"]
        )
        
        # Mock request without client info
        request = MagicMock()
        request.client = None
        
        error = await self.simulator.process_request(config, 1, request)
        
        # Should use default IP (127.0.0.1) and pass
        assert error is None


if __name__ == "__main__":
    pytest.main([__file__])
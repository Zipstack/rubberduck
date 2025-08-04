import pytest
import json
from rubberduck.failure import FailureConfig, create_default_failure_config


class TestFailureConfigResponseDelay:
    """Test response delay configuration in FailureConfig."""
    
    def test_default_response_delay_values(self):
        """Test that default values are set correctly."""
        config = FailureConfig()
        
        assert config.response_delay_enabled is False
        assert config.response_delay_min_seconds == 0.5
        assert config.response_delay_max_seconds == 2.0
        assert config.response_delay_cache_only is True
    
    def test_create_default_failure_config_includes_response_delay(self):
        """Test that create_default_failure_config includes response delay fields."""
        config = create_default_failure_config()
        
        assert config.response_delay_enabled is False
        assert config.response_delay_min_seconds == 0.5
        assert config.response_delay_max_seconds == 2.0
        assert config.response_delay_cache_only is True
    
    def test_to_json_includes_response_delay(self):
        """Test that to_json serializes response delay fields."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=1.0,
            response_delay_max_seconds=3.0,
            response_delay_cache_only=False
        )
        
        json_str = config.to_json()
        data = json.loads(json_str)
        
        assert data["response_delay_enabled"] is True
        assert data["response_delay_min_seconds"] == 1.0
        assert data["response_delay_max_seconds"] == 3.0
        assert data["response_delay_cache_only"] is False
    
    def test_from_json_with_response_delay(self):
        """Test that from_json deserializes response delay fields."""
        json_str = json.dumps({
            "timeout_enabled": False,
            "error_injection_enabled": False,
            "ip_filtering_enabled": False,
            "rate_limiting_enabled": False,
            "response_delay_enabled": True,
            "response_delay_min_seconds": 0.1,
            "response_delay_max_seconds": 5.0,
            "response_delay_cache_only": False
        })
        
        config = FailureConfig.from_json(json_str)
        
        assert config.response_delay_enabled is True
        assert config.response_delay_min_seconds == 0.1
        assert config.response_delay_max_seconds == 5.0
        assert config.response_delay_cache_only is False
    
    def test_from_json_backward_compatibility(self):
        """Test that from_json handles old configs without response delay fields."""
        # Old config without response delay fields
        json_str = json.dumps({
            "timeout_enabled": True,
            "timeout_seconds": 10.0,
            "timeout_rate": 0.5,
            "error_injection_enabled": False,
            "error_rates": {},
            "ip_filtering_enabled": False,
            "ip_allowlist": [],
            "ip_blocklist": [],
            "rate_limiting_enabled": False,
            "requests_per_minute": 60
        })
        
        config = FailureConfig.from_json(json_str)
        
        # Should have default response delay values
        assert config.response_delay_enabled is False
        assert config.response_delay_min_seconds == 0.5
        assert config.response_delay_max_seconds == 2.0
        assert config.response_delay_cache_only is True
        
        # Should preserve other fields
        assert config.timeout_enabled is True
        assert config.timeout_seconds == 10.0
        assert config.timeout_rate == 0.5
    
    def test_from_json_partial_response_delay(self):
        """Test that from_json handles partial response delay fields."""
        # Config with only some response delay fields
        json_str = json.dumps({
            "timeout_enabled": False,
            "error_injection_enabled": False,
            "ip_filtering_enabled": False,
            "rate_limiting_enabled": False,
            "response_delay_enabled": True,
            "response_delay_min_seconds": 1.5
            # Missing max_seconds and cache_only
        })
        
        config = FailureConfig.from_json(json_str)
        
        assert config.response_delay_enabled is True
        assert config.response_delay_min_seconds == 1.5
        assert config.response_delay_max_seconds == 2.0  # Default
        assert config.response_delay_cache_only is True  # Default
    
    def test_round_trip_serialization(self):
        """Test that config survives round-trip serialization."""
        original_config = FailureConfig(
            timeout_enabled=True,
            timeout_seconds=5.0,
            timeout_rate=0.1,
            error_injection_enabled=True,
            error_rates={429: 0.2, 500: 0.1},
            ip_filtering_enabled=True,
            ip_allowlist=["192.168.1.0/24"],
            ip_blocklist=["10.0.0.1"],
            rate_limiting_enabled=True,
            requests_per_minute=100,
            response_delay_enabled=True,
            response_delay_min_seconds=0.2,
            response_delay_max_seconds=1.0,
            response_delay_cache_only=False
        )
        
        # Serialize and deserialize
        json_str = original_config.to_json()
        loaded_config = FailureConfig.from_json(json_str)
        
        # Check all fields match
        assert loaded_config.timeout_enabled == original_config.timeout_enabled
        assert loaded_config.timeout_seconds == original_config.timeout_seconds
        assert loaded_config.timeout_rate == original_config.timeout_rate
        assert loaded_config.error_injection_enabled == original_config.error_injection_enabled
        assert loaded_config.error_rates == original_config.error_rates
        assert loaded_config.ip_filtering_enabled == original_config.ip_filtering_enabled
        assert loaded_config.ip_allowlist == original_config.ip_allowlist
        assert loaded_config.ip_blocklist == original_config.ip_blocklist
        assert loaded_config.rate_limiting_enabled == original_config.rate_limiting_enabled
        assert loaded_config.requests_per_minute == original_config.requests_per_minute
        assert loaded_config.response_delay_enabled == original_config.response_delay_enabled
        assert loaded_config.response_delay_min_seconds == original_config.response_delay_min_seconds
        assert loaded_config.response_delay_max_seconds == original_config.response_delay_max_seconds
        assert loaded_config.response_delay_cache_only == original_config.response_delay_cache_only
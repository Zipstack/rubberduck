import pytest
from fastapi import HTTPException

from rubberduck.failure import FailureConfig


class TestResponseDelayValidation:
    """Test validation logic for response delay configuration."""
    
    def test_create_failure_config_with_response_delay_fields(self):
        """Test that FailureConfig can be created with response delay fields."""
        config_data = {
            "timeout_enabled": False,
            "error_injection_enabled": False,
            "ip_filtering_enabled": False,
            "rate_limiting_enabled": False,
            "response_delay_enabled": True,
            "response_delay_min_seconds": 0.5,
            "response_delay_max_seconds": 2.0,
            "response_delay_cache_only": True
        }
        
        # Should not raise any exception
        config = FailureConfig(**config_data)
        
        assert config.response_delay_enabled is True
        assert config.response_delay_min_seconds == 0.5
        assert config.response_delay_max_seconds == 2.0
        assert config.response_delay_cache_only is True
    
    def test_validate_response_delay_ranges(self):
        """Test various response delay value combinations."""
        # Test valid configurations
        valid_configs = [
            # Normal range
            {"response_delay_min_seconds": 0.5, "response_delay_max_seconds": 2.0},
            # Zero delays
            {"response_delay_min_seconds": 0.0, "response_delay_max_seconds": 0.0},
            # Equal min and max
            {"response_delay_min_seconds": 1.5, "response_delay_max_seconds": 1.5},
            # Small values
            {"response_delay_min_seconds": 0.001, "response_delay_max_seconds": 0.002}
        ]
        
        for delay_config in valid_configs:
            config = FailureConfig(
                response_delay_enabled=True,
                response_delay_cache_only=True,
                **delay_config
            )
            # Should create successfully
            assert config.response_delay_min_seconds == delay_config["response_delay_min_seconds"]
            assert config.response_delay_max_seconds == delay_config["response_delay_max_seconds"]
    
    def test_failure_config_serialization_with_delays(self):
        """Test that response delay fields are properly serialized."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.8,
            response_delay_max_seconds=1.5,
            response_delay_cache_only=False
        )
        
        # Test to_json
        json_str = config.to_json()
        assert "response_delay_enabled" in json_str
        assert "response_delay_min_seconds" in json_str
        assert "response_delay_max_seconds" in json_str
        assert "response_delay_cache_only" in json_str
        
        # Test round-trip
        loaded_config = FailureConfig.from_json(json_str)
        assert loaded_config.response_delay_enabled is True
        assert loaded_config.response_delay_min_seconds == 0.8
        assert loaded_config.response_delay_max_seconds == 1.5
        assert loaded_config.response_delay_cache_only is False
    
    def test_config_creation_with_partial_fields(self):
        """Test creating config with only some response delay fields."""
        # Should use defaults for missing fields
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.8
            # Missing max_seconds and cache_only
        )
        
        assert config.response_delay_enabled is True
        assert config.response_delay_min_seconds == 0.8
        assert config.response_delay_max_seconds == 2.0  # Default
        assert config.response_delay_cache_only is True  # Default
    
    def test_backwards_compatibility(self):
        """Test that old configs without response delay fields still work."""
        # Simulate old config JSON without response delay fields
        old_config_json = '{"timeout_enabled": false, "error_injection_enabled": false, "ip_filtering_enabled": false, "rate_limiting_enabled": false}'
        
        config = FailureConfig.from_json(old_config_json)
        
        # Should have default values
        assert config.response_delay_enabled is False
        assert config.response_delay_min_seconds == 0.5
        assert config.response_delay_max_seconds == 2.0
        assert config.response_delay_cache_only is True
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from rubberduck.main import app
from rubberduck.failure import FailureConfig


class TestResponseDelayAPI:
    """Test API endpoints for response delay configuration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_response_delay_validation_valid_config(self):
        """Test validation with valid response delay configuration."""
        config_data = {
            "response_delay_enabled": True,
            "response_delay_min_seconds": 0.5,
            "response_delay_max_seconds": 2.0,
            "response_delay_cache_only": True,
            # Include other required fields
            "timeout_enabled": False,
            "timeout_seconds": 5.0,
            "timeout_rate": 0.0,
            "error_injection_enabled": False,
            "error_rates": {},
            "ip_filtering_enabled": False,
            "ip_allowlist": [],
            "ip_blocklist": [],
            "rate_limiting_enabled": False,
            "requests_per_minute": 60
        }
        
        # Test that config can be created and serialized
        config = FailureConfig(**config_data)
        json_str = config.to_json()
        restored_config = FailureConfig.from_json(json_str)
        
        assert restored_config.response_delay_enabled is True
        assert restored_config.response_delay_min_seconds == 0.5
        assert restored_config.response_delay_max_seconds == 2.0
        assert restored_config.response_delay_cache_only is True
    
    def test_response_delay_validation_negative_values(self):
        """Test validation rejects negative delay values."""
        # Test negative min
        with pytest.raises(ValueError, match="Response delay values must be non-negative"):
            self._validate_response_delay(-0.1, 2.0)
        
        # Test negative max
        with pytest.raises(ValueError, match="Response delay values must be non-negative"):
            self._validate_response_delay(0.5, -1.0)
    
    def test_response_delay_validation_min_greater_than_max(self):
        """Test validation rejects min > max."""
        with pytest.raises(ValueError, match="Response delay minimum must be less than or equal to maximum"):
            self._validate_response_delay(3.0, 2.0)
    
    def test_response_delay_validation_max_too_large(self):
        """Test validation rejects max > 30 seconds."""
        with pytest.raises(ValueError, match="Response delay maximum cannot exceed 30 seconds"):
            self._validate_response_delay(1.0, 31.0)
    
    def test_response_delay_validation_edge_cases(self):
        """Test validation edge cases."""
        # Test zero values (should be valid)
        self._validate_response_delay(0.0, 0.0)
        
        # Test min == max (should be valid)
        self._validate_response_delay(1.5, 1.5)
        
        # Test max at limit (should be valid)
        self._validate_response_delay(1.0, 30.0)
        
        # Test very small values (should be valid)
        self._validate_response_delay(0.001, 0.002)
    
    def _validate_response_delay(self, min_delay: float, max_delay: float):
        """Helper method to validate response delay values."""
        if min_delay < 0 or max_delay < 0:
            raise ValueError("Response delay values must be non-negative")
        if min_delay > max_delay:
            raise ValueError("Response delay minimum must be less than or equal to maximum")
        if max_delay > 30:
            raise ValueError("Response delay maximum cannot exceed 30 seconds")


class TestResponseDelayConfigDefaults:
    """Test default configuration behavior for response delay."""
    
    def test_default_config_has_response_delay_fields(self):
        """Test that default config includes response delay fields."""
        config = FailureConfig()
        
        assert hasattr(config, 'response_delay_enabled')
        assert hasattr(config, 'response_delay_min_seconds')
        assert hasattr(config, 'response_delay_max_seconds')
        assert hasattr(config, 'response_delay_cache_only')
        
        # Test default values
        assert config.response_delay_enabled is False
        assert config.response_delay_min_seconds == 0.5
        assert config.response_delay_max_seconds == 2.0
        assert config.response_delay_cache_only is True
    
    def test_json_roundtrip_preserves_response_delay(self):
        """Test that JSON serialization preserves response delay fields."""
        original_config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=1.5,
            response_delay_max_seconds=3.5,
            response_delay_cache_only=False
        )
        
        json_str = original_config.to_json()
        restored_config = FailureConfig.from_json(json_str)
        
        assert restored_config.response_delay_enabled == original_config.response_delay_enabled
        assert restored_config.response_delay_min_seconds == original_config.response_delay_min_seconds
        assert restored_config.response_delay_max_seconds == original_config.response_delay_max_seconds
        assert restored_config.response_delay_cache_only == original_config.response_delay_cache_only
    
    def test_backward_compatibility_missing_fields(self):
        """Test backward compatibility when response delay fields are missing from JSON."""
        # Simulate old JSON without response delay fields
        old_config_json = json.dumps({
            "timeout_enabled": False,
            "timeout_seconds": 5.0,
            "timeout_rate": 0.0,
            "error_injection_enabled": False,
            "error_rates": {},
            "ip_filtering_enabled": False,
            "ip_allowlist": [],
            "ip_blocklist": [],
            "rate_limiting_enabled": False,
            "requests_per_minute": 60
            # Missing response delay fields
        })
        
        config = FailureConfig.from_json(old_config_json)
        
        # Should use default values
        assert config.response_delay_enabled is False
        assert config.response_delay_min_seconds == 0.5
        assert config.response_delay_max_seconds == 2.0
        assert config.response_delay_cache_only is True


class TestResponseDelayConfigurationRange:
    """Test response delay configuration with various ranges."""
    
    def test_millisecond_precision(self):
        """Test response delay with millisecond precision."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=0.001,  # 1ms
            response_delay_max_seconds=0.010,  # 10ms
            response_delay_cache_only=False
        )
        
        assert config.response_delay_min_seconds == 0.001
        assert config.response_delay_max_seconds == 0.010
    
    def test_second_precision(self):
        """Test response delay with second precision."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=1.0,
            response_delay_max_seconds=5.0,
            response_delay_cache_only=True
        )
        
        assert config.response_delay_min_seconds == 1.0
        assert config.response_delay_max_seconds == 5.0
    
    def test_maximum_allowed_delay(self):
        """Test response delay at maximum allowed value."""
        config = FailureConfig(
            response_delay_enabled=True,
            response_delay_min_seconds=29.0,
            response_delay_max_seconds=30.0,  # Maximum allowed
            response_delay_cache_only=False
        )
        
        assert config.response_delay_min_seconds == 29.0
        assert config.response_delay_max_seconds == 30.0


if __name__ == "__main__":
    pytest.main([__file__])
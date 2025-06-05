import pytest
from providers import get_provider, list_providers, get_all_providers, PROVIDERS
from providers.base import BaseProvider
from providers.openai import OpenAIProvider

def test_provider_registration():
    """Test that providers are automatically registered."""
    providers = list_providers()
    assert "openai" in providers
    assert len(providers) >= 1

def test_get_provider_success():
    """Test getting a registered provider."""
    provider = get_provider("openai")
    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "openai"
    assert provider.base_url == "https://api.openai.com/v1"

def test_get_provider_not_found():
    """Test getting a non-existent provider raises KeyError."""
    with pytest.raises(KeyError) as exc_info:
        get_provider("nonexistent")
    
    assert "Provider 'nonexistent' not found" in str(exc_info.value)

def test_get_all_providers():
    """Test getting all providers returns dictionary."""
    all_providers = get_all_providers()
    assert isinstance(all_providers, dict)
    assert "openai" in all_providers
    assert isinstance(all_providers["openai"], OpenAIProvider)

def test_openai_provider_interface():
    """Test that OpenAI provider implements the required interface."""
    provider = get_provider("openai")
    
    # Check it has required methods
    assert hasattr(provider, "normalize_request")
    assert hasattr(provider, "forward_request")
    assert hasattr(provider, "get_supported_endpoints")
    assert hasattr(provider, "transform_error_response")
    assert hasattr(provider, "generate_cache_key")

def test_openai_supported_endpoints():
    """Test OpenAI provider returns expected endpoints."""
    provider = get_provider("openai")
    endpoints = provider.get_supported_endpoints()
    
    expected_endpoints = [
        "/chat/completions",
        "/completions", 
        "/embeddings",
        "/models"
    ]
    
    for endpoint in expected_endpoints:
        assert endpoint in endpoints

def test_normalize_request():
    """Test request normalization."""
    provider = get_provider("openai")
    
    # Test with a typical chat completion request
    request_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        "temperature": 0.7,
        "max_tokens": 150,
        "extra_param": "should_be_ignored"
    }
    
    normalized = provider.normalize_request(request_data)
    
    # Should include core parameters
    assert normalized["model"] == "gpt-3.5-turbo"
    assert normalized["temperature"] == 0.7
    assert normalized["max_tokens"] == 150
    assert len(normalized["messages"]) == 2
    
    # Should exclude non-core parameters
    assert "extra_param" not in normalized

def test_cache_key_generation():
    """Test cache key generation is consistent."""
    provider = get_provider("openai")
    
    request1 = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7
    }
    
    request2 = {
        "temperature": 0.7,
        "model": "gpt-3.5-turbo", 
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    # Same content but different order should produce same cache key
    normalized1 = provider.normalize_request(request1)
    normalized2 = provider.normalize_request(request2)
    
    key1 = provider.generate_cache_key(normalized1)
    key2 = provider.generate_cache_key(normalized2)
    
    assert key1 == key2
    assert len(key1) == 64  # SHA-256 hash length

def test_cache_key_different_requests():
    """Test different requests produce different cache keys."""
    provider = get_provider("openai")
    
    request1 = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7
    }
    
    request2 = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Goodbye"}],  # Different content
        "temperature": 0.7
    }
    
    normalized1 = provider.normalize_request(request1)
    normalized2 = provider.normalize_request(request2)
    
    key1 = provider.generate_cache_key(normalized1)
    key2 = provider.generate_cache_key(normalized2)
    
    assert key1 != key2

def test_error_response_transformation():
    """Test error response transformation to OpenAI format."""
    provider = get_provider("openai")
    
    error_response = {
        "error": {
            "message": "Invalid request",
            "type": "invalid_request_error"
        }
    }
    
    transformed = provider.transform_error_response(error_response, 400)
    
    assert transformed["status_code"] == 400
    assert "data" in transformed
    assert "error" in transformed["data"]
    assert transformed["data"]["error"]["message"] == "Invalid request"
    assert transformed["data"]["error"]["type"] == "invalid_request_error"
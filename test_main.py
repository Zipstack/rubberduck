import pytest
from fastapi.testclient import TestClient
from main import app
from failure_simulation import create_default_failure_config

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    
    json_response = response.json()
    assert json_response["status"] == "ok"
    assert json_response["version"] == "0.1.0"
    assert isinstance(json_response, dict)
    assert len(json_response) == 2

def test_failure_config_endpoints():
    """Test failure configuration management endpoints."""
    # Create user and get auth headers
    import time
    user_data = {"email": f"test-failure-{int(time.time())}@example.com", "password": "testpass123"}
    
    # Register user
    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code == 201
    
    # Login to get token
    login_response = client.post("/auth/jwt/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test proxy
    proxy_data = {
        "name": "test-failure-proxy",
        "provider": "openai",
        "model_name": "gpt-4",
        "description": "Test proxy for failure config"
    }
    
    response = client.post("/proxies", json=proxy_data, headers=headers)
    assert response.status_code == 200
    proxy_id = response.json()["id"]
    
    # Test getting default failure config
    response = client.get(f"/proxies/{proxy_id}/failure-config", headers=headers)
    assert response.status_code == 200
    config_data = response.json()
    assert "failure_config" in config_data
    assert config_data["proxy_id"] == proxy_id
    
    # Default config should have everything disabled
    config = config_data["failure_config"]
    assert config["timeout_enabled"] is False
    assert config["error_injection_enabled"] is False
    assert config["ip_filtering_enabled"] is False
    assert config["rate_limiting_enabled"] is False
    
    # Test updating failure config
    new_config = {
        "timeout_enabled": True,
        "timeout_seconds": 5.0,
        "timeout_rate": 0.1,
        "error_injection_enabled": True,
        "error_rates": {429: 0.2, 500: 0.1},
        "ip_filtering_enabled": True,
        "ip_allowlist": ["192.168.1.0/24"],
        "ip_blocklist": ["10.0.0.1"],
        "rate_limiting_enabled": True,
        "requests_per_minute": 30
    }
    
    response = client.put(f"/proxies/{proxy_id}/failure-config", json=new_config, headers=headers)
    assert response.status_code == 200
    assert response.json()["proxy_id"] == proxy_id
    
    # Verify the config was updated
    response = client.get(f"/proxies/{proxy_id}/failure-config", headers=headers)
    assert response.status_code == 200
    updated_config = response.json()["failure_config"]
    
    assert updated_config["timeout_enabled"] is True
    assert updated_config["timeout_seconds"] == 5.0
    assert updated_config["timeout_rate"] == 0.1
    assert updated_config["error_injection_enabled"] is True
    assert updated_config["error_rates"] == {"429": 0.2, "500": 0.1}  # JSON converts int keys to strings
    assert updated_config["ip_filtering_enabled"] is True
    assert updated_config["ip_allowlist"] == ["192.168.1.0/24"]
    assert updated_config["ip_blocklist"] == ["10.0.0.1"]
    assert updated_config["rate_limiting_enabled"] is True
    assert updated_config["requests_per_minute"] == 30
    
    # Test resetting failure config
    response = client.post(f"/proxies/{proxy_id}/failure-config/reset", headers=headers)
    assert response.status_code == 200
    assert response.json()["proxy_id"] == proxy_id
    
    # Verify config was reset to defaults
    response = client.get(f"/proxies/{proxy_id}/failure-config", headers=headers)
    assert response.status_code == 200
    reset_config = response.json()["failure_config"]
    
    assert reset_config["timeout_enabled"] is False
    assert reset_config["error_injection_enabled"] is False
    assert reset_config["ip_filtering_enabled"] is False
    assert reset_config["rate_limiting_enabled"] is False
    
    # Test invalid config update
    invalid_config = {"invalid_field": True}
    response = client.put(f"/proxies/{proxy_id}/failure-config", json=invalid_config, headers=headers)
    assert response.status_code == 400
    
    # Test accessing non-existent proxy
    response = client.get("/proxies/99999/failure-config", headers=headers)
    assert response.status_code == 404
import pytest
import json
from datetime import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from rubberduck.main import app
from rubberduck.database import get_async_session, Base, SessionLocal
from rubberduck.models import User, Proxy, CacheEntry
from rubberduck.cache import CacheManager, cache_manager

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_cache.db"
test_async_engine = create_async_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingAsyncSessionLocal = sessionmaker(
    test_async_engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_async_session():
    async with TestingAsyncSessionLocal() as session:
        yield session

app.dependency_overrides[get_async_session] = override_get_async_session

@pytest.fixture(scope="function")
def client():
    # Setup
    async def setup():
        async with test_async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    import asyncio
    asyncio.run(setup())
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Teardown
    async def teardown():
        async with test_async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    asyncio.run(teardown())

@pytest.fixture
def auth_headers(client):
    """Create a user and return auth headers."""
    # Register user
    register_response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    assert register_response.status_code == 201
    
    # Login
    login_response = client.post("/auth/jwt/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

def test_cache_manager_initialization():
    """Test CacheManager initialization."""
    manager = CacheManager()
    assert manager is not None

def test_generate_cache_key():
    """Test cache key generation."""
    manager = CacheManager()
    
    normalized_request = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7
    }
    
    cache_key = manager.generate_cache_key(1, normalized_request)
    
    # Should be a 64-character hex string (SHA-256)
    assert len(cache_key) == 64
    assert all(c in '0123456789abcdef' for c in cache_key)

def test_cache_key_consistency():
    """Test that same request produces same cache key."""
    manager = CacheManager()
    
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
    
    key1 = manager.generate_cache_key(1, request1)
    key2 = manager.generate_cache_key(1, request2)
    
    assert key1 == key2

def test_cache_key_different_for_different_requests():
    """Test that different requests produce different cache keys."""
    manager = CacheManager()
    
    request1 = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7
    }
    
    request2 = {
        "model": "gpt-3.5-turbo", 
        "messages": [{"role": "user", "content": "Goodbye"}],
        "temperature": 0.7
    }
    
    key1 = manager.generate_cache_key(1, request1)
    key2 = manager.generate_cache_key(1, request2)
    
    assert key1 != key2

def test_cache_key_different_for_different_proxies():
    """Test that same request for different proxies produces different cache keys."""
    manager = CacheManager()
    
    request = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7
    }
    
    key1 = manager.generate_cache_key(1, request)
    key2 = manager.generate_cache_key(2, request)
    
    assert key1 != key2

def test_store_and_retrieve_cache():
    """Test storing and retrieving cached responses."""
    manager = CacheManager()
    
    proxy_id = 1
    normalized_request = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    cache_key = manager.generate_cache_key(proxy_id, normalized_request)
    
    response_data = {
        "id": "chatcmpl-123",
        "choices": [{"message": {"content": "Hi there!"}}]
    }
    
    response_headers = {"content-type": "application/json"}
    
    # Store successful response
    stored = manager.store_response(
        proxy_id=proxy_id,
        cache_key=cache_key,
        normalized_request=normalized_request,
        response_data=response_data,
        response_headers=response_headers,
        status_code=200
    )
    
    assert stored is True
    
    # Retrieve cached response
    cached_response = manager.get_cached_response(proxy_id, cache_key)
    
    assert cached_response is not None
    assert cached_response["data"] == response_data
    assert cached_response["headers"] == response_headers
    assert cached_response["cached"] is True
    assert "cache_timestamp" in cached_response

def test_cache_miss():
    """Test cache miss for non-existent cache key."""
    manager = CacheManager()
    
    cached_response = manager.get_cached_response(1, "nonexistent_key")
    assert cached_response is None

def test_store_non_2xx_response():
    """Test that non-2xx responses are not cached."""
    manager = CacheManager()
    
    proxy_id = 1
    normalized_request = {"model": "gpt-3.5-turbo"}
    cache_key = manager.generate_cache_key(proxy_id, normalized_request)
    
    response_data = {"error": {"message": "Bad request"}}
    response_headers = {"content-type": "application/json"}
    
    # Try to store error response
    stored = manager.store_response(
        proxy_id=proxy_id,
        cache_key=cache_key,
        normalized_request=normalized_request,
        response_data=response_data,
        response_headers=response_headers,
        status_code=400  # Client error
    )
    
    assert stored is False
    
    # Verify it's not cached
    cached_response = manager.get_cached_response(proxy_id, cache_key)
    assert cached_response is None

def test_cache_invalidation():
    """Test cache invalidation for a proxy."""
    manager = CacheManager()
    
    proxy_id = 999  # Use unique proxy ID to avoid conflicts
    
    # Store multiple cache entries
    for i in range(3):
        normalized_request = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": f"Message {i}"}]
        }
        cache_key = manager.generate_cache_key(proxy_id, normalized_request)
        
        manager.store_response(
            proxy_id=proxy_id,
            cache_key=cache_key,
            normalized_request=normalized_request,
            response_data={"response": f"Response {i}"},
            response_headers={},
            status_code=200
        )
    
    # Invalidate cache
    deleted_count = manager.invalidate_proxy_cache(proxy_id)
    assert deleted_count == 3
    
    # Verify cache is empty
    stats = manager.get_cache_stats(proxy_id)
    assert stats["total_entries"] == 0

def test_cache_stats():
    """Test cache statistics."""
    manager = CacheManager()
    
    proxy_id = 998  # Use unique proxy ID to avoid conflicts
    
    # Initially empty
    stats = manager.get_cache_stats(proxy_id)
    assert stats["total_entries"] == 0
    assert stats["oldest_entry"] is None
    assert stats["newest_entry"] is None
    
    # Add cache entries
    for i in range(2):
        normalized_request = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": f"Message {i}"}]
        }
        cache_key = manager.generate_cache_key(proxy_id, normalized_request)
        
        manager.store_response(
            proxy_id=proxy_id,
            cache_key=cache_key,
            normalized_request=normalized_request,
            response_data={"response": f"Response {i}"},
            response_headers={},
            status_code=200
        )
    
    # Check stats
    stats = manager.get_cache_stats(proxy_id)
    assert stats["total_entries"] == 2
    assert stats["oldest_entry"] is not None
    assert stats["newest_entry"] is not None

def test_cache_invalidation_endpoint(client, auth_headers):
    """Test cache invalidation API endpoint."""
    # Create a proxy
    proxy_data = {
        "name": "Test Proxy",
        "provider": "openai",
        "model_name": "gpt-3.5-turbo"
    }
    
    create_response = client.post("/proxies", json=proxy_data, headers=auth_headers)
    assert create_response.status_code == 200
    proxy_id = create_response.json()["id"]
    
    # Test cache invalidation
    invalidate_response = client.delete(f"/cache/{proxy_id}", headers=auth_headers)
    assert invalidate_response.status_code == 200
    
    data = invalidate_response.json()
    assert "message" in data
    assert "entries_removed" in data

def test_cache_stats_endpoint(client, auth_headers):
    """Test cache statistics API endpoint."""
    # Create a proxy
    proxy_data = {
        "name": "Test Proxy",
        "provider": "openai",
        "model_name": "gpt-3.5-turbo"
    }
    
    create_response = client.post("/proxies", json=proxy_data, headers=auth_headers)
    assert create_response.status_code == 200
    proxy_id = create_response.json()["id"]
    
    # Test cache stats
    stats_response = client.get(f"/cache/{proxy_id}/stats", headers=auth_headers)
    assert stats_response.status_code == 200
    
    data = stats_response.json()
    assert "proxy_id" in data
    assert "cache_stats" in data
    assert data["proxy_id"] == proxy_id

def test_cache_invalidation_unauthorized_proxy(client, auth_headers):
    """Test cache invalidation fails for unauthorized proxy."""
    # Try to invalidate cache for non-existent proxy
    invalidate_response = client.delete("/cache/999", headers=auth_headers)
    assert invalidate_response.status_code == 404
    assert "Proxy not found" in invalidate_response.json()["detail"]
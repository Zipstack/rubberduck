import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from rubberduck.main import app
from rubberduck.database import get_async_session, Base
from rubberduck.models import User

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_auth.db"
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
    
    asyncio.run(setup())
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Teardown
    async def teardown():
        async with test_async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    asyncio.run(teardown())

def test_user_registration(client):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "secretpassword123"
    })
    assert response.status_code == 201
    
    user_data = response.json()
    assert user_data["email"] == "test@example.com"
    assert "id" in user_data
    assert user_data["is_active"] is True
    assert user_data["is_superuser"] is False
    assert user_data["is_verified"] is False

def test_user_login_success(client):
    # First register a user
    register_response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "secretpassword123"
    })
    assert register_response.status_code == 201
    
    # Then login
    login_response = client.post("/auth/jwt/login", data={
        "username": "test@example.com",
        "password": "secretpassword123"
    })
    assert login_response.status_code == 200
    
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"

def test_user_login_invalid_credentials(client):
    # Try to login with non-existent user
    login_response = client.post("/auth/jwt/login", data={
        "username": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert login_response.status_code == 400

def test_protected_route_without_token(client):
    response = client.get("/protected-route")
    assert response.status_code == 401

def test_protected_route_with_valid_token(client):
    # Register and login to get token
    register_response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "secretpassword123"
    })
    assert register_response.status_code == 201
    
    login_response = client.post("/auth/jwt/login", data={
        "username": "test@example.com",
        "password": "secretpassword123"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Access protected route with token
    protected_response = client.get(
        "/protected-route",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert protected_response.status_code == 200
    assert "Hello test@example.com" in protected_response.text

def test_protected_route_with_invalid_token(client):
    response = client.get(
        "/protected-route",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
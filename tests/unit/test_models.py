import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from rubberduck.database import Base
from rubberduck.models import User, Proxy, LogEntry
from datetime import datetime

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

def test_user_creation(db):
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123",
        is_verified=True
    )
    db.add(user)
    db.commit()
    
    retrieved_user = db.query(User).filter(User.email == "test@example.com").first()
    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.hashed_password == "hashed_password_123"
    assert retrieved_user.is_verified is True
    assert retrieved_user.id is not None

def test_proxy_creation_with_user_fk(db):
    # Create user first
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123",
        is_verified=True
    )
    db.add(user)
    db.commit()
    
    # Create proxy with foreign key to user
    proxy = Proxy(
        name="Test Proxy",
        port=8001,
        status="running",
        user_id=user.id,
        provider="openai",
        model_name="gpt-3.5-turbo",
        description="Test proxy description"
    )
    db.add(proxy)
    db.commit()
    
    retrieved_proxy = db.query(Proxy).filter(Proxy.name == "Test Proxy").first()
    assert retrieved_proxy is not None
    assert retrieved_proxy.name == "Test Proxy"
    assert retrieved_proxy.port == 8001
    assert retrieved_proxy.status == "running"
    assert retrieved_proxy.user_id == user.id
    assert retrieved_proxy.provider == "openai"
    assert retrieved_proxy.model_name == "gpt-3.5-turbo"
    
    # Test relationship
    assert retrieved_proxy.owner.email == "test@example.com"
    assert user.proxies[0].name == "Test Proxy"

def test_log_entry_creation_with_proxy_fk(db):
    # Create user and proxy first
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123",
        is_verified=True
    )
    db.add(user)
    db.commit()
    
    proxy = Proxy(
        name="Test Proxy",
        port=8001,
        status="running",
        user_id=user.id,
        provider="openai",
        model_name="gpt-3.5-turbo"
    )
    db.add(proxy)
    db.commit()
    
    # Create log entry with foreign key to proxy
    log_entry = LogEntry(
        proxy_id=proxy.id,
        ip_address="127.0.0.1",
        status_code=200,
        latency=150.5,
        cache_hit=True,
        prompt_hash="abc123def456",
        token_usage=50,
        cost=0.001
    )
    db.add(log_entry)
    db.commit()
    
    retrieved_log = db.query(LogEntry).filter(LogEntry.prompt_hash == "abc123def456").first()
    assert retrieved_log is not None
    assert retrieved_log.proxy_id == proxy.id
    assert retrieved_log.ip_address == "127.0.0.1"
    assert retrieved_log.status_code == 200
    assert retrieved_log.latency == 150.5
    assert retrieved_log.cache_hit is True
    assert retrieved_log.prompt_hash == "abc123def456"
    assert retrieved_log.token_usage == 50
    assert retrieved_log.cost == 0.001
    
    # Test relationship
    assert retrieved_log.proxy.name == "Test Proxy"
    assert proxy.log_entries[0].ip_address == "127.0.0.1"

def test_foreign_key_constraints(db):
    # Test that creating a proxy with non-existent user_id creates proxy but no valid relationship
    proxy = Proxy(
        name="Invalid Proxy",
        port=8002,
        status="stopped",
        user_id=999,  # Non-existent user ID
        provider="anthropic",
        model_name="claude-3"
    )
    db.add(proxy)
    db.commit()
    
    # Proxy should be created but owner relationship should be None
    retrieved_proxy = db.query(Proxy).filter(Proxy.name == "Invalid Proxy").first()
    assert retrieved_proxy is not None
    assert retrieved_proxy.user_id == 999
    assert retrieved_proxy.owner is None  # No valid relationship
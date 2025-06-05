from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import uuid
from datetime import datetime
from ..database import Base
from fastapi_users.db import SQLAlchemyBaseUserTableUUID

# SQLite-compatible UUID type
class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value

class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    created_at = Column(DateTime, default=datetime.utcnow)
    proxies = relationship("Proxy", back_populates="owner")

class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    port = Column(Integer, unique=True, nullable=True)
    status = Column(String, default="stopped")  # running, stopped, error
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # openai, anthropic, etc.
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Failure simulation configuration (JSON strings)
    failure_config = Column(String, nullable=True)  # JSON config for failure simulation
    
    owner = relationship("User", back_populates="proxies")
    log_entries = relationship("LogEntry", back_populates="proxy")

class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    proxy_id = Column(Integer, ForeignKey("proxies.id"), nullable=False)
    ip_address = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    latency = Column(Float, nullable=False)  # in milliseconds
    cache_hit = Column(Boolean, default=False)
    prompt_hash = Column(String, nullable=True)
    failure_type = Column(String, nullable=True)  # timeout, error_injection, etc.
    token_usage = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)

    proxy = relationship("Proxy", back_populates="log_entries")

class CacheEntry(Base):
    __tablename__ = "cache_entries"

    id = Column(Integer, primary_key=True, index=True)
    proxy_id = Column(Integer, ForeignKey("proxies.id"), nullable=False)
    cache_key = Column(String, nullable=False, index=True)
    request_data = Column(String, nullable=False)  # JSON string of normalized request
    response_data = Column(String, nullable=False)  # JSON string of response
    response_headers = Column(String, nullable=True)  # JSON string of headers
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite index for faster lookups
    __table_args__ = (
        Index('ix_cache_proxy_key', 'proxy_id', 'cache_key'),
    )

    proxy = relationship("Proxy")
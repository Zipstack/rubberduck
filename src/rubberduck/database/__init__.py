from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import os

# Get the project root directory (3 levels up from this file: src/rubberduck/database/__init__.py)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'rubberduck.db')}"
SQLALCHEMY_ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'rubberduck.db')}"

# Sync engine for regular operations  
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    pool_recycle=300
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine for FastAPI-Users
async_engine = create_async_engine(SQLALCHEMY_ASYNC_DATABASE_URL)
async_session_maker = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()
metadata = MetaData()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
from database import engine, async_engine, Base
from models import User, Proxy, LogEntry
import asyncio

def create_sync_tables():
    Base.metadata.create_all(bind=engine)
    print("Sync tables created successfully")

async def create_async_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Async tables created successfully")

if __name__ == "__main__":
    create_sync_tables()
    asyncio.run(create_async_tables())
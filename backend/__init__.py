"""Backend package initialization."""
__version__ = "1.0.0"
import asyncio
from backend.database.connection import engine
from backend.database.models import Base

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init())
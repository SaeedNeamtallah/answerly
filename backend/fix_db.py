import asyncio
import logging

from backend.database.connection import engine
from backend.database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    try:
        async with engine.begin() as conn:
            logger.info("Creating all tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Done creating tables ✔")
    except Exception as e:
        logger.error(f"DB init failed: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
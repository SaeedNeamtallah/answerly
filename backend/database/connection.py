"""
Database connection management with async SQLAlchemy.
Provides engine and session factory.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

# ------------------------
# Create async engine
# ------------------------
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True
)

# ------------------------
# Create async session factory
# ------------------------
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# ------------------------
# DB Dependency (IMPORTANT)
# ------------------------
async def get_db() -> AsyncSession:
    """
    FastAPI dependency to get DB session
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ------------------------
# Initialize DB
# ------------------------
async def init_db():
    """Initialize database - create tables if they don't exist."""
    from backend.database.models import Base
    from sqlalchemy import text

    try:
        async with engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            # Create tables
            await conn.run_sync(Base.metadata.create_all)

            logger.info("Database initialized successfully with pgvector")

    except Exception as e:
        logger.warning(f"Could not initialize pgvector extension: {str(e)}")

        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables initialized (fallback)")
        except Exception as e2:
            logger.error(f"Failed to initialize database tables: {str(e2)}")

# ------------------------
# Close DB
# ------------------------
async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")

# ------------------------
# For Monitoring
# ------------------------
def get_db_pool():
    """
    Return session maker (used in metrics)
    """
    return async_session_maker
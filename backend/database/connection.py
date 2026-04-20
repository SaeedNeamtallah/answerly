"""
Database connection management with async SQLAlchemy.
Provides engine and session factory.
"""
import asyncio
from pathlib import Path
from typing import AsyncGenerator

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_timeout=30,
    future=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    Use with FastAPI Depends().
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


async def init_db():
    """Initialize database extensions and apply Alembic migrations."""
    from sqlalchemy import text

    def run_alembic_upgrade() -> None:
        project_root = Path(__file__).resolve().parents[2]
        alembic_cfg = Config(str(project_root / "backend" / "alembic" / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(project_root / "backend" / "alembic"))
        command.upgrade(alembic_cfg, "head")

    try:
        async with engine.begin() as conn:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("pgvector extension is available")
            except Exception as ext_error:
                logger.warning(f"Could not initialize pgvector extension: {str(ext_error)}")
    except Exception as e:
        logger.warning(f"Could not open database connection for extension setup: {str(e)}")

    try:
        await asyncio.to_thread(run_alembic_upgrade)
        logger.info("Database schema is up to date via Alembic")
    except Exception as migration_error:
        logger.error(f"Failed to apply Alembic migrations: {str(migration_error)}")
        raise


async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")

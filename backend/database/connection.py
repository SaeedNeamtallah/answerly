
"""
Database connection management with async SQLAlchemy.
Provides engine and session factory.
"""
from typing import AsyncGenerator
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
    """Initialize database - create tables if they don't exist."""
    from backend.database.models import Base
    from sqlalchemy import text

    async def ensure_projects_owner_id_schema(conn):
        """Backfill legacy schemas that predate multi-user owner_id on projects."""
        # Ensure owner_id column exists on legacy databases.
        await conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS owner_id INTEGER"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_owner_id ON projects(owner_id)"))

        # Pick a fallback owner for legacy rows without ownership data.
        fallback_owner_id = (
            await conn.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
        ).scalar_one_or_none()

        if fallback_owner_id is None:
            await conn.execute(
                text(
                    """
                    INSERT INTO users (username, hashed_password)
                    VALUES ('__migration_owner__', '__disabled__')
                    ON CONFLICT (username) DO NOTHING
                    """
                )
            )
            fallback_owner_id = (
                await conn.execute(
                    text("SELECT id FROM users WHERE username = '__migration_owner__' LIMIT 1")
                )
            ).scalar_one()

        await conn.execute(
            text("UPDATE projects SET owner_id = :owner_id WHERE owner_id IS NULL"),
            {"owner_id": fallback_owner_id},
        )

        # Ensure FK exists even for old schemas.
        await conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'fk_projects_owner_id_users'
                    ) THEN
                        ALTER TABLE projects
                        ADD CONSTRAINT fk_projects_owner_id_users
                        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
                    END IF;
                END;
                $$;
                """
            )
        )

        # Enforce non-null ownership after backfill.
        await conn.execute(text("ALTER TABLE projects ALTER COLUMN owner_id SET NOT NULL"))

    try:
        async with engine.begin() as conn:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            await ensure_projects_owner_id_schema(conn)
            logger.info("Database initialized successfully with pgvector")
    except Exception as e:
        logger.warning(f"Could not initialize pgvector extension: {str(e)}")
        logger.info("Attempting to initialize other tables...")
        try:
            async with engine.begin() as conn:
                # Try to create tables one by one or skip those that fail
                await conn.run_sync(Base.metadata.create_all)
                await ensure_projects_owner_id_schema(conn)
                logger.info("Database tables initialized (some might have failed)")
        except Exception as e2:
            logger.error(f"Failed to initialize database tables: {str(e2)}")


async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")

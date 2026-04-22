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

    async def ensure_user_account_status_schema(conn):
        """Backfill user account status column for legacy user tables."""
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(32)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS status_reason VARCHAR(255)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMPTZ"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended_until TIMESTAMPTZ"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS status_changed_by VARCHAR(64)"))

        # Legacy compatibility: keep data from previous temporary-suspension column if present.
        await conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'users'
                          AND column_name = 'suspension_expires_at'
                    ) THEN
                        UPDATE users
                        SET suspended_until = suspension_expires_at
                        WHERE suspended_until IS NULL
                          AND suspension_expires_at IS NOT NULL;
                    END IF;
                END;
                $$;
                """
            )
        )

        await conn.execute(text("UPDATE users SET status = 'ACTIVE' WHERE status IS NULL OR BTRIM(CAST(status AS TEXT)) = ''"))
        await conn.execute(text("UPDATE users SET status = UPPER(CAST(status AS TEXT))"))
        await conn.execute(
            text(
                """
                UPDATE users
                SET status = 'ACTIVE'
                WHERE status NOT IN ('ACTIVE', 'BLOCKED', 'SUSPENDED')
                """
            )
        )
        await conn.execute(text("ALTER TABLE users ALTER COLUMN status TYPE VARCHAR(32) USING UPPER(CAST(status AS TEXT))"))
        await conn.execute(text("ALTER TABLE users ALTER COLUMN status SET DEFAULT 'ACTIVE'"))
        await conn.execute(text("ALTER TABLE users ALTER COLUMN status SET NOT NULL"))
        await conn.execute(text("UPDATE users SET status_updated_at = NOW() WHERE status_updated_at IS NULL"))
        await conn.execute(text("ALTER TABLE users ALTER COLUMN status_updated_at SET DEFAULT NOW()"))
        await conn.execute(text("ALTER TABLE users ALTER COLUMN status_updated_at SET NOT NULL"))

        # Keep semantic consistency: ACTIVE/BLOCKED should not have temporary suspension expiry.
        await conn.execute(text("UPDATE users SET suspended_until = NULL WHERE status IN ('ACTIVE', 'BLOCKED')"))

        # Ensure legacy suspended users receive temporary-expiry semantics.
        await conn.execute(
            text(
                """
                UPDATE users
                SET suspended_until = NOW() + make_interval(mins => :minutes)
                WHERE status = 'SUSPENDED' AND suspended_until IS NULL
                """
            ),
            {"minutes": max(1, int(settings.security_user_suspension_default_minutes))},
        )

        await conn.execute(
            text(
                """
                UPDATE users
                SET status_reason = 'legacy_migration'
                WHERE status_reason IS NULL AND status IN ('SUSPENDED', 'BLOCKED')
                """
            )
        )
        await conn.execute(
            text(
                """
                UPDATE users
                SET status_changed_by = 'system'
                WHERE status_changed_by IS NULL AND status IN ('SUSPENDED', 'BLOCKED')
                """
            )
        )

        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_status ON users(status)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_suspended_until ON users(suspended_until)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_status_changed_by ON users(status_changed_by)"))

    async def ensure_incident_schema(conn):
        """Backfill incident schema changes for older iterations."""
        await conn.execute(
            text(
                """
                DO $$
                DECLARE
                    fk_name TEXT;
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'incidents'
                          AND column_name = 'created_by'
                    ) THEN
                        SELECT tc.constraint_name
                        INTO fk_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON tc.constraint_name = kcu.constraint_name
                         AND tc.table_schema = kcu.table_schema
                        WHERE tc.table_schema = 'public'
                          AND tc.table_name = 'incidents'
                          AND tc.constraint_type = 'FOREIGN KEY'
                          AND kcu.column_name = 'created_by'
                        LIMIT 1;

                        IF fk_name IS NOT NULL THEN
                            EXECUTE format('ALTER TABLE incidents DROP CONSTRAINT %I', fk_name);
                        END IF;

                        BEGIN
                            ALTER TABLE incidents
                            ALTER COLUMN created_by TYPE VARCHAR(64)
                            USING created_by::VARCHAR;
                        EXCEPTION WHEN others THEN
                            -- Keep initialization resilient for mixed legacy states.
                            NULL;
                        END;

                        ALTER TABLE incidents
                        ALTER COLUMN created_by SET DEFAULT 'system';
                    END IF;
                END;
                $$;
                """
            )
        )
        await conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = 'incidents'
                    ) THEN
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS notes TEXT;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS false_positive BOOLEAN;

                        UPDATE incidents
                        SET false_positive = FALSE
                        WHERE false_positive IS NULL;

                        ALTER TABLE incidents
                        ALTER COLUMN false_positive SET DEFAULT FALSE;

                        ALTER TABLE incidents
                        ALTER COLUMN false_positive SET NOT NULL;

                        CREATE INDEX IF NOT EXISTS ix_incidents_false_positive ON incidents(false_positive);
                    END IF;
                END;
                $$;
                """
            )
        )

    async def ensure_audit_log_schema(conn):
        """Backfill audit log schema for evolving incident response actions."""
        await conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = 'audit_logs'
                    ) THEN
                        ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS actor VARCHAR(64);
                        ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS target INTEGER;

                        UPDATE audit_logs
                        SET actor = 'security_engineer'
                        WHERE actor IS NULL OR BTRIM(actor) = '';

                        UPDATE audit_logs
                        SET target = target_user_id
                        WHERE target IS NULL AND target_user_id IS NOT NULL;

                        ALTER TABLE audit_logs
                        ALTER COLUMN actor SET DEFAULT 'security_engineer';

                        ALTER TABLE audit_logs
                        ALTER COLUMN actor SET NOT NULL;
                    END IF;
                END;
                $$;
                """
            )
        )

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

    # Keep startup resilient for legacy databases with partial historical schemas.
    try:
        async with engine.begin() as conn:
            await ensure_user_account_status_schema(conn)
            await ensure_incident_schema(conn)
            await ensure_audit_log_schema(conn)
            logger.info("Legacy security schema compatibility checks completed")
    except Exception as compatibility_error:
        logger.warning(f"Could not apply legacy compatibility schema checks: {str(compatibility_error)}")


async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")

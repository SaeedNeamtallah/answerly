"""
Database initialization script.
Creates database and tables with pgvector extension.
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy.engine import make_url

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import init_db
from backend.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    parsed_url = make_url(settings.database_url)
    db_name = parsed_url.database
    if not db_name:
        raise ValueError("DATABASE_URL must include a database name")

    connect_kwargs = {
        "dbname": "postgres",
        "host": parsed_url.host or "localhost",
        "port": parsed_url.port or 5432,
    }
    if parsed_url.username:
        connect_kwargs["user"] = parsed_url.username
    if parsed_url.password:
        connect_kwargs["password"] = parsed_url.password
    
    try:
        # Connect to default 'postgres' database
        conn = psycopg2.connect(**connect_kwargs)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()
        
        if not exists:
            logger.info(f"Creating database {db_name}...")
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            logger.info(f"Database {db_name} created successfully")
        else:
            logger.info(f"Database {db_name} already exists")
            
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        # We continue anyway, maybe it exists but we couldn't check


async def main():
    """Initialize database."""
    try:
        # Step 1: Create database if needed
        await create_database_if_not_exists()

        parsed_url = make_url(settings.database_url)
        target = f"{parsed_url.host or 'localhost'}:{parsed_url.port or 5432}/{parsed_url.database}"
        logger.info("Connecting to database: %s", target)
        
        # Step 2: Initialize tables and extensions
        await init_db()
        
        logger.info("✅ Database initialized successfully!")
        logger.info("Tables created:")
        logger.info("  - users")
        logger.info("  - projects")
        logger.info("  - assets")
        logger.info("  - chunks (with vector embeddings)")
        logger.info("Extensions enabled:")
        logger.info("  - pgvector")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        return 1
    
    finally:
        from backend.database import close_db
        await close_db()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

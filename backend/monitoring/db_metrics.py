"""
Database Metrics Collection for RAGMind
Safe version (no crashing if tables don't exist)
"""

import logging
from prometheus_client import Gauge
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ------------------------
# Prometheus Metrics
# ------------------------

DB_TABLE_COUNT = Gauge(
    "db_table_count",
    "Number of tables in database"
)

DB_ROW_COUNT = Gauge(
    "db_row_count",
    "Number of rows per table",
    ["table_name"]
)

# ------------------------
# Update Metrics
# ------------------------

async def update_db_metrics(async_session_maker):

    if async_session_maker is None:
        logger.warning("DB session maker is None")
        return

    try:
        async with async_session_maker() as session:  # type: AsyncSession

            # ✅ هات كل الجداول
            result = await session.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema='public'
                """)
            )

            tables = [row[0] for row in result.fetchall()]

            # ✅ عدد الجداول
            DB_TABLE_COUNT.set(len(tables))

            # ✅ عدد الصفوف لكل جدول
            for table in tables:
                try:
                    result_rows = await session.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    )
                    row_count = result_rows.scalar()
                    DB_ROW_COUNT.labels(table_name=table).set(row_count)

                except Exception as table_error:
                    logger.warning(f"Skipping table {table}: {table_error}")

    except Exception as e:
        logger.warning(f"DB metrics collection failed: {str(e)}")
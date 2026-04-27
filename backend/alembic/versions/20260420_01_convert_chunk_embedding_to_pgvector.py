"""convert chunk embedding column to native pgvector

Revision ID: 20260420_01
Revises: 20260416_01
Create Date: 2026-04-20
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260420_01"
down_revision: Union[str, None] = "20260416_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "chunks" not in inspector.get_table_names():
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    embedding_column = next(
        (column for column in inspector.get_columns("chunks") if column["name"] == "embedding"),
        None,
    )
    if embedding_column is None:
        return

    column_type = str(embedding_column["type"]).lower()
    if "vector" in column_type:
        return

    op.execute(
        """
        ALTER TABLE chunks
        ALTER COLUMN embedding TYPE vector
        USING (
            CASE
                WHEN embedding IS NULL THEN NULL
                ELSE embedding::text::vector
            END
        )
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "chunks" not in inspector.get_table_names():
        return

    embedding_column = next(
        (column for column in inspector.get_columns("chunks") if column["name"] == "embedding"),
        None,
    )
    if embedding_column is None:
        return

    column_type = str(embedding_column["type"]).lower()
    if "vector" not in column_type:
        return

    op.execute(
        """
        ALTER TABLE chunks
        ALTER COLUMN embedding TYPE json
        USING (
            CASE
                WHEN embedding IS NULL THEN NULL
                ELSE to_json(embedding::float8[])
            END
        )
        """
    )

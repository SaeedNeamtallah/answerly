"""add pgvector hnsw indexes for chunk embeddings

Revision ID: 20260420_02
Revises: 20260420_01
Create Date: 2026-04-20
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260420_02"
down_revision: Union[str, None] = "20260420_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_VECTOR_INDEX_PREFIX = "ix_chunks_embedding_hnsw_"
_HALFVEC_INDEX_PREFIX = "ix_chunks_embedding_hnsw_halfvec_"
_DEFAULT_DIMENSIONS = {768, 1024}
_MAX_HNSW_VECTOR_DIMENSIONS = 2000
_MAX_HNSW_HALFVEC_DIMENSIONS = 4000


def _index_spec_for_dimension(dimension: int) -> tuple[str, str, str]:
    dim = int(dimension)
    if dim <= _MAX_HNSW_VECTOR_DIMENSIONS:
        return f"{_VECTOR_INDEX_PREFIX}{dim}", "vector", "vector_cosine_ops"
    if dim <= _MAX_HNSW_HALFVEC_DIMENSIONS:
        return f"{_HALFVEC_INDEX_PREFIX}{dim}", "halfvec", "halfvec_cosine_ops"
    raise ValueError(f"HNSW index not supported for dimension {dim}")


def _create_index_sql(dimension: int) -> str:
    dim = int(dimension)
    if dim <= 0:
        raise ValueError("dimension must be positive")
    index_name, cast_type, opclass = _index_spec_for_dimension(dim)
    return f"""
    CREATE INDEX IF NOT EXISTS {index_name}
    ON chunks
    USING hnsw ((embedding::{cast_type}({dim})) {opclass})
    WHERE embedding IS NOT NULL AND vector_dims(embedding) = {dim}
    """


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "chunks" not in inspector.get_table_names():
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    dimensions = set(_DEFAULT_DIMENSIONS)
    result = bind.execute(
        sa.text(
            """
            SELECT DISTINCT vector_dims(embedding)
            FROM chunks
            WHERE embedding IS NOT NULL
            """
        )
    )
    for row in result:
        value = row[0]
        if value:
            dimensions.add(int(value))

    for dimension in sorted(dimensions):
        if int(dimension) > _MAX_HNSW_HALFVEC_DIMENSIONS:
            print(
                f"Skipping pgvector HNSW index for dimension {int(dimension)}; "
                f"supported ANN index dimensions are <= {_MAX_HNSW_HALFVEC_DIMENSIONS}."
            )
            continue
        op.execute(_create_index_sql(dimension))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "chunks" not in inspector.get_table_names():
        return

    result = bind.execute(
        sa.text(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = current_schema()
              AND tablename = 'chunks'
                            AND (
                                indexname LIKE :vector_prefix
                                OR indexname LIKE :halfvec_prefix
                            )
            """
        ),
                {
                        "vector_prefix": f"{_VECTOR_INDEX_PREFIX}%",
                        "halfvec_prefix": f"{_HALFVEC_INDEX_PREFIX}%",
                },
    )

    for row in result:
        index_name = row[0]
        if index_name:
            op.execute(f"DROP INDEX IF EXISTS {index_name}")

"""add telegram outbox claim lease

Revision ID: 20260501_01
Revises: 20260429_01
Create Date: 2026-05-01
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260501_01"
down_revision: Union[str, None] = "20260429_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column("delivery_claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_conversation_messages_delivery_claimed_at",
        "conversation_messages",
        ["delivery_claimed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_messages_delivery_claimed_at", table_name="conversation_messages")
    op.drop_column("conversation_messages", "delivery_claimed_at")

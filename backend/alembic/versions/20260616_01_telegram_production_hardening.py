"""telegram production hardening

Revision ID: 20260616_01
Revises: 20260501_01
Create Date: 2026-06-16
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260616_01"
down_revision: Union[str, None] = "20260501_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column("delivery_next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_conversation_messages_delivery_next_attempt_at",
        "conversation_messages",
        ["delivery_next_attempt_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_messages_delivery_next_attempt_at", table_name="conversation_messages")
    op.drop_column("conversation_messages", "delivery_next_attempt_at")

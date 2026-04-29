"""add delivery status to conversation messages

Revision ID: 20260429_01
Revises: 20260428_01
Create Date: 2026-04-29
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260429_01"
down_revision: Union[str, None] = "20260428_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column("delivery_status", sa.String(length=16), nullable=False, server_default="none"),
    )
    op.add_column(
        "conversation_messages",
        sa.Column("delivery_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_conversation_messages_delivery_status",
        "conversation_messages",
        ["delivery_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_messages_delivery_status", table_name="conversation_messages")
    op.drop_column("conversation_messages", "delivery_attempts")
    op.drop_column("conversation_messages", "delivery_status")


"""Harden persisted security events

Revision ID: 20260617_02
Revises: 3539647e7139
Create Date: 2026-06-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260617_02"
down_revision: Union[str, None] = "3539647e7139"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "security_events",
        sa.Column("is_simulation", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "security_events",
        sa.Column("delivery_status", sa.String(length=32), server_default="PENDING", nullable=False),
    )
    op.create_index("ix_security_events_is_simulation", "security_events", ["is_simulation"], unique=False)
    op.create_index("ix_security_events_delivery_status", "security_events", ["delivery_status"], unique=False)
    op.create_index("ix_security_events_severity_created", "security_events", ["severity", "created_at"], unique=False)
    op.create_index("ix_security_events_user_created", "security_events", ["user_id", "created_at"], unique=False)
    op.create_index("ix_security_events_simulation_created", "security_events", ["is_simulation", "created_at"], unique=False)
    op.create_index("ix_security_events_delivery_created", "security_events", ["delivery_status", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_security_events_delivery_created", table_name="security_events")
    op.drop_index("ix_security_events_simulation_created", table_name="security_events")
    op.drop_index("ix_security_events_user_created", table_name="security_events")
    op.drop_index("ix_security_events_severity_created", table_name="security_events")
    op.drop_index("ix_security_events_delivery_status", table_name="security_events")
    op.drop_index("ix_security_events_is_simulation", table_name="security_events")
    op.drop_column("security_events", "delivery_status")
    op.drop_column("security_events", "is_simulation")

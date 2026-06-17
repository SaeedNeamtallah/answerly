"""add google oauth to users

Revision ID: 20260617_01
Revises: 20260616_01
Create Date: 2026-06-17
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260617_01"
down_revision: Union[str, None] = "20260616_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("auth_provider", sa.String(length=50), server_default="local", nullable=False))
    op.add_column("users", sa.Column("google_id", sa.String(length=255), nullable=True))
    
    # 2. Make hashed_password nullable
    op.alter_column("users", "hashed_password", existing_type=sa.String(length=255), nullable=True)
    
    # 3. Create indexes
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)


def downgrade() -> None:
    # 1. Drop indexes
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    
    # 2. Make hashed_password not null
    op.alter_column("users", "hashed_password", existing_type=sa.String(length=255), nullable=False)
    
    # 3. Drop columns
    op.drop_column("users", "google_id")
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "email")

"""add users table and project ownership

Revision ID: 20260416_01
Revises:
Create Date: 2026-04-16
"""

from __future__ import annotations

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = "20260416_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _index_exists(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def _fk_exists(inspector: sa.Inspector, table_name: str, fk_name: str) -> bool:
    return any(fk.get("name") == fk_name for fk in inspector.get_foreign_keys(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "users"):
        op.create_table(
            "users",
            sa.Column("user_id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_uuid", sa.String(length=36), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False, server_default=sa.text("'user'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("email", name="uq_users_email"),
            sa.UniqueConstraint("user_uuid", name="uq_users_user_uuid"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=False)
        op.create_index("ix_users_user_uuid", "users", ["user_uuid"], unique=False)

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "projects") and not _column_exists(inspector, "projects", "user_id"):
        op.add_column("projects", sa.Column("user_id", sa.Integer(), nullable=True))

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "projects"):
        if not _index_exists(inspector, "projects", "ix_projects_user_id"):
            op.create_index("ix_projects_user_id", "projects", ["user_id"], unique=False)

        inspector = sa.inspect(bind)
        if not _fk_exists(inspector, "projects", "fk_projects_user_id_users"):
            op.create_foreign_key(
                "fk_projects_user_id_users",
                "projects",
                "users",
                ["user_id"],
                ["user_id"],
                ondelete="CASCADE",
            )

        null_count = bind.execute(sa.text("SELECT COUNT(*) FROM projects WHERE user_id IS NULL")).scalar() or 0
        if null_count > 0:
            default_user_id = bind.execute(
                sa.text(
                    """
                    INSERT INTO users (user_uuid, email, password_hash, role)
                    VALUES (:user_uuid, :email, :password_hash, :role)
                    ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                    RETURNING user_id
                    """
                ),
                {
                    "user_uuid": str(uuid.uuid4()),
                    "email": "legacy_owner@ragmind.local",
                    "password_hash": "MIGRATION_ONLY_SET_REAL_PASSWORD",
                    "role": "admin",
                },
            ).scalar()

            bind.execute(
                sa.text("UPDATE projects SET user_id = :user_id WHERE user_id IS NULL"),
                {"user_id": int(default_user_id)},
            )

        inspector = sa.inspect(bind)
        user_id_col = next((col for col in inspector.get_columns("projects") if col["name"] == "user_id"), None)
        if user_id_col and user_id_col.get("nullable", True):
            op.alter_column("projects", "user_id", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "projects") and _fk_exists(inspector, "projects", "fk_projects_user_id_users"):
        op.drop_constraint("fk_projects_user_id_users", "projects", type_="foreignkey")

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "projects") and _index_exists(inspector, "projects", "ix_projects_user_id"):
        op.drop_index("ix_projects_user_id", table_name="projects")

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "projects") and _column_exists(inspector, "projects", "user_id"):
        op.drop_column("projects", "user_id")

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "users"):
        op.drop_table("users")

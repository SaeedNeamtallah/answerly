
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
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

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

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    if not _table_exists(inspector, "users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("username", sa.String(length=150), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_users_id", "users", ["id"], unique=False)
        op.create_index("ix_users_username", "users", ["username"], unique=True)
    else:
        user_columns = {col["name"] for col in inspector.get_columns("users")}
        with op.batch_alter_table("users") as batch_op:
            if "user_id" in user_columns and "id" not in user_columns:
                batch_op.alter_column("user_id", new_column_name="id", existing_type=sa.Integer())
            if "email" in user_columns and "username" not in user_columns:
                batch_op.alter_column("email", new_column_name="username", existing_type=sa.String(length=255))
            if "password_hash" in user_columns and "hashed_password" not in user_columns:
                batch_op.alter_column(
                    "password_hash",
                    new_column_name="hashed_password",
                    existing_type=sa.String(length=255),
                )
            if "created_at" not in user_columns:
                batch_op.add_column(
                    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"))
                )

        inspector = sa.inspect(bind)
        if not _index_exists(inspector, "users", "ix_users_id"):
            op.create_index("ix_users_id", "users", ["id"], unique=False)
        if not _index_exists(inspector, "users", "ix_users_username"):
            op.create_index("ix_users_username", "users", ["username"], unique=True)

    inspector = sa.inspect(bind)
    if not _table_exists(inspector, "projects"):
        op.create_table(
            "projects",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_projects_id", "projects", ["id"], unique=False)
        op.create_index("ix_projects_name", "projects", ["name"], unique=False)
        op.create_index("ix_projects_owner_id", "projects", ["owner_id"], unique=False)
    else:
        project_columns = {col["name"] for col in inspector.get_columns("projects")}
        with op.batch_alter_table("projects") as batch_op:
            if "user_id" in project_columns and "owner_id" not in project_columns:
                batch_op.alter_column("user_id", new_column_name="owner_id", existing_type=sa.Integer())
            if "owner_id" not in project_columns and "user_id" not in project_columns:
                batch_op.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))
            if "name" not in project_columns:
                batch_op.add_column(sa.Column("name", sa.String(length=255), nullable=False, server_default="Untitled"))
            if "description" not in project_columns:
                batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
            if "created_at" not in project_columns:
                batch_op.add_column(
                    sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()"))
                )
            if "updated_at" not in project_columns:
                batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
            if "metadata" not in project_columns:
                batch_op.add_column(sa.Column("metadata", sa.JSON(), nullable=True))

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "projects"):
        if not _index_exists(inspector, "projects", "ix_projects_id"):
            op.create_index("ix_projects_id", "projects", ["id"], unique=False)
        if not _index_exists(inspector, "projects", "ix_projects_name"):
            op.create_index("ix_projects_name", "projects", ["name"], unique=False)
        if not _index_exists(inspector, "projects", "ix_projects_owner_id"):
            op.create_index("ix_projects_owner_id", "projects", ["owner_id"], unique=False)

        inspector = sa.inspect(bind)
        if _fk_exists(inspector, "projects", "fk_projects_user_id_users"):
            op.drop_constraint("fk_projects_user_id_users", "projects", type_="foreignkey")

        inspector = sa.inspect(bind)
        if not _fk_exists(inspector, "projects", "fk_projects_owner_id_users"):
            op.create_foreign_key(
                "fk_projects_owner_id_users",
                "projects",
                "users",
                ["owner_id"],
                ["id"],
                ondelete="CASCADE",
            )

        null_count = bind.execute(sa.text("SELECT COUNT(*) FROM projects WHERE owner_id IS NULL")).scalar() or 0
        if null_count > 0:
            default_user_id = bind.execute(
                sa.text(
                    """
                    INSERT INTO users (username, hashed_password)
                    VALUES (:username, :hashed_password)
                    ON CONFLICT (username) DO UPDATE SET username = EXCLUDED.username
                    RETURNING id
                    """
                ),
                {
                    "username": "__migration_owner__",
                    "hashed_password": f"migration-only-{uuid.uuid4()}",
                },
            ).scalar()

            bind.execute(
                sa.text("UPDATE projects SET owner_id = :user_id WHERE owner_id IS NULL"),
                {"user_id": int(default_user_id)},
            )

        inspector = sa.inspect(bind)
        owner_id_col = next((col for col in inspector.get_columns("projects") if col["name"] == "owner_id"), None)
        if owner_id_col and owner_id_col.get("nullable", True):
            op.alter_column("projects", "owner_id", existing_type=sa.Integer(), nullable=False)

    inspector = sa.inspect(bind)
    if not _table_exists(inspector, "assets"):
        op.create_table(
            "assets",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("filename", sa.String(length=500), nullable=False),
            sa.Column("original_filename", sa.String(length=500), nullable=False),
            sa.Column("file_path", sa.String(length=1000), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("file_type", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=True, server_default="uploaded"),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_assets_id", "assets", ["id"], unique=False)
        op.create_index("ix_assets_project_status", "assets", ["project_id", "status"], unique=False)

    inspector = sa.inspect(bind)
    if not _table_exists(inspector, "chunks"):
        op.create_table(
            "chunks",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("asset_id", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("chunk_index", sa.Integer(), nullable=False),
            sa.Column("embedding", Vector(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_chunks_id", "chunks", ["id"], unique=False)
        op.create_index("ix_chunks_project_asset", "chunks", ["project_id", "asset_id"], unique=False)
        op.create_index("ix_chunks_asset_idx", "chunks", ["asset_id", "chunk_index"], unique=False)

    inspector = sa.inspect(bind)
    if not _table_exists(inspector, "celery_task_executions"):
        op.create_table(
            "celery_task_executions",
            sa.Column("execution_id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("task_name", sa.String(length=255), nullable=False),
            sa.Column("task_args_hash", sa.String(length=64), nullable=False),
            sa.Column("celery_task_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
            sa.Column("task_args", sa.JSON(), nullable=True),
            sa.Column("result", sa.JSON(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index(
            "ixz_task_name_args_celery_hash",
            "celery_task_executions",
            ["task_name", "task_args_hash", "celery_task_id"],
            unique=True,
        )
        op.create_index("ixz_task_execution_status", "celery_task_executions", ["status"], unique=False)
        op.create_index("ixz_task_execution_created_at", "celery_task_executions", ["created_at"], unique=False)
        op.create_index("ixz_celery_task_id", "celery_task_executions", ["celery_task_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "celery_task_executions"):
        for index_name in (
            "ixz_task_name_args_celery_hash",
            "ixz_task_execution_status",
            "ixz_task_execution_created_at",
            "ixz_celery_task_id",
        ):
            inspector = sa.inspect(bind)
            if _index_exists(inspector, "celery_task_executions", index_name):
                op.drop_index(index_name, table_name="celery_task_executions")
        op.drop_table("celery_task_executions")

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "chunks"):
        for index_name in ("ix_chunks_project_asset", "ix_chunks_asset_idx", "ix_chunks_id"):
            inspector = sa.inspect(bind)
            if _index_exists(inspector, "chunks", index_name):
                op.drop_index(index_name, table_name="chunks")
        op.drop_table("chunks")

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "assets"):
        for index_name in ("ix_assets_project_status", "ix_assets_id"):
            inspector = sa.inspect(bind)
            if _index_exists(inspector, "assets", index_name):
                op.drop_index(index_name, table_name="assets")
        op.drop_table("assets")

    if _table_exists(inspector, "projects") and _fk_exists(inspector, "projects", "fk_projects_owner_id_users"):
        op.drop_constraint("fk_projects_owner_id_users", "projects", type_="foreignkey")

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "projects"):
        for index_name in ("ix_projects_owner_id", "ix_projects_name", "ix_projects_id"):
            inspector = sa.inspect(bind)
            if _index_exists(inspector, "projects", index_name):
                op.drop_index(index_name, table_name="projects")

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "projects"):
        op.drop_table("projects")

    inspector = sa.inspect(bind)
    if _table_exists(inspector, "users"):
        for index_name in ("ix_users_username", "ix_users_id"):
            inspector = sa.inspect(bind)
            if _index_exists(inspector, "users", index_name):
                op.drop_index(index_name, table_name="users")
        op.drop_table("users")

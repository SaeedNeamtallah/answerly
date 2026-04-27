"""add b2b telegram saas tables

Revision ID: 20260427_01
Revises: 20260420_02
Create Date: 2026-04-27
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260427_01"
down_revision: Union[str, None] = "20260420_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    user_columns = {column["name"] for column in inspector.get_columns("users")} if "users" in tables else set()
    if "users" in tables and "role" not in user_columns:
        op.add_column(
            "users",
            sa.Column("role", sa.String(length=30), nullable=False, server_default="company_admin"),
        )
        op.create_index("ix_users_role", "users", ["role"])
    if "users" in tables and "company_name" not in user_columns:
        op.add_column("users", sa.Column("company_name", sa.String(length=255), nullable=True))
    if "users" in tables and "company_website" not in user_columns:
        op.add_column("users", sa.Column("company_website", sa.String(length=500), nullable=True))

    if "bot_integrations" not in tables:
        op.create_table(
            "bot_integrations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("telegram_bot_id", sa.String(length=64), nullable=False),
            sa.Column("telegram_username", sa.String(length=120), nullable=True),
            sa.Column("token_encrypted", sa.Text(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("webhook_secret", sa.String(length=160), nullable=False),
            sa.Column("webhook_url", sa.String(length=1000), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("show_sources_to_customer", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("human_handoff_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("fallback_message", sa.Text(), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("last_update_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by_user_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash"),
            sa.UniqueConstraint("webhook_secret"),
        )
        op.create_index("ix_bot_integrations_id", "bot_integrations", ["id"])
        op.create_index("ix_bot_integrations_owner_id", "bot_integrations", ["owner_id"])
        op.create_index("ix_bot_integrations_project_id", "bot_integrations", ["project_id"])
        op.create_index("ix_bot_integrations_telegram_bot_id", "bot_integrations", ["telegram_bot_id"])
        op.create_index("ix_bot_integrations_telegram_username", "bot_integrations", ["telegram_username"])
        op.create_index("ix_bot_integrations_token_hash", "bot_integrations", ["token_hash"], unique=True)
        op.create_index("ix_bot_integrations_webhook_secret", "bot_integrations", ["webhook_secret"], unique=True)
        op.create_index("ix_bot_integrations_owner_project", "bot_integrations", ["owner_id", "project_id"])
        op.create_index("ix_bot_integrations_owner_status", "bot_integrations", ["owner_id", "status"])

    if "telegram_customers" not in tables:
        op.create_table(
            "telegram_customers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column("bot_integration_id", sa.Integer(), nullable=False),
            sa.Column("telegram_user_id", sa.String(length=64), nullable=True),
            sa.Column("chat_id", sa.String(length=64), nullable=False),
            sa.Column("username", sa.String(length=120), nullable=True),
            sa.Column("first_name", sa.String(length=120), nullable=True),
            sa.Column("last_name", sa.String(length=120), nullable=True),
            sa.Column("language_code", sa.String(length=16), nullable=True),
            sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["bot_integration_id"], ["bot_integrations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_telegram_customers_id", "telegram_customers", ["id"])
        op.create_index("ix_telegram_customers_owner_id", "telegram_customers", ["owner_id"])
        op.create_index("ix_telegram_customers_bot_integration_id", "telegram_customers", ["bot_integration_id"])
        op.create_index("ix_telegram_customers_telegram_user_id", "telegram_customers", ["telegram_user_id"])
        op.create_index("ix_telegram_customers_chat_id", "telegram_customers", ["chat_id"])
        op.create_index("ix_telegram_customers_is_blocked", "telegram_customers", ["is_blocked"])
        op.create_index("ix_telegram_customers_bot_chat", "telegram_customers", ["bot_integration_id", "chat_id"], unique=True)
        op.create_index("ix_telegram_customers_owner_bot", "telegram_customers", ["owner_id", "bot_integration_id"])

    if "conversations" not in tables:
        op.create_table(
            "conversations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column("bot_integration_id", sa.Integer(), nullable=False),
            sa.Column("telegram_customer_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
            sa.Column("needs_human", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
            sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["bot_integration_id"], ["bot_integrations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["telegram_customer_id"], ["telegram_customers.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_conversations_id", "conversations", ["id"])
        op.create_index("ix_conversations_owner_id", "conversations", ["owner_id"])
        op.create_index("ix_conversations_bot_integration_id", "conversations", ["bot_integration_id"])
        op.create_index("ix_conversations_telegram_customer_id", "conversations", ["telegram_customer_id"])
        op.create_index("ix_conversations_project_id", "conversations", ["project_id"])
        op.create_index("ix_conversations_status", "conversations", ["status"])
        op.create_index("ix_conversations_needs_human", "conversations", ["needs_human"])
        op.create_index("ix_conversations_assigned_to_user_id", "conversations", ["assigned_to_user_id"])
        op.create_index("ix_conversations_last_message_at", "conversations", ["last_message_at"])
        op.create_index("ix_conversations_owner_status", "conversations", ["owner_id", "status"])
        op.create_index("ix_conversations_bot_customer_status", "conversations", ["bot_integration_id", "telegram_customer_id", "status"])

    if "conversation_messages" not in tables:
        op.create_table(
            "conversation_messages",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("owner_id", sa.Integer(), nullable=False),
            sa.Column("bot_integration_id", sa.Integer(), nullable=False),
            sa.Column("conversation_id", sa.Integer(), nullable=False),
            sa.Column("telegram_customer_id", sa.Integer(), nullable=True),
            sa.Column("sender_type", sa.String(length=32), nullable=False),
            sa.Column("agent_user_id", sa.Integer(), nullable=True),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("telegram_update_id", sa.String(length=64), nullable=True),
            sa.Column("telegram_message_id", sa.String(length=64), nullable=True),
            sa.Column("answer_sources_json", sa.JSON(), nullable=True),
            sa.Column("retrieval_metadata_json", sa.JSON(), nullable=True),
            sa.Column("raw_payload_json", sa.JSON(), nullable=True),
            sa.Column("raw_payload_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["agent_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["bot_integration_id"], ["bot_integrations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["telegram_customer_id"], ["telegram_customers.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_conversation_messages_id", "conversation_messages", ["id"])
        op.create_index("ix_conversation_messages_owner_id", "conversation_messages", ["owner_id"])
        op.create_index("ix_conversation_messages_bot_integration_id", "conversation_messages", ["bot_integration_id"])
        op.create_index("ix_conversation_messages_conversation_id", "conversation_messages", ["conversation_id"])
        op.create_index("ix_conversation_messages_telegram_customer_id", "conversation_messages", ["telegram_customer_id"])
        op.create_index("ix_conversation_messages_sender_type", "conversation_messages", ["sender_type"])
        op.create_index("ix_conversation_messages_agent_user_id", "conversation_messages", ["agent_user_id"])
        op.create_index("ix_conversation_messages_telegram_update_id", "conversation_messages", ["telegram_update_id"])
        op.create_index("ix_conversation_messages_telegram_message_id", "conversation_messages", ["telegram_message_id"])
        op.create_index("ix_conversation_messages_raw_payload_expires_at", "conversation_messages", ["raw_payload_expires_at"])
        op.create_index("ix_conversation_messages_created_at", "conversation_messages", ["created_at"])
        op.create_index("ix_conversation_messages_conversation_created", "conversation_messages", ["conversation_id", "created_at"])
        op.create_index("ix_conversation_messages_update_unique", "conversation_messages", ["bot_integration_id", "telegram_update_id"], unique=True)
        op.create_index("ix_conversation_messages_message_unique", "conversation_messages", ["bot_integration_id", "telegram_customer_id", "telegram_message_id"], unique=True)
        op.create_index("ix_conversation_messages_owner_sender", "conversation_messages", ["owner_id", "sender_type"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "conversation_messages" in tables:
        op.drop_table("conversation_messages")
    if "conversations" in tables:
        op.drop_table("conversations")
    if "telegram_customers" in tables:
        op.drop_table("telegram_customers")
    if "bot_integrations" in tables:
        op.drop_table("bot_integrations")

    user_columns = {column["name"] for column in inspector.get_columns("users")} if "users" in tables else set()
    if "users" in tables and "company_website" in user_columns:
        op.drop_column("users", "company_website")
    if "users" in tables and "company_name" in user_columns:
        op.drop_column("users", "company_name")
    if "users" in tables and "role" in user_columns:
        op.drop_index("ix_users_role", table_name="users")
        op.drop_column("users", "role")

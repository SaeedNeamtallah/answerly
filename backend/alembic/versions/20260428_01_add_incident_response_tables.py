"""add incident response tables

Revision ID: 20260428_01
Revises: 20260427_01
Create Date: 2026-04-28
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260428_01"
down_revision: Union[str, None] = "20260427_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "incidents" not in tables:
        op.create_table(
            "incidents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("type", sa.String(length=120), nullable=False),
            sa.Column(
                "severity",
                sa.Enum("LOW", "MEDIUM", "HIGH", name="incident_severity", native_enum=False),
                nullable=False,
                server_default="MEDIUM",
            ),
            sa.Column(
                "status",
                sa.Enum("OPEN", "INVESTIGATING", "RESOLVED", "CLOSED", name="incident_status", native_enum=False),
                nullable=False,
                server_default="OPEN",
            ),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.String(length=64), nullable=True, server_default="system"),
            sa.Column("assigned_to", sa.Integer(), nullable=True),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True, server_default=""),
            sa.Column("false_positive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_incidents_id", "incidents", ["id"])
        op.create_index("ix_incidents_type", "incidents", ["type"])
        op.create_index("ix_incidents_status", "incidents", ["status"])
        op.create_index("ix_incidents_actor_id", "incidents", ["actor_id"])
        op.create_index("ix_incidents_created_by", "incidents", ["created_by"])
        op.create_index("ix_incidents_assigned_to", "incidents", ["assigned_to"])
        op.create_index("ix_incidents_false_positive", "incidents", ["false_positive"])
        op.create_index("ix_incidents_status_severity", "incidents", ["status", "severity"])
        op.create_index("ix_incidents_created_at", "incidents", ["created_at"])

    if "incident_logs" not in tables:
        op.create_table(
            "incident_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("incident_id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("severity", sa.String(length=16), nullable=True),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_incident_logs_id", "incident_logs", ["id"])
        op.create_index("ix_incident_logs_incident_id", "incident_logs", ["incident_id"])
        op.create_index("ix_incident_logs_event_type", "incident_logs", ["event_type"])
        op.create_index("ix_incident_logs_actor_id", "incident_logs", ["actor_id"])
        op.create_index("ix_incident_logs_incident_created", "incident_logs", ["incident_id", "created_at"])

    if "audit_logs" not in tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("actor", sa.String(length=64), nullable=False, server_default="security_engineer"),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("target", sa.Integer(), nullable=True),
            sa.Column("target_user_id", sa.Integer(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
        op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
        op.create_index("ix_audit_logs_actor", "audit_logs", ["actor"])
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
        op.create_index("ix_audit_logs_target", "audit_logs", ["target"])
        op.create_index("ix_audit_logs_target_user_id", "audit_logs", ["target_user_id"])
        op.create_index("ix_audit_logs_action_created", "audit_logs", ["action", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_target_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_target", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_incident_logs_incident_created", table_name="incident_logs")
    op.drop_index("ix_incident_logs_actor_id", table_name="incident_logs")
    op.drop_index("ix_incident_logs_event_type", table_name="incident_logs")
    op.drop_index("ix_incident_logs_incident_id", table_name="incident_logs")
    op.drop_index("ix_incident_logs_id", table_name="incident_logs")
    op.drop_table("incident_logs")

    op.drop_index("ix_incidents_created_at", table_name="incidents")
    op.drop_index("ix_incidents_status_severity", table_name="incidents")
    op.drop_index("ix_incidents_false_positive", table_name="incidents")
    op.drop_index("ix_incidents_assigned_to", table_name="incidents")
    op.drop_index("ix_incidents_created_by", table_name="incidents")
    op.drop_index("ix_incidents_actor_id", table_name="incidents")
    op.drop_index("ix_incidents_status", table_name="incidents")
    op.drop_index("ix_incidents_type", table_name="incidents")
    op.drop_index("ix_incidents_id", table_name="incidents")
    op.drop_table("incidents")

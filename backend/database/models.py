"""
Database models using SQLAlchemy async ORM.
Defines tables for users, projects, assets, and chunks with vector embeddings.
"""
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, LargeBinary, Index, Boolean, Enum as SAEnum
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid


Base = declarative_base()


class IncidentSeverity(str, PyEnum):
    """Supported incident severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class IncidentStatus(str, PyEnum):
    """Supported incident lifecycle states."""

    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class UserAccountStatus(str, PyEnum):
    """Supported user account states for security actions."""

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    SUSPENDED = "SUSPENDED"


class UserRole(str, PyEnum):
    """Product roles for dashboard and platform-owner access."""

    PLATFORM_OWNER = "platform_owner"
    COMPANY_ADMIN = "company_admin"


class User(Base):
    """Application user model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default=UserRole.COMPANY_ADMIN.value, server_default=UserRole.COMPANY_ADMIN.value, index=True)
    company_name = Column(String(255), nullable=True)
    company_website = Column(String(500), nullable=True)
    status = Column(
        SAEnum(UserAccountStatus, name="user_account_status", native_enum=False),
        nullable=False,
        default=UserAccountStatus.ACTIVE,
        index=True,
    )
    status_reason = Column(String(255), nullable=True)
    status_updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    suspended_until = Column(DateTime(timezone=True), nullable=True, index=True)
    status_changed_by = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    bot_integrations = relationship("BotIntegration", foreign_keys="BotIntegration.owner_id", back_populates="owner", cascade="all, delete-orphan")
    created_bot_integrations = relationship("BotIntegration", foreign_keys="BotIntegration.created_by_user_id", back_populates="created_by_user")
    telegram_customers = relationship("TelegramCustomer", back_populates="owner", cascade="all, delete-orphan")
    conversations = relationship("Conversation", foreign_keys="Conversation.owner_id", back_populates="owner", cascade="all, delete-orphan")
    assigned_conversations = relationship("Conversation", foreign_keys="Conversation.assigned_to_user_id", back_populates="assigned_to_user")
    conversation_messages = relationship("ConversationMessage", foreign_keys="ConversationMessage.owner_id", back_populates="owner", cascade="all, delete-orphan")
    agent_conversation_messages = relationship("ConversationMessage", foreign_keys="ConversationMessage.agent_user_id", back_populates="agent_user")
    caused_incidents = relationship("Incident", foreign_keys="Incident.actor_id", back_populates="actor")
    assigned_incidents = relationship("Incident", foreign_keys="Incident.assigned_to", back_populates="assignee")
    incident_logs = relationship("IncidentLog", back_populates="actor")
    performed_audit_logs = relationship("AuditLog", foreign_keys="AuditLog.actor_id", back_populates="actor_user")
    targeted_audit_logs = relationship("AuditLog", foreign_keys="AuditLog.target_user_id", back_populates="target_user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Project(Base):
    """Project model for organizing documents."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Metadata (renamed to avoid conflict with SQLAlchemy metadata)
    extra_metadata = Column("metadata", JSON, default={})
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="project", cascade="all, delete-orphan")
    bot_integrations = relationship("BotIntegration", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, owner_id={self.owner_id}, name='{self.name}')>"


class Asset(Base):
    """Asset model for uploaded documents."""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # File information
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_type = Column(String(50), nullable=False)  # pdf, txt, docx
    
    # Status
    status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata (renamed to avoid conflict)
    extra_metadata = Column("metadata", JSON, default={})
    
    # Relationships
    project = relationship("Project", back_populates="assets")
    chunks = relationship("Chunk", back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_assets_project_status', 'project_id', 'status'),
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class Chunk(Base):
    """Chunk model for text chunks with vector embeddings."""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Position in document
    
    # Native pgvector column. Dimension is left flexible to support multiple embedding providers.
    embedding = Column(Vector(), nullable=True)
    
    # Metadata (renamed to avoid conflict)
    extra_metadata = Column("metadata", JSON, default={})  # page_number, section, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="chunks")
    asset = relationship("Asset", back_populates="chunks")

    __table_args__ = (
        Index('ix_chunks_project_asset', 'project_id', 'asset_id'),
        Index('ix_chunks_asset_idx', 'asset_id', 'chunk_index'),
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, asset_id={self.asset_id}, chunk_index={self.chunk_index})>"


class BotIntegration(Base):
    """Database-backed Telegram bot integration owned by a company user."""

    __tablename__ = "bot_integrations"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    telegram_bot_id = Column(String(64), nullable=False, index=True)
    telegram_username = Column(String(120), nullable=True, index=True)
    token_encrypted = Column(Text, nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    webhook_secret = Column(String(160), nullable=False, unique=True, index=True)
    webhook_url = Column(String(1000), nullable=True)
    status = Column(String(32), nullable=False, default="active", server_default="active", index=True)
    show_sources_to_customer = Column(Boolean, nullable=False, default=False, server_default="false")
    human_handoff_enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    fallback_message = Column(Text, nullable=True)
    last_error = Column(Text, nullable=True)
    last_update_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="bot_integrations")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_bot_integrations")
    project = relationship("Project", back_populates="bot_integrations")
    customers = relationship("TelegramCustomer", back_populates="bot_integration", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="bot_integration", cascade="all, delete-orphan")
    messages = relationship("ConversationMessage", back_populates="bot_integration", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_bot_integrations_owner_project", "owner_id", "project_id"),
        Index("ix_bot_integrations_owner_status", "owner_id", "status"),
    )

    def __repr__(self):
        return f"<BotIntegration(id={self.id}, owner_id={self.owner_id}, project_id={self.project_id}, status='{self.status}')>"


class TelegramCustomer(Base):
    """External Telegram user scoped to a single bot integration."""

    __tablename__ = "telegram_customers"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bot_integration_id = Column(Integer, ForeignKey("bot_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_user_id = Column(String(64), nullable=True, index=True)
    chat_id = Column(String(64), nullable=False, index=True)
    username = Column(String(120), nullable=True)
    first_name = Column(String(120), nullable=True)
    last_name = Column(String(120), nullable=True)
    language_code = Column(String(16), nullable=True)
    is_blocked = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="telegram_customers")
    bot_integration = relationship("BotIntegration", back_populates="customers")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_telegram_customers_bot_chat", "bot_integration_id", "chat_id", unique=True),
        Index("ix_telegram_customers_owner_bot", "owner_id", "bot_integration_id"),
    )

    def __repr__(self):
        return f"<TelegramCustomer(id={self.id}, bot_integration_id={self.bot_integration_id}, chat_id='{self.chat_id}')>"


class Conversation(Base):
    """Durable customer-support conversation for a Telegram customer."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bot_integration_id = Column(Integer, ForeignKey("bot_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_customer_id = Column(Integer, ForeignKey("telegram_customers.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="open", server_default="open", index=True)
    needs_human = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="conversations")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id], back_populates="assigned_conversations")
    bot_integration = relationship("BotIntegration", back_populates="conversations")
    customer = relationship("TelegramCustomer", back_populates="conversations")
    project = relationship("Project")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.created_at")

    __table_args__ = (
        Index("ix_conversations_owner_status", "owner_id", "status"),
        Index("ix_conversations_bot_customer_status", "bot_integration_id", "telegram_customer_id", "status"),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, owner_id={self.owner_id}, status='{self.status}')>"


class ConversationMessage(Base):
    """Stored support message with optional internal retrieval metadata."""

    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bot_integration_id = Column(Integer, ForeignKey("bot_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_customer_id = Column(Integer, ForeignKey("telegram_customers.id", ondelete="CASCADE"), nullable=True, index=True)
    sender_type = Column(String(32), nullable=False, index=True)
    agent_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    text = Column(Text, nullable=False)
    telegram_update_id = Column(String(64), nullable=True, index=True)
    telegram_message_id = Column(String(64), nullable=True, index=True)
    answer_sources_json = Column(JSON, nullable=True)
    retrieval_metadata_json = Column(JSON, nullable=True)
    raw_payload_json = Column(JSON, nullable=True)
    raw_payload_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    delivery_status = Column(
        String(16),
        nullable=False,
        default="none",
        server_default="none",
        index=True,
    )
    delivery_attempts = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    delivery_claimed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    delivery_next_attempt_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="conversation_messages")
    agent_user = relationship("User", foreign_keys=[agent_user_id], back_populates="agent_conversation_messages")
    bot_integration = relationship("BotIntegration", back_populates="messages")
    conversation = relationship("Conversation", back_populates="messages")
    customer = relationship("TelegramCustomer")

    __table_args__ = (
        Index("ix_conversation_messages_conversation_created", "conversation_id", "created_at"),
        Index("ix_conversation_messages_update_unique", "bot_integration_id", "telegram_update_id", unique=True),
        Index("ix_conversation_messages_message_unique", "bot_integration_id", "telegram_customer_id", "telegram_message_id", unique=True),
        Index("ix_conversation_messages_owner_sender", "owner_id", "sender_type"),
        Index("ix_conversation_messages_delivery_next_attempt_at", "delivery_next_attempt_at"),
    )

    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, conversation_id={self.conversation_id}, sender_type='{self.sender_type}')>"


class CeleryTaskExecution(Base):
    """Track Celery task executions."""
    __tablename__ = "celery_task_executions"

    execution_id = Column(Integer, primary_key=True, autoincrement=True)

    task_name = Column(String(255), nullable=False)
    task_args_hash = Column(String(64), nullable=False)  # SHA-256 hash of task arguments
    celery_task_id = Column(UUID(as_uuid=True), nullable=True)

    status = Column(String(20), nullable=False, default="PENDING")

    task_args = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    __table_args__ = (
        Index("ixz_task_name_args_celery_hash", "task_name", "task_args_hash", "celery_task_id", unique=True),
        Index("ixz_task_execution_status", "status"),
        Index("ixz_task_execution_created_at", "created_at"),
        Index("ixz_celery_task_id", "celery_task_id"),
    )

    def __repr__(self):
        return f"<CeleryTaskExecution(execution_id={self.execution_id}, task_name='{self.task_name}', status='{self.status}')>"

class Incident(Base):
    """Incident model used for incident-response workflows."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(120), nullable=False, index=True)
    severity = Column(
        SAEnum(IncidentSeverity, name="incident_severity", native_enum=False),
        nullable=False,
        default=IncidentSeverity.MEDIUM,
    )
    status = Column(
        SAEnum(IncidentStatus, name="incident_status", native_enum=False),
        nullable=False,
        default=IncidentStatus.OPEN,
        index=True,
    )

    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by = Column(String(64), nullable=True, index=True, default="system")
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    description = Column(Text, nullable=False)
    notes = Column(Text, nullable=True, default="")
    false_positive = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    actor = relationship("User", foreign_keys=[actor_id], back_populates="caused_incidents")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_incidents")
    logs = relationship("IncidentLog", back_populates="incident", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_incidents_status_severity", "status", "severity"),
        Index("ix_incidents_created_at", "created_at"),
    )

    def __repr__(self):
        return (
            f"<Incident(id={self.id}, type='{self.type}', severity='{self.severity}', "
            f"status='{self.status}')>"
        )


class IncidentLog(Base):
    """Log/event entries linked to incidents (one incident -> many logs)."""

    __tablename__ = "incident_logs"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(16), nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    message = Column(Text, nullable=False)
    extra_metadata = Column("metadata", JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    incident = relationship("Incident", back_populates="logs")
    actor = relationship("User", back_populates="incident_logs")

    __table_args__ = (
        Index("ix_incident_logs_incident_created", "incident_id", "created_at"),
    )

    def __repr__(self):
        return f"<IncidentLog(id={self.id}, incident_id={self.incident_id}, event_type='{self.event_type}')>"


class AuditLog(Base):
    """Audit trail for security actions executed by SOC users."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor = Column(String(64), nullable=False, default="security_engineer", index=True)
    action = Column(String(64), nullable=False, index=True)
    target = Column(Integer, nullable=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    extra_metadata = Column("metadata", JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    actor_user = relationship("User", foreign_keys=[actor_id], back_populates="performed_audit_logs")
    target_user = relationship("User", foreign_keys=[target_user_id], back_populates="targeted_audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', target_user_id={self.target_user_id})>"

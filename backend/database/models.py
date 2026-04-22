"""
Database models using SQLAlchemy async ORM.
Defines tables for users, projects, assets, and chunks with vector embeddings.
"""
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, LargeBinary, Index, Boolean, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base
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


class User(Base):
    """Application user model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
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

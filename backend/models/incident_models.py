"""Pydantic models for incident API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.database.models import IncidentStatus


class IncidentStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: IncidentStatus
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentAssignResponse(BaseModel):
    id: int
    assigned_to: Optional[int] = None
    assigned_to_username: Optional[str] = None
    status: str


class IncidentActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: Literal["block_user", "suspend_user", "reactivate_user", "ignore"]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentNotesUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentFalsePositiveUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_false_positive: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentLogResponse(BaseModel):
    id: int
    incident_id: int
    event_type: str
    severity: Optional[str] = None
    result: Literal["success", "failed"]
    actor_id: Optional[int] = None
    actor_username: Optional[str] = None
    message: str
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class IncidentResponse(BaseModel):
    id: int
    type: str
    severity: str
    status: str
    actor_id: Optional[int] = None
    actor_username: Optional[str] = None
    created_by: Optional[str] = None
    assigned_to: Optional[int] = None
    assigned_to_username: Optional[str] = None
    description: str
    notes: str = ""
    is_false_positive: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class IncidentDetailsResponse(IncidentResponse):
    logs: List[IncidentLogResponse]

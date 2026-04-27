"""Admin-only user account status management endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.database.models import User, UserAccountStatus
from backend.security.auth import require_platform_owner_access
from backend.security.sanitization import sanitize_text
from backend.services.auth_service import AuthService
from backend.services.incident_management_service import IncidentManagementService


router = APIRouter(
    prefix="/admin/users",
    tags=["Admin"],
)


class AdminSuspendUserRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255)
    duration_minutes: int = Field(..., ge=1, le=10080)


class AdminBlockUserRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255)


class AdminUserStatusSnapshot(BaseModel):
    id: int
    username: str
    status: str
    status_reason: Optional[str] = None
    status_updated_at: Optional[datetime] = None
    suspended_until: Optional[datetime] = None
    status_changed_by: Optional[str] = None


class AdminUserStatusActionResponse(BaseModel):
    success: bool
    action: str
    message: str
    user: AdminUserStatusSnapshot


def _normalize_reason(reason: str) -> str:
    sanitized = sanitize_text(
        reason,
        max_length=255,
        strip_html=True,
        allow_newlines=False,
    ).strip()
    if len(sanitized) < 3:
        raise HTTPException(
            status_code=422,
            detail="reason must be at least 3 visible characters",
        )
    return sanitized


def _serialize_user_status(user: User) -> AdminUserStatusSnapshot:
    status_value = getattr(user, "status", UserAccountStatus.ACTIVE)
    if isinstance(status_value, UserAccountStatus):
        status_text = status_value.value
    else:
        status_text = str(status_value)

    return AdminUserStatusSnapshot(
        id=int(user.id),
        username=str(user.username),
        status=status_text,
        status_reason=getattr(user, "status_reason", None),
        status_updated_at=getattr(user, "status_updated_at", None),
        suspended_until=getattr(user, "suspended_until", None),
        status_changed_by=getattr(user, "status_changed_by", None),
    )


@router.post("/{user_id}/suspend", response_model=AdminUserStatusActionResponse)
async def admin_suspend_user(
    payload: AdminSuspendUserRequest,
    user_id: int = Path(..., gt=0),
    current_admin: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
    incident_management_service: IncidentManagementService = Depends(IncidentManagementService),
):
    """Suspend a user account for a bounded duration (admin only)."""
    reason = _normalize_reason(payload.reason)

    try:
        updated_user = await incident_management_service.suspend_user(
            user_id,
            reason,
            int(payload.duration_minutes),
            actor=current_admin.username,
            db=db,
            auth_service=auth_service,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc

    await db.commit()
    await db.refresh(updated_user)

    return AdminUserStatusActionResponse(
        success=True,
        action="suspend",
        message="User account suspended successfully",
        user=_serialize_user_status(updated_user),
    )


@router.post("/{user_id}/block", response_model=AdminUserStatusActionResponse)
async def admin_block_user(
    payload: AdminBlockUserRequest,
    user_id: int = Path(..., gt=0),
    current_admin: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
    incident_management_service: IncidentManagementService = Depends(IncidentManagementService),
):
    """Block a user account permanently (admin only)."""
    reason = _normalize_reason(payload.reason)

    try:
        updated_user = await incident_management_service.block_user(
            user_id,
            reason,
            actor=current_admin.username,
            db=db,
            auth_service=auth_service,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc

    await db.commit()
    await db.refresh(updated_user)

    return AdminUserStatusActionResponse(
        success=True,
        action="block",
        message="User account blocked successfully",
        user=_serialize_user_status(updated_user),
    )


@router.post("/{user_id}/restore", response_model=AdminUserStatusActionResponse)
async def admin_restore_user(
    user_id: int = Path(..., gt=0),
    current_admin: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
    incident_management_service: IncidentManagementService = Depends(IncidentManagementService),
):
    """Restore a user account to ACTIVE status (admin only)."""
    try:
        updated_user = await incident_management_service.restore_user(
            user_id,
            actor=current_admin.username,
            db=db,
            auth_service=auth_service,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc

    await db.commit()
    await db.refresh(updated_user)

    return AdminUserStatusActionResponse(
        success=True,
        action="restore",
        message="User account restored successfully",
        user=_serialize_user_status(updated_user),
    )

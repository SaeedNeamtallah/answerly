from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import List, Optional

from backend.database import get_db
from backend.database.models import AuditLog, User, RoleAssignmentHistory, UserRole
from backend.security.auth import require_platform_owner_access
from backend.security.event_service import log_event
from backend.security.sanitization import sanitize_text
from backend.security.security_event import SecurityEventType, SecuritySeverity

router = APIRouter(
    prefix="/admin/roles",
    tags=["Admin Roles"],
)

class UpdateRoleRequest(BaseModel):
    role: str = Field(..., description="The new role to assign to the user.")
    reason: str = Field(..., min_length=3, max_length=500, description="Reason for role change.")

class RoleAssignmentResponse(BaseModel):
    success: bool
    user_id: int
    new_role: str
    message: str


async def _reject_last_platform_owner_demotion(
    *,
    db: AsyncSession,
    target_user: User,
    new_role: str,
) -> None:
    if target_user.role != UserRole.PLATFORM_OWNER.value:
        return
    if new_role == UserRole.PLATFORM_OWNER.value:
        return

    platform_owner_count = await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.PLATFORM_OWNER.value)
    )
    if int(platform_owner_count or 0) <= 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove the last platform_owner role",
        )

@router.post("/users/{user_id}", response_model=RoleAssignmentResponse)
async def assign_user_role(
    payload: UpdateRoleRequest,
    user_id: int = Path(..., gt=0),
    current_admin: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    """Assign a new role to a user (platform owners only)."""
    # Validate role enum
    valid_roles = [r.value for r in UserRole]
    if payload.role not in valid_roles:
        raise HTTPException(status_code=422, detail=f"Invalid role. Must be one of {valid_roles}")

    stmt = select(User).where(User.id == user_id).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    await _reject_last_platform_owner_demotion(
        db=db,
        target_user=user,
        new_role=payload.role,
    )

    old_role = user.role
    reason = sanitize_text(payload.reason, max_length=500, strip_html=True, allow_newlines=False)
    user.role = payload.role
    
    # Log to history
    history = RoleAssignmentHistory(
        target_user_id=user.id,
        actor_user_id=current_admin.id,
        actor_username=current_admin.username,
        old_role=old_role,
        new_role=payload.role,
        reason=reason
    )
    db.add(history)
    db.add(AuditLog(
        actor_id=current_admin.id,
        actor=current_admin.username,
        action="role_assignment_changed",
        target=user.id,
        target_user_id=user.id,
        extra_metadata={
            "target_username": user.username,
            "old_role": old_role,
            "new_role": payload.role,
            "reason": reason,
        },
    ))
    log_event({
        "event_type": SecurityEventType.ROLE_ASSIGNMENT_CHANGED,
        "severity": SecuritySeverity.MEDIUM,
        "user_id": user.id,
        "username": user.username,
        "message": "User role assignment changed",
        "metadata": {
            "actor_user_id": current_admin.id,
            "actor_username": current_admin.username,
            "target_user_id": user.id,
            "target_username": user.username,
            "old_role": old_role,
            "new_role": payload.role,
            "reason": reason,
        },
    })
    await db.commit()
    
    return RoleAssignmentResponse(
        success=True,
        user_id=user.id,
        new_role=payload.role,
        message="Role updated successfully."
    )

class AdminRoleUserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str

@router.get("/users", response_model=List[AdminRoleUserResponse])
async def list_users_for_roles(
    current_admin: User = Depends(require_platform_owner_access),
    db: AsyncSession = Depends(get_db),
):
    """List all users and their roles for role management."""
    stmt = select(User).order_by(User.id.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [
        AdminRoleUserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role
        ) for u in users
    ]

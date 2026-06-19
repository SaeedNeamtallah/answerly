## 22. Admin User Controls

### Explanation

The backend provides admin-only APIs for suspending, blocking, and restoring users. These routes are protected by `require_admin_access`. Reasons are sanitized, suspension duration is bounded, and actions are performed through the central incident/account-management service while emitting security events and audit logs.

### Path

`backend/routes/admin_users.py`

```python
router = APIRouter(
    prefix="/admin/users",
    tags=["Admin"],
)

@router.post("/{user_id}/suspend", response_model=AdminUserStatusActionResponse)
async def admin_suspend_user(
    payload: AdminSuspendUserRequest,
    user_id: int = Path(..., gt=0),
    current_admin: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
    incident_management_service: IncidentManagementService = Depends(IncidentManagementService),
):
    updated_user = await incident_management_service.suspend_user(
        user_id,
        reason,
        int(payload.duration_minutes),
        actor=current_admin.username,
        db=db,
        auth_service=auth_service,
    )
```

```python
@router.post("/{user_id}/block", response_model=AdminUserStatusActionResponse)
async def admin_block_user(
    payload: AdminBlockUserRequest,
    user_id: int = Path(..., gt=0),
    current_admin: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    updated_user = await incident_management_service.block_user(
        user_id,
        reason,
        actor=current_admin.username,
        db=db,
        auth_service=auth_service,
    )
```

```python
@router.post("/{user_id}/restore", response_model=AdminUserStatusActionResponse)
async def admin_restore_user(
    user_id: int = Path(..., gt=0),
    current_admin: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    updated_user = await incident_management_service.restore_user(
        user_id,
        actor=current_admin.username,
        db=db,
        auth_service=auth_service,
    )
```

---

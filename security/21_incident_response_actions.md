## 21. Incident Response Actions

### Explanation

Security engineers and admins can take response actions against incident actors, including suspending users, blocking users, restoring users, or ignoring incidents as false positives. Suspension duration must be positive, blocking remains active until manual restoration, and all actions are stored in incident logs and audit logs.

### Paths

`backend/models/incident_models.py`

```python
class IncidentActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: Literal["block_user", "suspend_user", "reactivate_user", "ignore"]
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

`backend/services/incident_management_service.py`

```python
_ACTION_LABELS: Dict[str, str] = {
    "block_user": "Block user",
    "suspend_user": "Suspend user",
    "reactivate_user": "Restore user",
    "ignore": "Ignore",
}

_AUDIT_ACTIONS: Dict[str, str] = {
    "block_user": "user_blocked",
    "suspend_user": "user_suspended",
    "reactivate_user": "user_reactivated",
    "ignore": "incident_ignored",
}
```

---

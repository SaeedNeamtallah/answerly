## 20. Incident Lifecycle Enforcement

### Explanation

Incident status transitions are controlled. The normal lifecycle is `OPEN → INVESTIGATING → RESOLVED → CLOSED`. Invalid transitions are rejected. Reopening is a special case allowed only from `CLOSED → OPEN` and requires a reason. Every major status change creates incident log entries and audit records.

### Path

`backend/services/incident_management_service.py`

```python
_ALLOWED_STATUS_TRANSITIONS: Dict[IncidentStatus, IncidentStatus] = {
    IncidentStatus.OPEN: IncidentStatus.INVESTIGATING,
    IncidentStatus.INVESTIGATING: IncidentStatus.RESOLVED,
    IncidentStatus.RESOLVED: IncidentStatus.CLOSED,
}

_REOPEN_ALLOWED_FROM: set = {IncidentStatus.CLOSED}
```

```python
if next_allowed is None or payload.status != next_allowed:
    raise HTTPException(
        status_code=400,
        detail=(
            f"Invalid transition from {self._enum_value(current_status)} "
            f"to {self._enum_value(payload.status)}"
        ),
    )

incident.status = payload.status

await self._append_incident_log(
    db=db,
    incident=incident,
    actor=current_user,
    event_type="STATUS_UPDATED",
    severity="LOW",
    message=f"Incident status updated from {previous_status} to {next_status}",
    metadata=status_log_metadata,
)
```

---

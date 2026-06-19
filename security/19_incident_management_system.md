## 19. Incident Management System

### Explanation

The project includes a full incident-management subsystem. Incidents are persisted in PostgreSQL and include severity, status, actor, assignment, description, notes, and false-positive fields. The system supports incident timelines, audit logs, assignment to security engineers, notes, false-positive handling, and reopening. Incidents can be automatically created from security events such as `BRUTE_FORCE`, `FILE_UPLOAD_BLOCKED`, and `RATE_LIMITED`.

### Paths

`backend/database/models.py`

```python
class Incident(Base):
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
```

`backend/services/incident_service.py`

```python
class IncidentService:
    _TYPE_MAP = {
        SecurityEventType.BRUTE_FORCE: "Brute Force",
        SecurityEventType.FILE_UPLOAD_BLOCKED: "Upload Attack",
        SecurityEventType.RATE_LIMITED: "Rate Limit Abuse",
    }

    _SEVERITY_MAP = {
        SecurityEventType.BRUTE_FORCE: IncidentSeverity.HIGH,
        SecurityEventType.FILE_UPLOAD_BLOCKED: IncidentSeverity.HIGH,
        SecurityEventType.RATE_LIMITED: IncidentSeverity.MEDIUM,
    }
```

---

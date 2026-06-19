## 24. Security Event CSV Export

### Explanation

The backend supports exporting security events as CSV. The export includes a UTF-8 BOM for Excel compatibility, supports up to 5,000 events, and sends `Cache-Control: no-store` to prevent caching. This is useful for reporting, evidence collection, and security reviews.

### Path

`backend/routes/security.py`

```python
@router.get("/events/export")
async def security_events_export(
    limit: int = Query(default=1000, ge=1, le=5000),
    _current_user: User = Depends(require_security_center_access),
):
    events = security_dashboard_service.get_events_for_export(limit=limit)
    csv_payload = _to_events_export_csv(events)
    filename = f"security-events-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=f"\ufeff{csv_payload}",
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
```

---

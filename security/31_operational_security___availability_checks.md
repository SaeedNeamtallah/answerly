## 31. Operational Security / Availability Checks

### Explanation

The health-readiness checks verify that the system is not only running but also operationally ready. They check the database, Celery broker, Redis result backend, shared configuration path, and vector store. This helps prevent exposing a partially broken system as healthy.

### Path

`backend/routes/health.py`

```python
broker_status, result_backend_status, shared_config_status, vector_store_status = (
    await asyncio.gather(
        _probe_tcp_endpoint(settings.celery_broker_url),
        _probe_tcp_endpoint(settings.celery_result_backend),
        _probe_shared_config(),
        _probe_vector_store(db_status),
    )
)

overall_status = "healthy"
if not all(
    (
        db_status == "connected",
        broker_status == "connected",
        result_backend_status == "connected",
        shared_config_status == "ready",
        vector_store_status == "connected",
    )
):
    overall_status = "unhealthy"
```

```python
@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    return await _build_health_response(db, include_deep_checks=False)


@router.get("/health/full", response_model=HealthResponse)
async def health_check_full(db: AsyncSession = Depends(get_db)):
    return await _build_health_response(db, include_deep_checks=True)
```

---

# Limitations Found

These are not missing features from the extraction list, but visible limitations in the current code/design:

* No MFA.
* Security event feed is in-memory with a maximum of 5,000 events and may be lost after restart.
* RBAC is username/config-driven, not a full database-backed role-management system.
* No external SIEM integration.
* Simulation can block a real user when escalation is enabled.
* Security Center is suitable for demo/SOC workflow, but it is not a production-grade SIEM.
* `GET /bot/config` appears to be read-only/open, while mutation is protected.
* XSS and SQL injection are mainly represented through simulation and input sanitization; there is no full WAF-style detector.

---

# Best One-Line Summary

The code includes security across **JWT authentication, bcrypt password hashing, RBAC, account suspension/blocking, brute-force protection, endpoint rate limiting, upload hardening, ownership isolation, vector-search tenant isolation, security event logging, incident management, SOC dashboard features, attack simulation, admin response actions, sanitized errors, CORS controls, and frontend role-aware security behavior**.

---

## Footer — 31 Points Only

1. Security configuration layer
2. JWT authentication
3. Password security
4. Username validation and normalization
5. Service account security
6. Role-Based Access Control
7. Account status enforcement
8. Login brute-force protection
9. Rate limiting
10. Input sanitization
11. Filename sanitization
12. File upload security
13. Project ownership isolation
14. Document ownership isolation
15. Query/RAG access control
16. Vector database security
17. Background task security
18. Security event logging
19. Incident management system
20. Incident lifecycle enforcement
21. Incident response actions
22. Admin user controls
23. Security Center dashboard APIs
24. Security event CSV export
25. Attack simulation / SOC demo mode
26. Frontend security behavior
27. Runtime configuration security
28. Bot configuration security
29. Error handling hardening
30. CORS hardening
31. Operational security / availability checks

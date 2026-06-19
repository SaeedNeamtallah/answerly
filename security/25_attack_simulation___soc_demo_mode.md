## 25. Attack Simulation / SOC Demo Mode

### Explanation

The project includes a safe SOC/demo attack simulation mode. It can generate login-failure events, brute-force events, XSS attempt events, SQL injection events, attack simulation events, and optional account-block escalation. Simulated events are tagged with `simulation: true`, allowing the frontend to separate them from real security events. XSS and SQL injection appear mainly as simulated events; the actual general defense is sanitization, not a full WAF-style detection engine.

### Paths

`backend/routes/security.py`

```python
@router.post("/simulate", response_model=SecuritySimulationResponse)
async def simulate_security_attack(
    request: Request,
    target_user_id: Optional[int] = Query(default=None, gt=0),
    escalate_to_block: bool = Query(default=True),
    current_user: User = Depends(require_security_center_access),
    db: AsyncSession = Depends(get_db),
):
    simulation_result = await security_dashboard_service.simulate_attack_with_user_control(
        db=db,
        actor_username=current_user.username,
        actor_user_id=current_user.id,
        ip_address=_extract_client_ip(request),
        target_user_id=resolved_target_user_id,
        escalate_to_block=escalate_to_block,
        block_reason="attack_simulation_escalation",
    )
```

`backend/services/security_dashboard_service.py`

```python
log_event({
    "event_type": SecurityEventType.BRUTE_FORCE,
    "severity": SecuritySeverity.HIGH,
    "user_id": user_id,
    "username": username,
    "ip_address": ip_address,
    "message": "Credential stuffing pattern detected (simulation)",
    "metadata": {
        "simulation": True,
        "attack": "credential_stuffing",
    },
})
```

---

# Backend Services Test Report

Date: 2026-06-12  
Branch: `final_v4`  
Environment: local Docker Compose on Windows  
Base URL: `http://127.0.0.1:8000`

## Scope

This run checked the backend API, Docker services, database/broker/result-backend dependencies, Celery worker/scheduler wiring, Alembic migration state, monitoring endpoints, backend regression tests, and live smoke flows.

The worktree already had local uncommitted changes from removing the legacy static frontend before this test run. No secrets from `.env` were printed into this report.

## Summary

Overall backend readiness is healthy.

- Docker Compose config: pass
- Backend health endpoints: pass
- PostgreSQL: pass
- RabbitMQ: pass
- Redis: pass with authenticated ping
- Qdrant: pass
- Celery worker inspect ping: pass
- Celery beat outbox schedule: pass
- Alembic migration state: pass, current revision is `20260501_01 (head)`
- Backend pytest suite: pass, `77 passed`
- Prometheus/Grafana availability: pass
- Live smoke tool: partial fail due stale smoke expectation around Telegram outbox behavior

## Service Checks

### Docker Compose

Command:

```powershell
docker compose -f docker/docker-compose.yml config --quiet
docker compose -f docker/docker-compose.yml ps
```

Result:

- Compose config validated successfully.
- Running services:
  - `backend`
  - `worker`
  - `scheduler`
  - `telegram_bot`
  - `postgres`
  - `rabbitmq`
  - `redis`
  - `qdrant`
  - `prometheus`
  - `grafana`
  - `postgres-exporter`
  - `node-exporter`

No `frontend` Docker service is present after legacy frontend removal.

### HTTP Health

Checked:

```text
GET /health/live
GET /health
GET /health/full
GET /metrics
```

Results:

- `/health/live`: `200`
- `/health`: `200`
- `/health/full`: `200`
- `/metrics`: `200`

`/health/full` response:

```json
{
  "status": "healthy",
  "database": "connected",
  "broker": "connected",
  "result_backend": "connected",
  "celery_worker": "connected",
  "shared_config": "ready",
  "vector_store": "connected",
  "llm_provider": "cerebras-llama-3.1-8b",
  "embedding_provider": "cohere",
  "embedding_provider_health": "connected",
  "vector_db_provider": "pgvector"
}
```

### Data and Queue Dependencies

PostgreSQL:

```powershell
docker exec ragmind-postgres pg_isready -U minirag_user -d minirag
```

Result: accepting connections.

RabbitMQ:

```powershell
docker exec rabbitmq rabbitmq-diagnostics -q ping
```

Result: `Ping succeeded`.

Redis:

```powershell
docker exec redis redis-cli -a <local-compose-password> ping
```

Result: `PONG`. Unauthenticated Redis ping is rejected, as expected.

Qdrant:

```powershell
Invoke-WebRequest http://127.0.0.1:6381/healthz
```

Result: `200`, `healthz check passed`.

### Celery and Migrations

Celery worker inspect:

```powershell
docker exec ragmind-backend python -c "from backend.celery_app import celery_app; print(celery_app.control.inspect(timeout=5).ping())"
```

Result:

```python
{'celery@e94624da7930': {'ok': 'pong'}}
```

Celery beat schedule and routes:

- `deliver-pending-telegram-messages` is registered.
- `backend.tasks.telegram_outbox.deliver_pending_messages` is routed to the default queue.
- Processing/indexing tasks are registered.

Alembic:

```powershell
docker exec ragmind-backend alembic -c backend/alembic/alembic.ini current
```

Result: `20260501_01 (head)`.

### Monitoring

Checked:

- Worker metrics: `http://127.0.0.1:9108/metrics` returned `200`.
- Prometheus: `http://127.0.0.1:9090/-/healthy` returned `200`.
- Grafana: `http://127.0.0.1:3000/api/health` returned `200`.

## Regression Tests

Command:

```powershell
.venv\Scripts\python.exe -m pytest -q backend/tests
```

Result:

```text
77 passed in 4.40s
```

Coverage includes auth/security regressions, app config, company project scoping, Telegram SaaS services, bot integration readiness, outbox task behavior, runtime config atomic writes, and Celery-only document processing.

## Live Smoke Test

Command:

```powershell
$env:RAGMIND_BASE_URL='http://localhost:8000'
.venv\Scripts\python.exe tools\test_all.py
```

Result: failed after partial success.

Passed before failure:

- `GET /health`
- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `GET /stats/`
- `GET /admin/overview` returned `403` for non-platform owner, expected
- `POST /security/simulate?escalate_to_block=false`
- `GET /incidents`
- `GET /incidents/{id}`
- `PATCH /incidents/{id}`
- `POST /incidents/{id}/assign`
- `POST /incidents/{id}/action`
- `PATCH /incidents/{id}/notes`
- `GET /config/providers`
- `POST /projects/`

Failure:

```text
[FAIL] Mocked webhook should send exactly one Telegram reply: []
```

Assessment:

This appears to be drift in `tools/test_all.py`, not a backend service outage. The smoke tool still expects webhook handling to call Telegram inline through the mocked `send_message`. Current backend behavior, documented in `AGENTS.md`, stores bot replies durably as `delivery_status="pending"` and sends them through the Celery Telegram outbox. The backend regression suite for the outbox passed.

Earlier in the same smoke area, an incident lifecycle run also failed once because the tool chose an incident already in `INVESTIGATING` and attempted the invalid transition `INVESTIGATING -> INVESTIGATING`. A manual incident lifecycle check using an `OPEN` incident passed.

## Manual Incident Lifecycle Check

Manual API check used the same backend auth flow without printing credentials.

Result:

- login: `200`
- security simulation: `200`
- list incidents: `200`
- patch incident from `OPEN` to `INVESTIGATING`: `200`
- assign incident: `200`
- apply incident action: `200`
- update notes: `200`

## Frontend-Related Sanity Check

Although this report targets backend services, the recent legacy frontend removal was verified:

- `http://127.0.0.1:3001/login`: `200`
- port `8080`: not listening
- compose services do not include a legacy `frontend` service

## Open Follow-Ups

1. Update `tools/test_all.py` so the mocked Telegram webhook smoke asserts the current outbox behavior:
   - bot reply persisted with `delivery_status="pending"`
   - no inline Telegram send required during webhook handling
   - optional outbox delivery tested separately with a decryptable token setup

2. Make the incident smoke idempotent:
   - choose an `OPEN` incident for `OPEN -> INVESTIGATING`
   - or transition based on the incident's current status
   - avoid asserting same-status transitions as success

3. If full production-like smoke is required, provide `RAGMIND_PLATFORM_OWNER_TOKEN` to enable positive `/admin/*` checks.

## Verdict

Backend runtime services are healthy and the backend regression test suite passes. The only failing live smoke result is caused by stale smoke-test expectations that do not match the current Telegram outbox design.

# Security Features — RAGMind SOC Dashboard

A technical reference for all security-related capabilities in this project. Intended for graduation project reviewers, technical evaluators, and developers onboarding to the codebase.

---

## 🛡️ Security Features Overview

RAGMind is a full-stack AI-powered document intelligence platform with an integrated Security Operations Center (SOC) dashboard. Beyond its core RAG (Retrieval-Augmented Generation) functionality, the system includes a dedicated security layer covering authentication, access control, real-time threat monitoring, incident lifecycle management, attack simulation for training purposes, and automated threat response.

The security subsystem is implemented across `backend/security/`, `backend/services/`, and `backend/routes/security.py`, and is designed to reflect realistic SOC workflows rather than synthetic counters.

---

## 🔐 Authentication & Access Control

### User Authentication

- **Signup and login** are handled via `POST /auth/signup` and `POST /auth/login`.
- Passwords are hashed using **bcrypt** before storage. Plain-text passwords are never persisted.
- Usernames are normalized (lowercased, sanitized) and validated against a strict regex pattern (`^[a-z0-9_.-]{3,50}$`) before any database operation.
- Passwords are validated for minimum length (8 characters), maximum byte length (72 bytes, matching bcrypt's limit), and absence of control characters.

### JWT-Based Session Management

- Successful login issues a **signed JWT access token** containing the user's subject (`sub`) and assigned roles.
- Tokens are signed using a configurable secret key and algorithm (via `AUTH_JWT_SECRET_KEY` and `AUTH_JWT_ALGORITHM`).
- Token expiry is configurable via `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES`.
- All protected endpoints require a `Bearer` token in the `Authorization` header.
- Expired or malformed tokens are rejected with a `401 Unauthorized` response, and the rejection is logged as a security event.

### Role-Based Access Control (RBAC)

Three roles are enforced at the route level:

| Role | Access |
|---|---|
| `user` | Standard application features (projects, documents, queries) |
| `security_engineer` / `cybersecurity_engineer` | Security Center, incident management, simulation |
| `admin` | All of the above plus admin-only endpoints |

- Security engineer usernames are configured via `SECURITY_ENGINEER_USERNAMES` in `.env` and are resolved dynamically (with a short TTL cache) so changes take effect without a restart.
- The `require_security_center_access` and `require_incident_access` FastAPI dependencies enforce role checks on every Security Center request and log any denied access attempt as a `AUTHZ_DENIED` security event.

### Service Account Management

- `BOT_API_USERNAME/BOT_API_PASSWORD` and `AUTH_ADMIN_USERNAME/AUTH_ADMIN_PASSWORD` are treated as managed service accounts.
- Successful login for a service account provisions or syncs a matching database user row, so JWT subjects always resolve through the standard `get_current_db_user()` dependency.
- Service account usernames are reserved and cannot be registered or have their passwords changed through the normal signup/change-password flows.
- Admin passwords support both plain-text comparison and a `pbkdf2_sha256` hash format for hardened deployments.

### Account Status Enforcement

User accounts carry one of three statuses: `ACTIVE`, `SUSPENDED`, or `BLOCKED`.

- **Suspended** accounts have a time-bounded expiry (`suspended_until`). Expired suspensions are automatically lifted on the next authenticated request or login attempt.
- **Blocked** accounts are permanently denied access until manually restored by an admin.
- Status checks are enforced on every authenticated request via `_enforce_account_status_policy()`, not only at login time.
- All status transitions are logged as security events and written to the `audit_logs` table.

---

## 🚨 Incident Management System

Incidents are persisted in PostgreSQL and follow a strict lifecycle enforced at the service layer.

### Incident Lifecycle

```
OPEN → INVESTIGATING → RESOLVED → CLOSED
```

- Forward transitions are the only allowed path. Skipping a step (e.g., `OPEN → RESOLVED`) is rejected with a `400` error.
- **Reopen** is a special reverse transition: `CLOSED → OPEN` only.
- Every status change is recorded in the `incident_logs` table and emits a security event.

### Automatic Incident Creation

High-value security detections automatically create incidents without manual intervention:

| Security Event | Incident Type | Severity |
|---|---|---|
| `BRUTE_FORCE` | Brute Force | HIGH |
| `FILE_UPLOAD_BLOCKED` | Upload Attack | HIGH |
| `RATE_LIMITED` | Rate Limit Abuse | MEDIUM |

Auto-created incidents are assigned to the security engineer with the lowest current active incident load (least-load balancing across configured engineer accounts).

### Incident Actions

Security engineers can apply the following actions to an incident's actor:

- **Suspend user** — temporarily suspends the account for a configurable duration (default from `SECURITY_USER_SUSPENSION_DEFAULT_MINUTES`).
- **Block user** — permanently blocks the account until manually restored.
- **Restore user** — reactivates a suspended or blocked account.
- **Ignore / Mark as false positive** — flags the incident as a false positive without affecting the actor's account.

All actions are written to both `incident_logs` (per-incident timeline) and `audit_logs` (global audit trail).

### Investigation Notes

- Each incident supports free-text investigation notes (up to 8,000 characters).
- Notes are bounded and sanitized before persistence.

### Assignment

- Incidents can be self-assigned by a security engineer via `POST /incidents/{id}/assign`.
- Auto-assignment at creation time uses a least-active-load strategy across all configured engineer accounts.

---

## 📊 Security Monitoring

### Real-Time Events Feed

- Security events are stored in an in-memory ring buffer (up to 5,000 events) via `backend/security/event_service.py`.
- The feed is accessible at `GET /security/events` and supports filtering by event type and severity.
- A **Server-Sent Events (SSE)** stream at `GET /security/events/stream` pushes live dashboard updates to connected clients every second, with keep-alive pings during idle periods.

### Event Types Tracked

The system captures the following event types:

- `LOGIN_FAIL`, `LOGIN_SUCCESS`
- `SIGNUP_FAIL`, `SIGNUP_SUCCESS`
- `PASSWORD_CHANGE_SUCCESS`, `PASSWORD_CHANGE_FAIL`
- `BRUTE_FORCE`
- `FILE_UPLOAD_BLOCKED`
- `RATE_LIMITED`
- `AUTH_REQUIRED`, `AUTHZ_DENIED`, `AUTH_TOKEN_INVALID`
- `XSS_ATTEMPT`, `SQL_INJECTION`
- `USER_SUSPENDED`, `USER_BLOCKED`, `USER_RESTORED`
- `ATTACK_SIMULATION`

### Dashboard Aggregates

`GET /security/stats` returns aggregate counters:

- Total events
- Login failures
- Brute-force attempts
- Blocked uploads

### User Account Status Summary

`GET /security/users/status-summary` returns counts of `ACTIVE`, `SUSPENDED`, and `BLOCKED` users, queried live from the database.

### Events Export

`GET /security/events/export` downloads up to 5,000 events as a UTF-8 CSV file, suitable for SOC reporting and evidence retention.

---

## 🧪 Attack Simulation (Safe Demo Mode)

The simulation feature exists exclusively for training, demonstrations, and testing SOC workflows. It is not connected to any external system.

### What Simulation Does

Triggering `POST /security/simulate` generates a realistic sequence of demo events through the same event logging pipeline used by real detections:

1. A series of `LOGIN_FAIL` events (credential stuffing pattern)
2. A `BRUTE_FORCE` detection event
3. An `XSS_ATTEMPT` event with a sample payload
4. A `SQL_INJECTION` event with a sample payload
5. An optional account block escalation on a target user

All generated events carry `"simulation": true` in their metadata, making them distinguishable from organic events at the data layer.

### Simulation Isolation Principle

> **Simulation data is strictly isolated and never mixed with real security data.**

- Simulated events are tagged at the source with `"simulation": true` in their metadata.
- The frontend renders a neutral "Simulated" badge on incidents and events originating from simulation runs.
- Incident source filtering is available in the UI to separate real from simulated incidents.
- Overview counters keep real incidents as the primary metric and expose simulated counts separately.

### Access Control

The simulation endpoint requires the `security_engineer` or `admin` role. It is not accessible to regular users.

---

## 🔄 Simulation Control & Reset

### What Reset Affects

The "Reset Simulation" action in the Security Center UI is a **view-only feed clear**:

- Removes simulated events from the transient in-memory event feed displayed in the UI.
- Logs an audit message recording that the reset was performed.

### What Reset Does NOT Affect

- Real security incidents stored in the database.
- Real security events (non-simulated).
- User account statuses (active, suspended, blocked).
- Overview metrics derived from real incidents.
- Any persistent database records.

This design ensures that SOC investigation continuity is preserved across simulation resets.

---

## 🧠 Chat & File Processing Security

### File Upload Validation

File uploads go through a multi-layer validation pipeline in `FileService.validate_file()`:

1. **Extension blocklist** — `.php`, `.exe`, `.js`, `.sh` are always rejected.
2. **Supported type check** — only `.pdf`, `.txt`, and `.docx` are accepted.
3. **File size limit** — configurable via `MAX_FILE_SIZE_MB`.
4. **MIME type validation** — the declared `Content-Type` is checked against the expected MIME types for the file extension. Generic `application/octet-stream` values are resolved by extension inference.
5. **Magic byte / file signature validation** — when enabled (`SECURITY_UPLOAD_VALIDATE_MAGIC=true`), the first bytes of the file are inspected to confirm the content matches the declared format:
   - PDF: must start with `%PDF-`
   - DOCX: must be a valid ZIP archive containing `[Content_Types].xml` and a `word/` directory
   - TXT: must not contain null bytes

Any blocked upload emits a `FILE_UPLOAD_BLOCKED` security event (severity: HIGH) and triggers automatic incident creation.

### Filename Sanitization

Uploaded filenames are sanitized before storage:

- Control characters and path traversal sequences are stripped.
- Only alphanumeric characters, dots, underscores, spaces, and hyphens are retained.
- A UUID suffix is appended to prevent collisions and obscure original filenames.

### Background Document Processing

Uploaded files are processed asynchronously via Celery workers:

- The API returns immediately after accepting the upload; processing happens in the background.
- If processing fails, stale chunks and vectors for the affected asset are cleaned up before any retry.
- Processing status is tracked in the `celery_task_executions` table and exposed via `GET /documents/{id}/task-status`.

### Chat / Query Security

- All query inputs are sanitized before being passed to the LLM pipeline.
- Queries are scoped to the authenticated user's owned projects — cross-user data access is not possible.
- Rate limiting is applied to query endpoints (see below).

---

## ⚙️ Background Processing (Celery + Queue)

Background processing decouples long-running operations from the HTTP request cycle, preventing timeouts and enabling reliable retry behavior.

### Components

| Service | Role |
|---|---|
| **RabbitMQ** | Message broker — queues task messages between the API and workers |
| **Redis** | Result backend — stores task state and output for status polling |
| **Celery Worker** | Executes document processing and indexing tasks |
| **Celery Beat (Scheduler)** | Runs periodic maintenance tasks (e.g., cleaning stale task execution records) |

### Task Queues

- `default` — general tasks
- `file_processing` — document upload, chunking, and embedding tasks

### Why Background Processing

- File parsing, text chunking, and embedding generation can take seconds to minutes depending on document size and the configured embedding provider.
- Running these operations synchronously would block the API and degrade user experience.
- Celery provides durable task execution with retry support and observable status.

---

## 🧱 Secure Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Nginx)                      │
│              Static HTML/CSS/JS served on port 80            │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS / REST + SSE
┌────────────────────────────▼────────────────────────────────┐
│                   Backend API (FastAPI)                       │
│  Routes → Controllers → Services → Providers                 │
│  Security Layer: JWT auth, RBAC, rate limiting, sanitization │
│  Port 8000                                                   │
└──────┬──────────────────────────────────────┬───────────────┘
       │ SQL (asyncpg)                         │ Task dispatch
┌──────▼──────────┐                  ┌────────▼───────────────┐
│   PostgreSQL    │                  │   RabbitMQ (broker)    │
│  + pgvector     │                  │   Redis (result store) │
│  Users/Projects │                  └────────┬───────────────┘
│  Incidents      │                           │
│  Audit Logs     │                  ┌────────▼───────────────┐
└─────────────────┘                  │   Celery Worker        │
                                     │   Document processing  │
┌─────────────────┐                  │   Embedding + indexing │
│  Qdrant         │◄─────────────────┤                        │
│  (vector store) │                  └────────────────────────┘
└─────────────────┘
```

All services run as isolated Docker containers orchestrated via `docker/docker-compose.yml`. The application image is built once (`ragmind-app:local`) and reused by the API, worker, scheduler, and Telegram bot containers.

---

## 🛡️ Security Best Practices Applied

### Input Handling

- All text inputs (usernames, project names, query strings, metadata) pass through `sanitize_text()`, which strips control characters, HTML tags, and script blocks before any processing or storage.
- Filenames are sanitized separately via `sanitize_filename()` to prevent path traversal.
- Metadata dictionaries are bounded to 32 keys with per-key and per-value length limits.

### Authentication Hardening

- Passwords are hashed with bcrypt (adaptive cost factor).
- JWT tokens require both `sub` and `exp` claims; tokens missing either are rejected.
- Token subjects are resolved against the database on every request — a deleted user cannot reuse a previously issued token.
- Rate limiting on `POST /auth/login` limits brute-force attempts at the network layer, complementing the in-memory login tracker.

### Rate Limiting

`SecurityRateLimitMiddleware` applies sliding-window rate limits per endpoint:

| Endpoint | Limit |
|---|---|
| `POST /auth/login` | Configurable via `SECURITY_RATE_LIMIT_LOGIN_*` |
| `POST /projects/{id}/query` | Configurable via `SECURITY_RATE_LIMIT_CHAT_*` |
| `POST /projects/{id}/documents` | Configurable via `SECURITY_RATE_LIMIT_UPLOAD_*` |
| `POST /projects` | Configurable via `SECURITY_RATE_LIMIT_PROJECT_CREATE_*` |

- Rate limit keys are derived from the JWT subject when a valid token is present, falling back to client IP. This prevents shared-IP bottlenecks in NAT environments.
- Repeated rate limit violations (threshold configurable) trigger automatic temporary account suspension.
- Rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) are included in responses.

### Brute-Force Detection

- `LoginSecurityService` tracks failed login attempts per username and per IP using a sliding window.
- When the failure threshold is crossed, a `BRUTE_FORCE` event is emitted and the username/IP is temporarily blocked.
- Successful login clears the failure counters for that username and IP.

### Audit Logging

- All security-sensitive actions (incident status changes, user suspensions, blocks, restores, assignments) are written to the `audit_logs` table with actor, action, target, and metadata.
- Security events are also emitted to the in-memory event feed for real-time dashboard visibility.

### Separation of Simulation and Real Data

- Simulated events carry `"simulation": true` in metadata.
- The frontend tags incidents by source and renders them with distinct visual indicators.
- Simulation reset only clears the transient UI feed — no database records are modified.

### Error Handling

- Route-level unexpected exceptions are caught, logged server-side, and returned to clients as sanitized messages (e.g., `"Internal server error"`) to prevent leaking stack traces or internal details.
- Background task failures clean up partial state (stale chunks and vectors) before surfacing the error.

### CORS

- Allowed origins are configured explicitly via `CORS_ORIGINS` — wildcard origins with credentials are not used.

---

## ⚠️ Known Limitations / Future Improvements

- **MFA not implemented.** Multi-factor authentication is not currently available. Login security relies on brute-force detection, rate limiting, and account suspension.
- **In-memory event store.** The security event feed is held in memory (up to 5,000 events). Events are lost on process restart. A persistent event store (e.g., a dedicated `security_events` table or an external SIEM) would be needed for production-grade retention.
- **RBAC is configuration-driven, not database-driven.** Engineer usernames are read from environment variables. A database-backed role assignment system would provide more flexible access management.
- **No real SIEM integration.** The current system is self-contained. Integration with external SIEM platforms (Splunk, Elastic SIEM, etc.) is a planned future improvement.
- **Simulation escalation affects real account state.** When `escalate_to_block=true` (the default), the simulation endpoint applies a real account block to the target user. This is intentional for demo realism but should be understood before running simulations in shared environments.

---

## ▶️ How to Run the Project

### Prerequisites

- Docker and Docker Compose installed
- A `.env` file configured from `.env.example`

### First-Time Setup

```bash
scripts\dev\setup.bat
```

This prepares the local environment, installs dependencies, and writes setup output to `uploads/logs/setup.log`.

### Start the Full Stack

```bash
scripts\dev\start.bat
```

This starts all Docker services (PostgreSQL, Redis, RabbitMQ, Qdrant, backend, worker, scheduler, frontend), waits for the backend health check at `http://127.0.0.1:8000/health` to report `"status": "healthy"`, and opens the frontend at:

```
http://localhost:8080/login.html?api=http://localhost:8000
```

To force a Docker image rebuild (e.g., after changing `requirements.txt` or a Dockerfile):

```bash
scripts\dev\start.bat --build
```

### Stop the Stack

```bash
scripts\dev\stop.bat
```

### Backend API

Available at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

### Health Check

```
GET http://localhost:8000/health
```

Returns `"status": "healthy"` only when the database, message broker, result backend, Celery worker, shared config, and vector store are all reachable.

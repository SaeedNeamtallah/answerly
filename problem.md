# Problem Backlog

Last updated: 2026-04-21

This file tracks confirmed code-grounded problems that need to be fixed, not speculative ideas.

## Resolved In This Task

1. Manual project reindex no longer queues into an unconsumed Celery queue.
   Fix: `index_project_task` now routes consistently through the default worker queue, and returned reindex task ids are owner-tracked.

2. Workflow/status tracking for background tasks is now durable.
   Fix: task ownership is persisted by `celery_task_id`, worker tasks reuse the same `celery_task_executions` row, and `/tasks/{task_id}` now resolves tracked workflow child state instead of relying on in-memory-only ownership.

3. The bot service-account login path now produces a DB-backed identity.
   Fix: configured `BOT_API_*` / `AUTH_ADMIN_*` credentials are treated as managed service accounts during `/auth/login`, and successful login provisions or syncs the corresponding `users` row.

4. `/bot/config` mutation is no longer effectively unauthenticated.
   Fix: `POST /bot/config` now requires `get_current_db_user()` and validates the selected project id before persisting it.

5. Runtime config drift across backend, worker, and telegram bot is reduced.
   Source: `docs/database.md`
   Fix: app and bot config now resolve through shared files under `uploads/config/`, all relevant Compose services receive `RAGMIND_SHARED_CONFIG_DIR`, and the bot mounts the shared uploads volume.

6. Fresh Docker startup no longer crash-loops the bot when the Telegram token is blank.
   Fix: the bot service idles instead of repeatedly failing when `TELEGRAM_BOT_TOKEN` is unset, and the hardcoded `BOT_ACTIVE_PROJECT_ID` Compose override was removed.

7. Celery cleanup scheduling is now active in the local Docker stack.
   Fix: Compose now includes a dedicated Celery beat scheduler service.

8. Docker startup now waits for full backend readiness instead of any `/health` 200.
   Fix: `backend/routes/health.py` now checks database, broker, result backend, Celery worker reachability, shared-config readiness, and vector-store connectivity; `scripts/dev/start.bat` now waits specifically for `status == "healthy"`.

9. `process-and-index` workflow records now finalize without requiring `/tasks/{task_id}` polling.
   Fix: child tasks reconcile the parent workflow row immediately after success, skip, or failure updates through `backend/utils/task_tracking.py`.

10. Historical duplicate `celery_task_executions` rows now self-heal during reads and scheduled cleanup.
    Fix: `backend/utils/idempotency_manager.py` now merges duplicate rows by `celery_task_id`, preserves the most advanced status/result, and deletes superseded rows both on lookup and during maintenance cleanup.

11. Failed document retries now clean stale vectors in Qdrant as well as stale chunk rows in PostgreSQL.
    Fix: the vector provider interface now exposes targeted `delete_vectors(...)`, `QdrantProvider` deletes by payload filter, and document processing clears old vectors for the current `asset_id` before retry and on failure.

## Remaining Problems

No confirmed open problems remain in this backlog after the latest fixes.

## Notes

- `docs/database.md` correctly identified config drift; that issue is now resolved through shared config under `uploads/config/`.
- The backend relational schema and RAG ownership model remain aligned; recent fixes were operational/runtime integration fixes, not schema-model mismatch fixes.

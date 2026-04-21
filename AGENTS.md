# AGENTS.md

## Purpose

This file is the working map for agents in this repository. Read it before deep exploration, keep it short, and update it whenever the code structure or critical behavior changes.

Primary goal: reduce token waste by searching first, reading only the needed files, and keeping a living code graph here instead of rediscovering the same structure every turn.

## Mandatory Workflow

1. Start with targeted search, not broad file dumps.
2. Read this file before opening many files.
3. Prefer `rg`, `rg --files`, and narrow reads around matched lines.
4. Trace requests by layer: `route -> controller -> service -> provider/db/task`.
5. When a structural change lands, update this file in the same task.
6. When adding a class, endpoint, task, provider, or major function, add it here immediately.
7. When removing or renaming behavior, remove stale entries here immediately.
8. Do not trust `README.md` as the source of truth; verify against code.
9. Keep summaries compact. Do not paste large code blocks into this file.
10. If this file is out of sync with the code, fix it first or explicitly note the drift.

## Token-Saving Search Playbook

- Entry points:
  - `backend/main.py`
  - `backend/routes/*.py`
  - `telegram_bot/bot.py`
  - `frontend/app.js`
- Find classes/functions:
  - `rg -n "^(class|def|async def) " backend telegram_bot`
- Find ownership/auth flow:
  - `rg -n "get_current_db_user|owner_id|require_security_center_access" backend`
- Find retrieval pipeline:
  - `rg -n "search_similar_chunks|generate_answer|add_vectors|create_provider" backend`
- Find Celery flow:
  - `rg -n "process_document_task|index_project_task|process_and_index_workflow" backend`
- Find config toggles:
  - `rg -n "get_runtime_value|settings\\." backend`

## Architecture Summary

The backend is layered and mostly follows this shape:

`FastAPI routes -> controllers -> services -> providers -> DB / vector DB / external APIs`

Cross-cutting layers:

- `backend/security/*`: auth, rate limiting, sanitization, event logging
- `backend/tasks/*`: Celery background processing/indexing workflows
- `backend/runtime_config.py`: runtime toggles persisted outside static env config via shared JSON under `uploads/config/`

Top-level repo organization:

- `.dockerignore`: Docker build allowlist for runtime-only context
- `scripts/dev/`: local Windows startup helpers
  - only three entry scripts should remain here: `setup.bat`, `start.bat`, `stop.bat`
- `tools/`: maintenance and one-off repo utilities
  - includes `tools/test_all.py` as the authenticated smoke test entrypoint
- `docs/`: notes and extra documentation
  - includes `docs/project-graph.md` as the current runtime/API/service/data/frontend graph
  - includes `docs/database.md` as the current storage/database map and sync verdict
- `assets/`: static project assets
- `uploads/config/`: shared runtime config for backend, worker, and telegram bot (`app_config.json`, `bot_config.json`)
- `uploads/logs/`: runtime logs, probes, and local command output
- `tmp/`: generated local artifacts
- root keeps only repo-critical/runtime-root files such as `.env*`, `README.md`, `LICENSE`, `AGENTS.md`, `app_config.json`, and `bot_config.json`; the two root config JSON files now act as legacy/bootstrap copies and live config should be read from `uploads/config/`; Alembic runtime files now live under `backend/alembic/` (`backend/alembic/alembic.ini`, `backend/alembic/init-db.sql`)

Main persistence model:

- PostgreSQL via async SQLAlchemy for users/projects/assets/chunks/task executions
- Vector storage via pluggable provider:
  - `pgvector`
  - `qdrant`

## Code Graph

### Entry Points

- `backend/main.py`
  - builds FastAPI app
  - registers routers
  - initializes and closes DB in `lifespan()`
- `telegram_bot/bot.py`
  - bot startup
  - handler wiring
- `frontend/app.js`
  - browser-side API integration and dashboard behavior
- `scripts/dev/*.bat`
  - local developer entrypoints
  - `setup.bat` prepares the local environment with Windows-friendly fallbacks (`uv` or `py/python` venv creation, `uv pip` or `pip` install, `docker compose` or `docker-compose` detection) and writes setup output to `uploads/logs/setup.log`
  - `start.bat` starts the full Docker stack without rebuilding by default, accepts `--build` to force image rebuilds when Dockerfile/image inputs changed, launches the local static frontend on port `8080`, opens `login.html`, and writes runtime logs into `uploads/logs/`
  - `stop.bat` stops the full Docker stack, closes the frontend/log windows started by the start script, and writes stop logs into `uploads/logs/`

### Local Run (Windows Start File)

- Preferred run path from repo root:
  - `scripts\dev\setup.bat` (first run or when dependencies/env changed)
  - `scripts\dev\start.bat` (normal startup)
  - `scripts\dev\start.bat --build` (only when Docker image inputs changed)
- `start.bat` behavior:
  - starts `docker/docker-compose.yml` services
  - waits for backend readiness at `http://127.0.0.1:8000/health` until the JSON response reports `status == "healthy"`
  - if host-side health probing is blocked, falls back to checking `/health` from inside `ragmind-backend` and logs a warning before continuing
  - serves frontend on `http://localhost:8080`
  - opens `http://localhost:8080/login.html?api=http://localhost:8000`
  - writes runtime logs into `uploads/logs/` (`start.log`, `docker_stack.log`, `frontend.log`, `docker_ps.log`)
- Stop path: `scripts\dev\stop.bat`

### Database Layer

- `backend/database/connection.py`
  - `get_db()`
  - `init_db()`
  - `close_db()`
- `backend/database/models.py`
  - `User`
  - `Project`
  - `Asset`
  - `Chunk`
  - `CeleryTaskExecution`

Relationships:

- `User.projects -> Project.owner`
- `Project.assets`
- `Project.chunks`
- `Asset.project`
- `Asset.chunks`
- `Chunk.project`
- `Chunk.asset`

Schema management rules:

- Alembic is the source of truth for schema creation and evolution.
- `backend/database/connection.py:init_db()` now ensures extensions and runs `alembic upgrade head`; it does not call `Base.metadata.create_all()` anymore.
- `backend/init_database.py` bootstraps the database, then relies on `init_db()` to apply migrations.
- If models change, add or update Alembic revisions in `backend/alembic/versions/` instead of adding new ad-hoc DDL in runtime code.
- `Chunk.embedding` is a native `pgvector` column now; do not reintroduce JSON fallback search paths.
- Because `Chunk.embedding` uses flexible `Vector()`, pgvector ANN search must filter by `vector_dims(embedding)` and cast to the current query dimension to use the correct expression index.

### Route Layer

- `backend/routes/auth.py`
  - `signup()`
  - `login()`
  - `me()`
  - `change_password()`
- `backend/routes/projects.py`
  - `create_project()`
  - `list_projects()`
  - `get_project()`
  - `index_project()`
  - `get_project_stats()`
  - `update_project()`
  - `delete_project()`
- `backend/routes/documents.py`
  - `upload_document()`
  - `list_project_documents()`
  - `get_document()`
  - `process_document()`
  - `process_and_index_document()`
  - `delete_document()`
  - `get_task_status()`
- `backend/routes/query.py`
  - `query_project()`
- `backend/routes/security.py`
  - `security_stats()`
  - `security_events()`
  - `simulate_security_attack()`
  - `security_events_stream()`
- `backend/routes/health.py`
  - `health_check()`
    - full readiness probe for database, Celery broker, result backend, live worker ping, shared config path readiness, and vector store connectivity
  - `root()`
- `backend/routes/stats.py`
  - `get_global_stats()`
- `backend/routes/app_config.py`
  - `get_providers()`
  - `update_providers()`
- `backend/routes/bot_config.py`
  - `get_bot_config()`
  - `update_bot_config()`
  - `update_bot_profile()`

### Controller Layer

- `backend/controllers/project_controller.py`
  - `create_project()`
  - `get_project()`
  - `list_projects()`
  - `update_project()`
  - `delete_project()`
  - `get_project_stats()`
- `backend/controllers/document_controller.py`
  - `upload_document()`
  - `process_document()`
  - `_process_document_impl()`
  - `_update_asset_progress()`
  - `get_document()`
  - `list_project_documents()`
  - `delete_document()`
- `backend/controllers/query_controller.py`
  - `answer_query()`
  - `_fallback_answer()`

### Service Layer

- `backend/services/auth_service.py`
  - `authenticate_user()`
  - `signup_user()`
  - `change_password()`
- `backend/services/file_service.py`
  - `save_upload_file()`
  - `delete_file()`
  - `delete_project_files()`
  - `validate_file()`
- `backend/services/document_loader.py`
  - `load_document()`
  - `_load_pdf()`
  - `_load_txt()`
  - `_load_docx()`
- `backend/services/chunking_service.py`
  - `chunk_text()`
  - `chunk_document()`
  - `_chunk_parent_child()`
- `backend/services/embedding_service.py`
  - `generate_embeddings()`
  - `generate_single_embedding()`
  - `get_embedding_dimension()`
- `backend/services/query_service.py`
  - `search_similar_chunks()`
  - `_hydrate_chunk_payloads()`
  - `_rewrite_query()`
  - `_apply_hybrid_scoring()`
  - `_apply_rerank()`
  - `_tokenize()`
  - `_lexical_score()`
- `backend/services/answer_service.py`
  - `generate_answer()`
  - `_build_context()`
  - `_build_prompt()`
  - `_extract_sources()`
  - `_fallback_answer()`
- `backend/services/login_security_service.py`
  - `check_block()`
  - `log_blocked_attempt()`
  - `record_failed_login()`
  - `clear_success()`
- `backend/services/security_dashboard_service.py`
  - `get_stats()`
  - `get_events()`
  - `get_dashboard_payload()`
  - `simulate_attack()`
  - `stream_dashboard_updates()`

### Provider Layer

LLM:

- `backend/providers/llm/interface.py`
  - `LLMInterface`
- `backend/providers/llm/factory.py`
  - `LLMProviderFactory.create_provider()`
  - `LLMProviderFactory.create_embedding_provider()`
- Implementations:
  - `GeminiProvider`
  - `CohereProvider`
  - `VoyageProvider`
  - `BgeM3Provider`
  - `OpenAICompatProvider`

Vector DB:

- `backend/providers/vectordb/interface.py`
  - `VectorDBInterface`
  - `delete_vectors()` for targeted metadata-filtered cleanup
- `backend/providers/vectordb/factory.py`
  - `VectorDBProviderFactory.create_provider()`
- Implementations:
  - `PGVectorProvider`
    - targeted vector deletion maps to deleting matching `Chunk` rows
  - `QdrantProvider`
    - targeted vector deletion uses Qdrant payload filters (`owner_id` / `project_id` / `asset_id`)

### Security Layer

- `backend/security/auth.py`
  - token decode and current-user dependencies
  - role resolution
- `backend/security/jwt_utils.py`
  - token create/decode helpers
- `backend/security/middleware.py`
  - `SecurityRateLimitMiddleware`
- `backend/security/rate_limit.py`
  - in-memory limiter primitives
- `backend/security/sanitization.py`
  - text/file/metadata sanitizers
- `backend/security/event_service.py`
  - security event storage and stats
- `backend/security/security_event.py`
  - event models/constants

### Background Tasks

- `backend/tasks/file_processing.py`
  - `process_document_task()`
  - `_process_document()`
    - clears stale per-asset chunks/vectors before retry and on failure
    - reconciles parent `process-and-index` workflow status after terminal child updates
  - `_update_progress()`
- `backend/tasks/data_indexing.py`
  - `index_project_task()`
  - `_index_project()`
    - reconciles parent `process-and-index` workflow status after terminal child updates
- `backend/tasks/process_workflow.py`
  - `push_after_process_task()`
  - `process_and_index_workflow()`
  - `_process_and_index_workflow()`
    - records child task ids (`process_task_id`, `index_task_id`) in the parent workflow result payload for downstream reconciliation
- `backend/tasks/maintenance.py`
  - `clean_celery_executions_table()`

### Utility Layer

- `backend/shared_config_paths.py`
  - resolves shared config paths for `app_config.json` and `bot_config.json`
  - copies legacy root config files into `uploads/config/` on first access when needed
- `backend/runtime_config.py`
  - `load_runtime_config()`
  - `save_runtime_config()`
  - `update_runtime_config()`
  - `get_runtime_value()`
- `backend/utils/idempotency_manager.py`
  - task deduplication and execution records keyed by normalized task args plus `celery_task_id`
  - self-heals duplicate `celery_task_executions` rows by merging duplicate `celery_task_id` records on lookup and cleanup
- `backend/utils/task_tracking.py`
  - `record_task_owner()`
  - `get_tracked_task_record()`
  - `task_belongs_to_user()`
  - `reconcile_process_and_index_workflow()`

### Repo Utilities

- `tools/combine_code.py`
  - default mode still writes `tmp/all_project_code.txt`
  - `--profile database` writes focused storage/database snippets to `tmp/database_code.txt`
- `tools/test_all.py`
  - authenticated smoke test for `health -> signup/login -> project -> upload/process -> query -> cleanup`
  - supports `RAGMIND_BASE_URL`, `RAGMIND_REQUEST_TIMEOUT`, `RAGMIND_PROCESSING_TIMEOUT`, and `RAGMIND_STRICT_QUERY=1`

### Telegram Bot

- `telegram_bot/config.py`
  - `BotSettings`
  - `BOT_CONFIG_PATH`
- `telegram_bot/handlers.py`
  - `start_command()`
  - `help_command()`
  - `handle_message()`
    - resolves active project from shared `uploads/config/bot_config.json`, then falls back to `BOT_ACTIVE_PROJECT_ID` only if the shared config is unset
    - obtains JWT via `/auth/login` using `BOT_API_USERNAME/BOT_API_PASSWORD` (fallback to `AUTH_ADMIN_*`), which now provisions or syncs a DB-backed service account row on successful login
    - on `403/404`, auto-selects first accessible project for bot user, persists it to shared bot config, and retries once
- `telegram_bot/bot.py`
  - `print_bot_link()`
  - `setup_handlers()`
  - `main()`

## Runtime Flows

### Upload + Process

1. `POST /projects/{project_id}/documents` in `backend/routes/documents.py`
2. `DocumentController.upload_document()`
3. `FileService.save_upload_file()`
4. Celery `process_document_task()`
5. `DocumentLoaderService.load_document()`
6. `ChunkingService.chunk_document()`
7. `EmbeddingService.generate_embeddings()`
8. `VectorDBProvider.add_vectors()`

### Query

1. `POST /projects/{project_id}/query` in `backend/routes/query.py`
2. `QueryController.answer_query()`
3. `QueryService.search_similar_chunks()`
4. `EmbeddingService.generate_single_embedding()`
5. `VectorDBProvider.search()`
6. `AnswerService.generate_answer()`

### Project Reindex

1. `POST /projects/{project_id}/index`
2. Celery `index_project_task()`
3. Re-embed all `Chunk` rows for project
4. Re-push vectors to configured vector DB

## Ownership and Security Rules

- Ownership is derived from JWT-backed `current_user`, not request payloads.
- Retrieval depends on `owner_id` scoping.
- Vector search providers expect owner-aware filtering.
- Any change to retrieval/indexing must preserve `owner_id` in vector metadata.
- Any route calling `ProjectController.get_project()` or `DocumentController.get_document()` must pass `owner_id`.
- `POST /bot/config` now requires a real JWT-backed DB user and only accepts `active_project_id` values owned by that user.
- Configured `BOT_API_*` / `AUTH_ADMIN_*` service-account usernames are reserved from normal signup/password rotation, and successful service-account login keeps a matching DB user row available for `get_current_db_user()`.

## Review Findings

No currently open high-severity findings are tracked in this file after the latest fixes.

Recently fixed:

1. `backend/routes/projects.py`
   `index_project()` now passes JWT-derived `owner_id` before queueing reindexing.
2. `backend/routes/documents.py`
   `process_and_index_document()` now enforces owned-document access before queueing workflow.
3. `backend/tasks/data_indexing.py`
   Reindexing now persists `owner_id` in vector metadata so retrieval scoping remains valid.
4. `backend/main.py`
   CORS now uses `settings.cors_origins` instead of wildcard origins with credentials.
5. `backend/database/connection.py` and `backend/alembic/versions/20260416_01_add_users_and_project_owner.py`
   Schema bootstrapping now runs through Alembic, and the base migration was aligned with the current `users/projects/assets/chunks/celery_task_executions` schema instead of the stale `user_id/email/password_hash` layout.
6. `backend/database/models.py`, `backend/providers/vectordb/pgvector_provider.py`, and `backend/alembic/versions/20260420_01_convert_chunk_embedding_to_pgvector.py`
   `chunks.embedding` now stores native `pgvector` values, a migration converts old JSON embeddings to `vector`, and `PGVectorProvider` executes similarity search inside PostgreSQL only.
7. `backend/providers/vectordb/pgvector_provider.py` and `backend/alembic/versions/20260420_02_add_pgvector_hnsw_indexes.py`
  ANN indexing is now dimension-aware: HNSW expression indexes are created per embedding dimension, and pgvector queries match them via `vector_dims(...)` plus a cast to `vector(query_dim)` or `halfvec(query_dim)`.
8. `backend/config.py` and `backend/flowerconfig.py`
   Runtime startup no longer fails when `CELERY_FLOWER_PASSWORD` is unset; the setting now defaults safely and Flower config reads it defensively.
9. `backend/providers/vectordb/pgvector_provider.py` and `backend/alembic/versions/20260420_02_add_pgvector_hnsw_indexes.py`
  HNSW indexes now use `vector` for dimensions `<= 2000` and `halfvec` for dimensions `<= 4000`; dimensions above that still use exact native pgvector search without ANN indexing.
10. `.dockerignore` and `docker/backend.Dockerfile`
  Docker builds now use a runtime-only context and copy only `backend/`, `telegram_bot/`, and required root config files; do not reintroduce `COPY . .` unless you also revisit build performance.
11. `docker/docker-compose.yml`
   Compose now builds the app image once as `ragmind-app:local`; `worker` and `telegram_bot` reuse that image instead of repeating the same build definition.
12. `scripts/dev/setup.bat`, `scripts/dev/start.bat`, and `scripts/dev/stop.bat`
   These are the only supported local entry scripts; when consolidating script behavior, remove stale helpers instead of keeping multiple overlapping launch paths. `start.bat` should default to a fast `docker compose up -d` path and reserve `--build` for explicit rebuilds only.
13. `uploads/logs/`
  `setup.bat` writes `uploads/logs/setup.log`; `start.bat` writes `uploads/logs/start.log`, follows container output into `uploads/logs/docker_stack.log`, snapshots `docker compose ps` into `uploads/logs/docker_ps.log`, and redirects the local static frontend server to `uploads/logs/frontend.log`; `stop.bat` writes `uploads/logs/stop.log` and appends pre/post-stop stack state to `uploads/logs/docker_ps.log`.
14. `frontend/app.js`, `frontend/login.html`, and `frontend/signup.html`
   Frontend API autodiscovery now defaults to `http://localhost:8000` and probes port `8000` before legacy ports like `8101`; keep query-string and `localStorage` overrides intact for non-local environments.
15. `backend/utils/task_tracking.py`, `backend/utils/idempotency_manager.py`, `backend/routes/projects.py`, `backend/routes/documents.py`, `backend/tasks/data_indexing.py`, `backend/tasks/file_processing.py`, `backend/tasks/process_workflow.py`, and `backend/celery_app.py`
  Task ownership is now persisted by `celery_task_id` instead of relying on in-memory-only `_TASK_OWNER_MAP`, manual project reindex uses the default worker queue plus durable owner tracking, worker tasks reuse the pre-created execution row instead of duplicating it, duplicate historical rows are merged away by `celery_task_id`, and `process-and-index` parent workflows now finalize from child-task reconciliation instead of needing `/tasks/{id}` polling to reach a terminal state.
16. `backend/providers/llm/factory.py` and `backend/routes/app_config.py`
  Embedding provider alias handling is now consistent: `get_available_embedding_providers()` is registry-backed, so aliases like `hf-bge-m3` pass `/config/providers` validation and match factory capabilities.
17. `backend/providers/llm/factory.py`
  `gemini-2.5-lite-flash` now resolves through a dedicated lite builder, ensuring explicit lite provider selection uses `settings.gemini_lite_model` instead of falling back to the standard Gemini model.
18. `backend/providers/llm/gemini_provider.py`
  Gemini embedding dimension is no longer hardcoded to `768`; it now infers by embedding model (`gemini-embedding-001` -> `3072`, `text-embedding-004` -> `768`) and updates dynamically from real embedding responses.
19. `backend/routes/documents.py`, `backend/routes/projects.py`, `backend/routes/query.py`, `backend/routes/stats.py`, and `backend/routes/bot_config.py`
  Route-level unexpected exceptions are now logged server-side and return sanitized client messages (for example `Internal server error`) instead of leaking raw `detail=str(e)` internals.
20. `backend/security/middleware.py` and `backend/config.py`
  Rate limiting now keys authenticated traffic by JWT subject (`user:<sub>`) with IP fallback to reduce shared-IP bottlenecks, and default throughput caps were raised (`chat` and `upload` request/in-flight limits) while retaining endpoint-specific throttling.
21. `backend/config.py`, `.env`, and `.env.example`
  The default Google LLM model was switched to `gemma-4-26b-a4b-it` (via `GEMINI_MODEL`) while keeping the provider as `gemini`, so new and local setups use Gemma 4 by default in Google AI Studio-backed flows.
22. `backend/shared_config_paths.py`, `backend/runtime_config.py`, `backend/routes/bot_config.py`, `telegram_bot/config.py`, `telegram_bot/handlers.py`, and `docker/docker-compose.yml`
  Runtime app/bot config now resolves through shared files under `uploads/config/`, Compose passes `RAGMIND_SHARED_CONFIG_DIR` to backend/worker/bot and mounts `uploads/` into the bot, the hardcoded `BOT_ACTIVE_PROJECT_ID` compose override was removed, `/bot/config` now requires an authenticated DB user plus owned-project validation, and the bot idles instead of crash-looping when `TELEGRAM_BOT_TOKEN` is blank.
23. `backend/security/auth.py` and `backend/services/auth_service.py`
  `BOT_API_*` and `AUTH_ADMIN_*` credentials now act as managed service accounts during `/auth/login`: successful login provisions or syncs a DB-backed user row so JWT subjects continue to resolve through `get_current_db_user()`, and those reserved usernames are blocked from normal signup/password rotation.
24. `docker/docker-compose.yml` and `backend/tasks/maintenance.py`
  Compose now runs a dedicated Celery beat scheduler service (`ragmind-scheduler`) so periodic cleanup tasks like `clean_celery_executions_table()` are actually scheduled in the default local stack.
25. `backend/providers/vectordb/interface.py`, `backend/providers/vectordb/pgvector_provider.py`, `backend/providers/vectordb/qdrant_provider.py`, and `backend/tasks/file_processing.py`
  Targeted stale-vector cleanup is now available across vector providers: `delete_vectors(...)` deletes by metadata filter, and document-processing retries/failures now clear old vectors for the current asset before rebuilding chunks/embeddings.
26. `backend/routes/health.py` and `scripts/dev/start.bat`
  Startup readiness now reflects the actual stack: `/health` returns `healthy` only when database, broker, result backend, Celery worker, shared config, and vector store are reachable, and `start.bat` waits for that JSON-ready state instead of any HTTP 200.

## Known Drift Between Docs and Code

- `README.md` is not fully aligned with current implementation.
- Security/auth ownership constraints are stronger in code than in README.
- Celery/background-task paths are central in code and should be trusted over README summaries.
- Runtime-config-driven retrieval behavior exists in code and is not fully captured in README.
- Alembic migrations must stay in sync with `backend/database/models.py`; do not assume old revisions reflect current field names.

## Update Rules For This File

Update `AGENTS.md` immediately when any of the following changes:

- new route/controller/service/provider/task is added
- method signatures change
- ownership/auth flow changes
- vector metadata shape changes
- runtime flags change retrieval/indexing behavior
- new known bug is discovered or fixed
- frontend entrypoint/API flow changes materially

When updating:

1. Keep this file concise.
2. Prefer bullets and short path-based references.
3. Remove stale entries, do not only append.
4. Add the critical path first, details second.
5. If a section becomes too large, summarize and point to the code paths.

## Practical Guidance For Future Agents

- Before editing retrieval or indexing, inspect:
  - `backend/services/query_service.py`
  - `backend/tasks/data_indexing.py`
  - `backend/tasks/file_processing.py`
  - `backend/providers/vectordb/*`
- Before editing auth/security, inspect:
  - `backend/security/auth.py`
  - `backend/routes/auth.py`
  - `backend/security/middleware.py`
  - `backend/services/login_security_service.py`
- Before editing uploads/documents, inspect:
  - `backend/routes/documents.py`
  - `backend/controllers/document_controller.py`
  - `backend/services/file_service.py`
  - `backend/services/document_loader.py`
  - `backend/services/chunking_service.py`

## Bottom Line

Yes, maintaining a repo-aware `AGENTS.md` with a concise code graph and update rules is a modern and useful workflow, especially for agent-assisted development. The important part is that it must stay short, code-grounded, and updated with every structural change, otherwise it becomes another stale doc that increases token cost instead of reducing it.

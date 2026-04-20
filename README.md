# RAGMind

RAGMind is a Retrieval Augmented Generation (RAG) platform for turning uploaded documents into searchable project knowledge bases.

It combines a FastAPI backend, background processing with Celery, vector search with pgvector or Qdrant, and a lightweight static frontend.

## Current Stack

- Backend: FastAPI + SQLAlchemy (async)
- Background jobs: Celery + RabbitMQ + Redis
- Databases: PostgreSQL (with pgvector) and optional Qdrant
- Frontend: static HTML/CSS/JS served locally on port 8080
- Bot: optional Telegram bot service

## Architecture At A Glance

1. Upload document to a project.
2. Celery worker extracts text, chunks content, and generates embeddings.
3. Vectors are written to the active vector provider.
4. Query endpoint retrieves relevant chunks and sends context to the configured LLM provider.
5. Response is returned with source context.

Code entry points:

- Backend app: backend/main.py
- Celery app: backend/celery_app.py
- Bot: telegram_bot/bot.py
- Frontend runtime logic: frontend/app.js

## Quick Start (Windows)

### Prerequisites

- Docker Desktop (Linux containers)
- WSL2 enabled for Docker Desktop
- Python 3.11+ for local tooling
- uv (optional but recommended for faster environment setup)

### 1. Clone

```powershell
git clone https://github.com/ZozElwakil/RAGMind---EELU-Project.git
cd RAGMind---EELU-Project
```

### 2. Setup

```powershell
scripts\dev\setup.bat
```

What setup does:

- creates or repairs venv
- installs backend dependencies from backend/requirements.txt (using `uv` when available, with `pip` fallback)
- creates .env from .env.example when missing
- creates uploads, tmp, and logs directories
- validates docker compose config when Docker is ready (`docker compose` or `docker-compose`)

### 3. Configure Environment

Edit .env and set provider credentials you plan to use.

Common required values:

- GEMINI_API_KEY (if using Gemini provider)
- COHERE_API_KEY or VOYAGE_API_KEY (if using those embedding providers)
- TELEGRAM_BOT_TOKEN (only if running bot features)

### 4. Start The Local Stack

```powershell
scripts\dev\start.bat
```

Use rebuild mode only when Docker image inputs changed:

```powershell
scripts\dev\start.bat --build
```

Default URLs:

- Frontend login: [http://localhost:8080/login.html?api=http://localhost:8000](http://localhost:8080/login.html?api=http://localhost:8000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- Health: [http://localhost:8000/health](http://localhost:8000/health)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Stop

```powershell
scripts\dev\stop.bat
```

## Dev Scripts

All supported local scripts are under scripts/dev.

| Script | Purpose | Key behavior | Logs |
| --- | --- | --- | --- |
| scripts/dev/setup.bat | Prepare local environment | Creates venv, installs deps, initializes .env | uploads/logs/setup.log |
| scripts/dev/start.bat | Start backend stack and frontend server | Uses docker compose up -d by default; supports --build | uploads/logs/start.log, uploads/logs/docker_stack.log, uploads/logs/docker_ps.log, uploads/logs/frontend.log |
| scripts/dev/stop.bat | Stop stack and close helper windows | Stops compose services and captures stack state | uploads/logs/stop.log, uploads/logs/docker_ps.log |

## Docker And WSL Troubleshooting (Windows)

If Docker Desktop shows errors like:

- WSL integration with distro Ubuntu unexpectedly stopped
- Wsl/Service/CreateInstance/E_FAIL

Use this sequence:

1. Close Docker Desktop.
2. Run: wsl --shutdown
3. Run: wsl --update
4. Start Docker Desktop again and wait until Engine is ready.
5. In Docker Desktop settings, toggle Ubuntu integration off/on under Resources > WSL Integration.
6. Retry scripts/dev/start.bat.

The scripts now print WSL-specific hints when this failure mode is detected.

## Runtime Services And Ports

- backend: 8000
- postgres (host mapped): 5435
- qdrant (host mapped): 6381
- rabbitmq AMQP: 5729
- rabbitmq management: 15672
- redis: 6383
- local frontend static server: 8080

## Database Migrations (Alembic)

Database initialization runs migrations via Alembic during backend startup.
Manual commands are still useful when working directly with schema changes.

Upgrade:

```powershell
alembic -c backend/alembic/alembic.ini upgrade head
```

Rollback one revision:

```powershell
alembic -c backend/alembic/alembic.ini downgrade -1
```

## API Reference

- Route inventory: backend/ENDPOINTS.md
- Interactive docs: /docs when backend is running

## Smoke Test

Run the end-to-end smoke test against a running backend:

```powershell
python tools/test_all.py
```

Optional environment variables:

- RAGMIND_BASE_URL
- RAGMIND_REQUEST_TIMEOUT
- RAGMIND_PROCESSING_TIMEOUT
- RAGMIND_STRICT_QUERY

## Repository Layout

```text
backend/        FastAPI app, routes, services, providers, tasks
backend/templates/ Prompt templates used by answer and query services
docker/         Dockerfile and docker-compose setup
frontend/       Static dashboard/login UI
telegram_bot/   Telegram bot integration
scripts/dev/    setup/start/stop scripts for local Windows workflow
backend/alembic/ Database migration revisions
docs/notes/     reports and long-form notes (non-runtime docs)
tools/          Utility scripts, including smoke test
uploads/        Local uploaded files and runtime logs under uploads/logs/
tmp/            Generated local artifacts
```

## Repository Hygiene

- Keep repository root for operational files only (runtime config, compose/build files, licenses, and primary docs like README).
- Move analysis reports and long-form notes under `docs/notes/` instead of adding them to root.
- Current report files live in `docs/notes/report.md` and `docs/notes/report-2.md`.

## License

MIT. See LICENSE.

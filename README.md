# RAGMind

RAGMind is a B2B SaaS Retrieval Augmented Generation (RAG) platform for turning uploaded company documents into searchable project knowledge bases and Telegram customer-support bots.

It combines a FastAPI backend, background processing with Celery, vector search with pgvector or Qdrant, and a lightweight static frontend.

## Current Stack

- Backend: FastAPI + SQLAlchemy (async)
- Background jobs: Celery + RabbitMQ + Redis
- Databases: PostgreSQL (with pgvector) and optional Qdrant
- Frontend: static HTML/CSS/JS served locally on port 8080
- Product roles: `company_admin` and `platform_owner`
- Telegram support: database-backed bot integrations plus durable conversations
- Legacy bot: optional single-bot service kept for demo/backward compatibility

## Architecture At A Glance

1. Upload document to a project.
2. Celery worker extracts text, chunks content, and generates embeddings.
3. Vectors are written to the active vector provider.
4. Query endpoint retrieves relevant chunks and sends context to the configured LLM provider.
5. Response is returned with source context for dashboard testing.
6. Production Telegram webhooks resolve a bot integration, persist the customer conversation, reuse the same RAG stack with `owner_id`/`project_id` scoping, and hide sources from customers by default.

Code entry points:

- Backend app: backend/main.py
- Celery app: backend/celery_app.py
- Legacy bot: telegram_bot/bot.py
- Production Telegram routes: backend/routes/bot_integrations.py, backend/routes/telegram_webhook.py, backend/routes/conversations.py
- Platform owner routes: backend/routes/admin_console.py
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
- OPENROUTER_API_KEY (if using OpenRouter Gemini, Free, or Gemma 4 26B A4B providers)
- GROQ_API_KEY (if using Groq Llama 3.3)
- CEREBRAS_API_KEY (if using Cerebras Llama 3.1)
- COHERE_API_KEY (if using Cohere embeddings)
- BOT_TOKEN_ENCRYPTION_KEY (required before saving production Telegram bot integrations)
- PUBLIC_WEBHOOK_BASE_URL (public HTTPS backend URL used to register Telegram webhooks)
- PLATFORM_OWNER_USERNAME (username promoted to platform_owner after login)
- TELEGRAM_BOT_TOKEN (legacy single-bot service only)

Generate a Fernet encryption key for bot tokens:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

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

Production Telegram endpoints:

- `POST /bot-integrations/` creates a company-owned Telegram bot integration for an owned project.
- `POST /telegram/webhook/{integration_id}/{webhook_secret}` receives Telegram updates for exactly one integration.
- `GET /conversations/` and related routes power the company support inbox.
- `/admin/*` routes are platform-owner-only and return `403` for normal company users.

The legacy `/bot/config` and `telegram_bot/` active-project flow remains for demo compatibility only. It must not be used for multi-company production support behavior.

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
telegram_bot/   Legacy single-bot integration
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

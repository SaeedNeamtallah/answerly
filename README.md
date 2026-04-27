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

### 3. 🏢 Corporate Knowledge Hub
For HR and IT departments to automate internal support.
*   **Scenario**: Storing company policies, insurance documents, and IT troubleshooting guides.
*   **Action**: Employee asks "How do I claim dental insurance?" via Telegram Bot.
*   **Outcome**: Instant instructions with links to the relevant forms found in the "Employee Handbook 2024".

---

## 🛠️ System Architecture

RAGMind follows a modern, decoupled microservices-ready architecture using the **Factory Pattern** for provider flexibility.

```mermaid
graph TD
    subgraph Frontend ["User Interfaces"]
        UI[Web Dashboard]
        TG[Telegram Bot]
    end

    subgraph Backend ["FastAPI Application Layer"]
        API[API Routes]
        Auth[Auth Middleware]
        
        subgraph Services ["Core Services"]
            Loader[Document Loader]
            Chunker[Text Splitter]
            Embedder[Embedding Service]
            Retriever[Query Service]
            GenAI[LLM Answer Service]
        end
    end

    subgraph Data ["Persistence Layer"]
        PG[(PostgreSQL + pgvector)]
        FS[File Storage]
        Qdrant[(Qdrant Vector DB)]
    end

    subgraph Monitoring ["Monitoring Stack"]
        Prom[Prometheus]
        Graf[Grafana]
    end

    UI -->|HTTP/REST| API
    TG -->|Webhook| API
    
    API --> Services
    
    Loader -->|Raw Text| Chunker
    Chunker -->|Chunks| Embedder
    Embedder -->|Vectors| PG
    Embedder -->|Vectors| Qdrant
    
    Retriever <-->|Semantic Search| PG
    Retriever <-->|Semantic Search| Qdrant
    
    GenAI <-->|Inference| Gemini[Google Gemini API]

    API -->|/metrics| Prom
    Prom -->|Data Source| Graf
```

---

## ⚙️ The Technical Pipeline (Deep Dive)

The system processes data through a strict **ETL (Extract, Transform, Load)** pipeline optimized for RAG.

### Phase 1: Ingestion & Chunking
1.  **File Upload**: Supports PDF, DOCX, TXT. Files are validated for MIME type and size.
2.  **Text Extraction**: content is stripped of non-printable characters.
3.  **Recursive Chunking**:
    *   Strategy: `RecursiveCharacterTextSplitter`
    *   Configuration: `chunk_size=1000`, `chunk_overlap=200`
    *   **Why?**: This preserves semantic context by keeping paragraphs together while ensuring chunks fit within the embedding model's context window.

### Phase 2: Vectorization (Embedding)
1.  **Model**: `models/gemini-embedding-001` (Google).
2.  **Dimension**: 768-dimensional dense vectors.
3.  **Batching**: Chunks are processed in batches (default: 10) to respect API rate limits.

### Phase 3: Retrieval & Generation (The "RAG" Loop)
1.  **Query Embedding**: User query is converted to a vector using the same model.
2.  **Similarity Search**:
    *   Metric: Cosine Similarity (via `pgvector` or `Qdrant`).
    *   Top-K: Retrieves the top 5 most relevant distinct chunks.
3.  **Prompt Engineering**:
    *   System constructs a prompt containing: "Context: [Retrieved Chunks] + Question: [User Query]".
    *   Instruction: "Answer based ONLY on the context provided."
4.  **Generation**:
    *   Model: `Gemini 2.5 Flash` (or configured model).
    *   Output: Streaming text response.

#### Query Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant API as FASTAPI
    participant V as VectorDB
    participant L as LLM (Gemini)
    
    U->>API: POST /query "Summarize the intro"
    
    Note over API: 1. Generate Query Embedding
    API->>L: Embed("Summarize the intro")
    L-->>API: Vector[0.12, -0.4, ...]
    
    Note over API: 2. Semantic Search
    API->>V: Search(Vector, Limit=5)
    V-->>API: Returns [Chunk A, Chunk B, Chunk C]
    
    Note over API: 3. Construct Context Prompt
    API->>L: Generate(Context + Question)
    L-->>API: "The introduction covers..."
    
    API->>U: Final Answer
```

---

## 💻 Tech Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Backend Framework** | **FastAPI** | High-performance async Python framework. |
| **LLM Provider** | **Google Gemini** | Using `gemini-2.0-flash` (configurable) for reasoning. |
| **Embeddings** | **Titan/Gemini** | `gemini-embedding-001` for vector representation. |
| **Vector Database** | **PostgreSQL (pgvector)** | Relational + Vector data in one place. Optional Qdrant support. |
| **ORM** | **SQLAlchemy** | Async ORM for database interactions. |
| **Task Queue** | **AsyncIO** | Python's native async/await for non-blocking operations. |
| **Frontend** | **Vanilla JS/CSS** | Lightweight, clean UI without complex build steps. |
| **Monitoring** | **Prometheus + Grafana** | Real-time metrics collection and visualization. |

---

## 📊 Monitoring & Observability

RAGMind includes a full monitoring stack powered by **Prometheus** and **Grafana** that tracks the health and performance of the entire system in real-time.

### Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin123 |

### Metrics Collected

| Category | Metrics |
|----------|---------|
| **API** | Request count, latency, error rate per endpoint |
| **Database** | Table counts, row counts per table |
| **Qdrant** | Vector collections count, vectors per collection |
| **System** | CPU usage %, RAM usage %, Disk usage % |
| **RAG** | LLM latency, Qdrant search latency, token usage |

### Grafana Dashboards

| Dashboard | Description |
|-----------|-------------|
| **FastAPI Observability** | Request rate, average duration, PR99 latency, error % |
| **Node Exporter Full** | System CPU, RAM, Disk, Network |
| **PostgreSQL Exporter** | DB connections, transactions, query performance |

### How It Works

```mermaid
graph LR
    A[FastAPI Backend] -->|exposes /metrics| B[Prometheus]
    B -->|scrapes every 5s| B
    B -->|data source| C[Grafana]
    C -->|visualizes| D[Dashboards]
```

1. The FastAPI backend exposes a `/metrics` endpoint using `prometheus-fastapi-instrumentator`.
2. A custom middleware tracks every request — method, endpoint, status code, and duration.
3. Background tasks collect DB, Qdrant, and system metrics every 5 seconds.
4. Prometheus scrapes the `/metrics` endpoint automatically.
5. Grafana reads from Prometheus and displays real-time dashboards.

### Quick Start Monitoring

```powershell
# Start all services including Prometheus and Grafana
.\start_docker.bat

# Start the backend
.\start_backend.bat
```

Then open **http://localhost:3000** → Login → Go to Dashboards.

---

## 📦 Installation & Setup

### Prerequisites
*   Python 3.8+
*   PostgreSQL 14+ (with `vector` extension installed)
*   Docker Desktop
*   A Google Cloud API Key (for Gemini)

- Docker Desktop (Linux containers)
- WSL2 enabled for Docker Desktop
- Python 3.11+ for local tooling
- uv (optional but recommended for faster environment setup)

### 1. Clone

2.  **Environment Config**:
    Open `.env` and paste your keys:
    ```env
    DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/ragmind
    GEMINI_API_KEY=AIzaSy...
    ```

3.  **Initialize DB**:
    ```powershell
    python -m backend.init_database
    ```

4.  **Run**:
    ```powershell
    .\start_docker.bat
    .\start_backend.bat
    ```

Visit **http://localhost:8001** to use the application.
Visit **http://localhost:3000** for Grafana dashboards.

---

## 📂 Project Structure

```bash
RAGMind/
├── backend/
│   ├── monitoring/        # Prometheus metrics (db, vector, system, llm)
│   ├── services/          # Business logic (RAG, Chunking, Parsing)
│   ├── providers/         # Interfaces for LLMs and VectorDBs
│   ├── routes/            # API Endpoints
│   ├── database/          # SQLAlchemy models and connection
│   └── main.py            # App entry point
├── docker/
│   └── docker-compose.yml # PostgreSQL, Qdrant, RabbitMQ, Redis, Prometheus, Grafana
├── frontend/              # Web UI (HTML/JS/CSS)
├── telegram_bot/          # Telegram Bot integration code
├── prometheus.yml         # Prometheus scrape configuration
├── uploads/               # Temporary storage for documents
└── scripts/               # .bat helper scripts
```

### 2. Setup

```powershell
scripts\dev\setup.bat
```

*   **Abdulmoezz Elwakil** ([@ZozElwakil](https://github.com/ZozElwakil)) - Core Logic & Architecture
*   **Fares Hakim** ([@fareshakim1](https://github.com/fareshakim1)) - Monitoring & Observability (Prometheus + Grafana)

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

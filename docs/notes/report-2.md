# Report 2: Unused Code & Critical Codebase Issues

This report details features and code that are implemented but not actively used, along with critical design, logic, and software architectural issues discovered during the codebase analysis.

## 1. Implemented Features Not Used & Useless Code
Despite having a functional platform, several blocks of code are either completely unused ghosts or redundant duplications:

*   **Duplicate Tool Scripts (`tools/`)**
    There are duplicate scripts acting as dead weight: `tools/combine_code.py` and `tools/combinecode.py` are identical files (same byte size). One of them is completely redundant and should be removed.
*   **Phantom Frontend Roles**
    In `frontend/app.js`, role mappings are fully implemented for `ROLE_ADMIN` and `ROLE_CYBERSECURITY_ENGINEER`. The Javascript specifically checks for these roles to configure the dashboard token payloads. However, there are no dedicated administrator or engineer UI templates (e.g., `admin.html`) built out. The roles are implemented in logic but point to ghost features in the UI.
*   **Redundant Database Imports and Variables**
    Static analysis reveals imported structural types `Float` and `LargeBinary` in `backend/database/models.py` which are never utilized, suggesting legacy or aborted attempts to store files/scores directly in Postgres. Additionally, variables like `telegram_admin_id` in `config.py` are declared but rarely leveraged within core workflows.

## 2. Critical Issues (Architecture, Design, Software, Logical)

> [!CAUTION]
> **Database Vector Storage Architecture (Critical Design / Arch. Issue)**
> In `backend/database/models.py`, `Chunk.embedding` is defined as a `JSON` column: `Column(JSON, nullable=True)`. Storing dense, high-dimensional vector embeddings as raw JSON arrays in a PostgreSQL relational table is a severe design flaw. 
> * **Impact**: This drastically inflates the row size of the `chunks` table. Any query fetching chunks (even just to read the text) forces the database to load massive JSON objects into memory. Since the system already delegates vector queries to a dedicated engine (`Qdrant`), mirroring embeddings into Postgres as JSON creates massive storage overhead and I/O bottlenecks without providing search utility.

> [!WARNING]
> **Aggressive Database Cleanup Schedule (Software / Logical Issue)**
> In `backend/celery_app.py`, the scheduled Celery beat task `cleanup-old-task-records` (which calls `clean_celery_executions_table` in `maintenance.py` to prune the `celery_task_executions` tracking table) is configured to run every **10 seconds** (`"schedule": 10`). 
> * **Impact**: Executing a table prune query every 10 seconds generates aggressive, unnecessary database thrashing. It can trigger lock contentions, excessive log writing, and transaction overhead. This should be a daily or hourly chronological cleanup, not a near real-time polling loop.

> [!NOTE]
> **Hardcoded LLM Factory Scaling (Design Issue)**
> The `LLMProviderFactory` (`backend/providers/llm/factory.py`) violates the **Open/Closed Principle**. Dozens of explicit `if provider_name == "..."` conditions are hardcoded to instantiate standard OpenRouter/Groq/Cerebras clients via `OpenAICompatProvider`. 
> * **Impact**: Whenever the administrators want to test a new model from an OpenAI-compatible endpoint, a developer must modify and redeploy the factory Python code. This should be refactored into a dynamic registry or database configuration mapping rather than hardcoded logic blocks.

> [!IMPORTANT]
> **Admin Authentication Bypass Vulnerabilities Surface (Logical Issue)**
> The route definitions and middleware expose functions like `authenticate_admin`, but they lack strict mapping enforcement from end-to-end. Without the accompanying UI panel to test and properly dogfood the "Admin" flows, there is a risk that newly written routes might lack the secondary `Roles` check boundary, relying strictly on standard valid JWT keys (meaning regular users could inadvertently hit administrative APIs).

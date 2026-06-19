# System Architecture and Flow Diagrams

This document contains Mermaid diagrams visualizing the system architecture, database schema, and key execution flows.

## 1. System Architecture

```mermaid
graph TD
    Frontend["Next.js frontend-next\n(Port 3001)"] --> ApiClient["lib/api"]
    ApiClient --> Routes["FastAPI Routes\n(Port 8000)"]
    Telegram["Telegram Webhook"] --> Routes

    subgraph Backend [Backend Stack]
        Routes --> Security["Security / Auth / Access"]
        Routes --> Controllers["Controllers"]
        Controllers --> Services["Services"]
        Services --> Providers["LLM / Vector Providers"]
        Services --> Database["PostgreSQL + pgvector"]
        Routes --> Celery["Celery Tasks\n(Worker Port 9108)"]
        Celery --> Database
        Celery --> Providers
    end

    Providers --> ExternalLLM["External LLM APIs\n(Gemini, Cohere, OpenRouter)"]
    Providers --> Qdrant["Qdrant\n(Optional)"]
    Services --> RuntimeConfig["uploads/config"]
```

## 2. Database Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    users ||--o{ projects : "owns"
    users ||--o{ bot_integrations : "owns/creates"
    users ||--o{ telegram_customers : "owns"
    users ||--o{ conversations : "owns/assigned"
    users ||--o{ conversation_messages : "owns/sends"
    users ||--o{ incidents : "causes/assigned"
    users ||--o{ incident_logs : "creates"
    users ||--o{ audit_logs : "performs/targets"
    users ||--o{ role_assignment_history : "targets/performs"
    users ||--o{ security_events : "triggers"

    projects ||--o{ assets : "contains"
    projects ||--o{ chunks : "contains"
    projects ||--o{ bot_integrations : "has"
    projects ||--o{ conversations : "has"

    assets ||--o{ chunks : "composed of"

    bot_integrations ||--o{ telegram_customers : "serves"
    bot_integrations ||--o{ conversations : "manages"
    bot_integrations ||--o{ conversation_messages : "has"

    telegram_customers ||--o{ conversations : "participates"
    telegram_customers ||--o{ conversation_messages : "receives/sends"

    conversations ||--o{ conversation_messages : "contains"

    incidents ||--o{ incident_logs : "has"

    celery_task_executions {
        int execution_id
        string task_name
        string status
    }
```

## 3. Upload and Process Document Flow

```mermaid
sequenceDiagram
    participant User
    participant Route as backend/routes/documents.py
    participant Controller as DocumentController
    participant Service as FileService
    participant Celery as process_document_task
    participant Loader as DocumentLoaderService
    participant Chunker as ChunkingService
    participant Embedder as EmbeddingService
    participant VectorDB as VectorDBProvider

    User->>Route: POST /projects/{id}/documents
    Route->>Controller: upload_document()
    Controller->>Service: save_upload_file()
    Service-->>Controller: saved file info
    Controller->>Celery: Enqueue process_document_task()
    Controller-->>User: 202 Accepted (Processing)

    Celery->>Loader: load_document()
    Loader-->>Celery: raw text
    Celery->>Chunker: chunk_document()
    Chunker-->>Celery: chunks
    Celery->>Embedder: generate_embeddings()
    Embedder-->>Celery: embeddings
    Celery->>VectorDB: add_vectors()
    VectorDB-->>Celery: success
```

## 4. Production Telegram Customer Query Flow

```mermaid
sequenceDiagram
    participant Telegram
    participant Route as /telegram/webhook/*
    participant WebhookService as TelegramWebhookService
    participant ConvService as ConversationService
    participant Celery as Query Task
    participant Controller as QueryController
    participant Embedder as EmbeddingService
    participant VectorDB as VectorDBProvider
    participant Answer as AnswerService
    participant Outbox as Outbox Task
    participant API as TelegramAPIService

    Telegram->>Route: POST Update
    Route->>WebhookService: process_update
    WebhookService->>ConvService: Persist customer/message
    WebhookService->>Celery: Enqueue generate_bot_reply
    Route-->>Telegram: 200 OK (Fast Ack)

    Celery->>Controller: answer_query(owner_id, project_id)
    Controller->>Embedder: generate_single_embedding()
    Embedder-->>Controller: embedding vector
    Controller->>VectorDB: search(vector, owner_id)
    VectorDB-->>Controller: context chunks
    Controller->>Answer: generate_answer(chunks)
    Answer-->>Celery: reply text
    Celery->>ConvService: Save reply (delivery_status="pending")

    Outbox->>Outbox: Lease pending messages
    Outbox->>API: send_message
    API->>Telegram: Send reply
    API-->>Outbox: success
    Outbox->>ConvService: Mark as delivered
```

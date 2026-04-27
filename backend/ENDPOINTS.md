# Backend Endpoints

This file lists the API endpoints defined in `backend/routes` and included in `backend/main.py`.

It does not include FastAPI's built-in documentation routes such as `/docs`, `/redoc`, or `/openapi.json`.

`backend/routes/alerts.py` is currently not mounted in `backend/main.py`, so it has no active HTTP endpoints.

## Health

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/` | Root endpoint that returns API name, version, and helpful links. | `backend/routes/health.py::root` |
| GET | `/health` | Full readiness check for database, queues, worker, shared config, and vector store. | `backend/routes/health.py::health_check` |

## Authentication

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| POST | `/auth/signup` | Create a new user account. | `backend/routes/auth.py::signup` |
| POST | `/auth/login` | Authenticate user credentials and return an access token. | `backend/routes/auth.py::login` |
| GET | `/auth/me` | Return the currently authenticated user identity, DB-backed product role, account status, and company profile fields. | `backend/routes/auth.py::me` |
| POST | `/auth/change-password` | Change password for the authenticated user. | `backend/routes/auth.py::change_password` |
| POST | `/auth/update-password` | Alias of change-password for compatibility. | `backend/routes/auth.py::change_password` |

## Projects

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| POST | `/projects/` | Create a new project. | `backend/routes/projects.py::create_project` |
| GET | `/projects/` | List projects with pagination via `skip` and `limit`. | `backend/routes/projects.py::list_projects` |
| GET | `/projects/{project_id}` | Get a single project by ID. | `backend/routes/projects.py::get_project` |
| POST | `/projects/{project_id}/index` | Trigger project-level reindexing via Celery. | `backend/routes/projects.py::index_project` |
| GET | `/projects/{project_id}/stats` | Get statistics for one project. | `backend/routes/projects.py::get_project_stats` |
| PUT | `/projects/{project_id}` | Update a project. | `backend/routes/projects.py::update_project` |
| DELETE | `/projects/{project_id}` | Delete a project and related data. | `backend/routes/projects.py::delete_project` |

## Documents

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| POST | `/projects/{project_id}/documents` | Upload a document to a project and queue background processing. | `backend/routes/documents.py::upload_document` |
| GET | `/projects/{project_id}/documents` | List all documents for a project. | `backend/routes/documents.py::list_project_documents` |
| GET | `/documents/{asset_id}` | Get a single document by asset ID. | `backend/routes/documents.py::get_document` |
| POST | `/documents/{asset_id}/process` | Manually trigger document processing. | `backend/routes/documents.py::process_document` |
| POST | `/documents/{asset_id}/process-and-index` | Run the process-and-index workflow for a document. | `backend/routes/documents.py::process_and_index_document` |
| DELETE | `/documents/{asset_id}` | Delete a document. | `backend/routes/documents.py::delete_document` |
| GET | `/tasks/{task_id}` | Check the status of a Celery task. | `backend/routes/documents.py::get_task_status` |

## Query

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| POST | `/projects/{project_id}/query` | Ask a question about project documents and get an answer with sources. | `backend/routes/query.py::query_project` |

## Bot Integrations

Production Telegram support uses database-backed bot integrations. All routes below require an authenticated dashboard user and filter by `owner_id == current_user.id`; Telegram bot tokens are accepted on create/rotation only and are never returned. Webhook secrets are not returned directly or through webhook URLs; responses expose only `webhook_configured`.

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/bot-integrations/` | List the current company's Telegram bot integrations. | `backend/routes/bot_integrations.py::list_bot_integrations` |
| POST | `/bot-integrations/` | Validate a Telegram bot token, encrypt it, link it to an owned project, and configure the webhook server-side when available. | `backend/routes/bot_integrations.py::create_bot_integration` |
| GET | `/bot-integrations/{integration_id}` | Get one owned bot integration. | `backend/routes/bot_integrations.py::get_bot_integration` |
| PATCH | `/bot-integrations/{integration_id}` | Update integration name, linked owned project, source visibility, handoff, or fallback message. | `backend/routes/bot_integrations.py::update_bot_integration` |
| PUT | `/bot-integrations/{integration_id}` | Alias for updating integration settings. | `backend/routes/bot_integrations.py::update_bot_integration` |
| POST | `/bot-integrations/{integration_id}/rotate-token` | Validate and rotate an integration token. | `backend/routes/bot_integrations.py::rotate_bot_token` |
| POST | `/bot-integrations/{integration_id}/enable` | Mark an owned integration active. | `backend/routes/bot_integrations.py::enable_bot_integration` |
| POST | `/bot-integrations/{integration_id}/disable` | Disable an owned integration. | `backend/routes/bot_integrations.py::disable_bot_integration` |
| GET | `/bot-integrations/{integration_id}/readiness` | Return readiness checks for token, webhook, project ownership, chunks, status, and last error. | `backend/routes/bot_integrations.py::bot_integration_readiness` |
| POST | `/bot-integrations/{integration_id}/test` | Alias for readiness checks. | `backend/routes/bot_integrations.py::bot_integration_readiness` |
| DELETE | `/bot-integrations/{integration_id}` | Delete an owned integration and attempt webhook cleanup. | `backend/routes/bot_integrations.py::delete_bot_integration` |

## Telegram Webhook

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| POST | `/telegram/webhook/{integration_id}/{webhook_secret}` | Receive Telegram updates, resolve one bot integration, persist customer/conversation/messages, answer through the linked project RAG stack, and save the bot reply. | `backend/routes/telegram_webhook.py::telegram_webhook` |

## Conversations

All conversation routes require an authenticated dashboard user and filter by `owner_id == current_user.id`.

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/conversations/` | List owned Telegram conversations with optional `status` and `needs_human` filters. | `backend/routes/conversations.py::list_conversations` |
| GET | `/conversations/{conversation_id}` | Get one owned conversation. | `backend/routes/conversations.py::get_conversation` |
| GET | `/conversations/{conversation_id}/messages` | List messages for one owned conversation. | `backend/routes/conversations.py::list_conversation_messages` |
| POST | `/conversations/{conversation_id}/reply` | Send a manual agent reply through the linked bot and persist it. | `backend/routes/conversations.py::manual_reply` |
| POST | `/conversations/{conversation_id}/assign-self` | Assign the conversation to the current company admin. | `backend/routes/conversations.py::assign_conversation_to_self` |
| POST | `/conversations/{conversation_id}/assign` | Alias for assigning the conversation to the current company admin. | `backend/routes/conversations.py::assign_conversation_to_self` |
| POST | `/conversations/{conversation_id}/escalate` | Mark the conversation escalated and needing human help. | `backend/routes/conversations.py::escalate_conversation` |
| POST | `/conversations/{conversation_id}/resolve` | Mark the conversation resolved. | `backend/routes/conversations.py::resolve_conversation` |
| POST | `/conversations/{conversation_id}/block` | Block the Telegram customer and mark the conversation blocked. | `backend/routes/conversations.py::block_customer` |
| POST | `/conversations/{conversation_id}/block-customer` | Alias for blocking the Telegram customer. | `backend/routes/conversations.py::block_customer` |

## Admin Console

All routes in this section require DB-backed `platform_owner` role via `require_platform_owner_access`; non-platform owners receive `403`.

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/admin/overview` | Cross-company counts for companies, projects, bot integrations, conversations, and recent messages. | `backend/routes/admin_console.py::admin_overview` |
| GET | `/admin/stats` | Alias for platform overview stats. | `backend/routes/admin_console.py::admin_stats` |
| GET | `/admin/companies` | List company/platform users with project, bot, and conversation counts. | `backend/routes/admin_console.py::list_admin_companies` |
| GET | `/admin/companies/{company_id}` | Get one company account with resource counts. | `backend/routes/admin_console.py::get_admin_company` |
| GET | `/admin/companies/{company_id}/projects` | List projects owned by one company. | `backend/routes/admin_console.py::list_admin_company_projects` |
| GET | `/admin/companies/{company_id}/bot-integrations` | List bot integrations owned by one company. | `backend/routes/admin_console.py::list_admin_company_bot_integrations` |
| GET | `/admin/companies/{company_id}/conversations` | List conversations owned by one company. | `backend/routes/admin_console.py::list_admin_company_conversations` |
| GET | `/admin/bot-integrations` | List all bot integrations across companies. | `backend/routes/admin_console.py::list_admin_bot_integrations` |
| GET | `/admin/conversations` | List all conversations across companies, with optional `status` filter. | `backend/routes/admin_console.py::list_admin_conversations` |
| GET | `/admin/conversations/{conversation_id}` | Get any conversation by ID. | `backend/routes/admin_console.py::get_admin_conversation` |
| GET | `/admin/conversations/{conversation_id}/messages` | List messages for any conversation. | `backend/routes/admin_console.py::list_admin_conversation_messages` |
| POST | `/admin/companies/{company_id}/activate` | Restore a company account to active status. | `backend/routes/admin_console.py::activate_company` |
| POST | `/admin/companies/{company_id}/suspend` | Suspend a company account. | `backend/routes/admin_console.py::suspend_company` |
| POST | `/admin/companies/{company_id}/block` | Block a company account. | `backend/routes/admin_console.py::block_company` |

## Stats

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/stats/` | Get global counts for projects, documents, and chunks. | `backend/routes/stats.py::get_global_stats` |

## Security

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/security/stats` | Return aggregated security counters for the dashboard. | `backend/routes/security.py::security_stats` |
| GET | `/security/events` | Return recent security events. | `backend/routes/security.py::security_events` |
| POST | `/security/simulate` | Generate demo security events for dashboard testing. | `backend/routes/security.py::simulate_security_attack` |
| GET | `/security/events/stream` | Stream security events and stats via SSE. | `backend/routes/security.py::security_events_stream` |

## Legacy Bot Config

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/bot/config` | Get deprecated demo bot configuration. Response includes a deprecation warning. | `backend/routes/bot_config.py::get_bot_config` |
| POST | `/bot/config` | Update deprecated demo bot configuration. Production flows must use `/bot-integrations`. | `backend/routes/bot_config.py::update_bot_config` |
| POST | `/bot/profile` | Legacy single-bot profile update. Production integrations should rotate/update through database-backed flows. | `backend/routes/bot_config.py::update_bot_profile` |

## App Config

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/config/providers` | Return available providers and current runtime selections. | `backend/routes/app_config.py::get_providers` |
| POST | `/config/providers` | Update runtime provider selections. | `backend/routes/app_config.py::update_providers` |

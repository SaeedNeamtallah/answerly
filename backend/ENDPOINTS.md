# Backend Endpoints

This file lists the API endpoints defined in `backend/routes` and included in `backend/main.py`.

It does not include FastAPI's built-in documentation routes such as `/docs`, `/redoc`, or `/openapi.json`.

`backend/routes/alerts.py` is currently not mounted in `backend/main.py`, so it has no active HTTP endpoints.

## Health

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/` | Root endpoint that returns API name, version, and helpful links. | `backend/routes/health.py::root` |
| GET | `/health` | Health check with database and provider status. | `backend/routes/health.py::health_check` |

## Authentication

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| POST | `/auth/signup` | Create a new user account. | `backend/routes/auth.py::signup` |
| POST | `/auth/login` | Authenticate user credentials and return an access token. | `backend/routes/auth.py::login` |
| GET | `/auth/me` | Return the currently authenticated user identity. | `backend/routes/auth.py::me` |
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

## Bot Config

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/bot/config` | Get the current Telegram bot configuration. | `backend/routes/bot_config.py::get_bot_config` |
| POST | `/bot/config` | Update the bot configuration. | `backend/routes/bot_config.py::update_bot_config` |
| POST | `/bot/profile` | Update the Telegram bot profile name. | `backend/routes/bot_config.py::update_bot_profile` |

## App Config

| Method | Path | Description | Source |
| --- | --- | --- | --- |
| GET | `/config/providers` | Return available providers and current runtime selections. | `backend/routes/app_config.py::get_providers` |
| POST | `/config/providers` | Update runtime provider selections. | `backend/routes/app_config.py::update_providers` |

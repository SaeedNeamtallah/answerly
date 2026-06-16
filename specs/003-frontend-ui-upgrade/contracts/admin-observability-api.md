# Contract: Platform Owner Observability

The observability page is a platform-owner feature. The frontend must not call Grafana or Prometheus with credentials directly. Backend routes must require the same platform-owner access boundary as existing `/admin/*` product-console routes.

## Existing Infrastructure Inputs

Provisioned dashboards:

- `ragmind-overview` - RAGMind Overview
- `fastapi-observability-18739` - FastAPI Observability
- `postgres-exporter-12485` - Postgres exporter dashboard
- `node-exporter-full-1860` - Node exporter dashboard

Prometheus jobs from `docker/prometheus.yml`:

- `prometheus`
- `ragmind-backend`
- `postgres`
- `node`
- `qdrant`
- `celery-worker`

## GET `/admin/observability/dashboards`

Returns the dashboard catalog.

### Response

```json
{
  "grafana_base_url": "http://127.0.0.1:3000",
  "embedding_enabled": false,
  "dashboards": [
    {
      "uid": "ragmind-overview",
      "title": "RAGMind Overview",
      "category": "application",
      "description": "Application, retrieval, Celery, and integration health.",
      "open_url": "http://127.0.0.1:3000/d/ragmind-overview",
      "embed_url": null,
      "status": "available"
    }
  ]
}
```

### Rules

- Requires platform-owner access.
- Dashboard uid values must come from an allowlist.
- `embed_url` is present only when embedding is explicitly configured.
- Missing Grafana returns catalog items with `status: "unavailable"` and a safe message.

## GET `/admin/observability/summary`

Returns curated health and metric summary for the selected time range.

### Query Parameters

- `range`: Allowed values `1h`, `24h`, `7d`. Default `1h`.

### Response

```json
{
  "range": "1h",
  "generated_at": "2026-06-13T00:00:00Z",
  "health": {
    "status": "healthy",
    "database": "connected",
    "broker": "connected",
    "result_backend": "connected",
    "celery_worker": "connected",
    "shared_config": "ready",
    "vector_store": "connected"
  },
  "targets": [
    {
      "job": "ragmind-backend",
      "state": "up",
      "last_scrape": "2026-06-13T00:00:00Z"
    }
  ],
  "metrics": {
    "request_rate_per_second": 0,
    "p95_latency_seconds": 0,
    "five_xx_count": 0,
    "query_failures": 0,
    "embedding_errors": 0,
    "telegram_webhook_failures": 0,
    "celery_task_p95_seconds": 0
  },
  "unavailable": []
}
```

### Rules

- Requires platform-owner access.
- Prometheus queries must be curated or allowlisted.
- Backend must return unavailable metric names instead of failing the whole response.
- The response must never include infrastructure passwords, tokens, or raw secret-bearing URLs.

## Frontend Behavior

- Add an admin navigation item for Observability or upgrade the existing Stats page into Observability.
- Show a dashboard switcher for the catalog.
- Show a health/target summary above dashboard panels.
- If embedding is enabled, show the selected dashboard in a framed, responsive viewer.
- If embedding is unavailable, show a high-quality fallback card with summary metrics and an "Open in Grafana" action.
- Keep the page useful when Grafana or Prometheus is down.

## Tests

- Backend route dependency test confirms platform-owner access.
- Backend response tests cover dashboard catalog, summary success, and Prometheus/Grafana unavailable states.
- Frontend tests or browser smoke checks confirm dashboard switching, fallback rendering, and forbidden access for non-platform users.

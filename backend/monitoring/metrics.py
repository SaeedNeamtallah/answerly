"""Minimal Prometheus metrics for the backend API.

This module is intentionally isolated from application services so monitoring
cannot change auth, retrieval, indexing, or startup behavior.
"""
from __future__ import annotations

import time

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the backend.",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

DOCUMENT_PROCESSING_TOTAL = Counter(
    "document_processing_total",
    "Document processing outcomes.",
    ["status"],
)

EMBEDDING_PROVIDER_ERRORS_TOTAL = Counter(
    "embedding_provider_errors_total",
    "Embedding provider failures by provider and error class.",
    ["provider", "error"],
)

QUERY_FAILURES_TOTAL = Counter(
    "query_failures_total",
    "Query pipeline failures.",
    ["stage"],
)

CELERY_TASK_DURATION_SECONDS = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds.",
    ["task_name", "status"],
    buckets=(0.1, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300, 600),
)

TELEGRAM_WEBHOOK_FAILURES_TOTAL = Counter(
    "telegram_webhook_failures_total",
    "Telegram webhook processing failures.",
    ["reason"],
)

INCIDENTS_CREATED_TOTAL = Counter(
    "incidents_created_total",
    "Incidents created by severity.",
    ["severity"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Record request count and latency without touching response bodies."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        status_code = "500"

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            return response
        finally:
            if request.url.path != "/metrics":
                route = request.scope.get("route")
                endpoint = getattr(route, "path", request.url.path)
                HTTP_REQUESTS_TOTAL.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=status_code,
                ).inc()
                HTTP_REQUEST_DURATION_SECONDS.labels(
                    method=request.method,
                    endpoint=endpoint,
                ).observe(time.perf_counter() - start_time)


def register_metrics(app: FastAPI) -> None:
    """Attach Prometheus middleware and expose a scrape endpoint."""

    app.add_middleware(PrometheusMiddleware)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

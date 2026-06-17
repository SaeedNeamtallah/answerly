"""Minimal Prometheus metrics for the backend API.

This module is intentionally isolated from application services so monitoring
cannot change auth, retrieval, indexing, or startup behavior.
"""
from __future__ import annotations

import ipaddress
import os
import time

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.config import settings


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


# Internal/trusted networks for /metrics access control
_TRUSTED_NETWORKS = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
)


def _is_trusted_ip(ip_str: str) -> bool:
    """Return True if *ip_str* belongs to a trusted internal network."""
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in _TRUSTED_NETWORKS)
    except ValueError:
        return False


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
                if route:
                    endpoint = getattr(route, "path", "__unknown__")
                else:
                    endpoint = "__unknown__"
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
    async def metrics(request: Request) -> Response:
        metrics_token = os.environ.get("METRICS_AUTH_TOKEN", "").strip()
        auth_header = request.headers.get("Authorization", "")
        has_valid_token = bool(metrics_token and auth_header == f"Bearer {metrics_token}")

        if settings.environment.lower() == "production":
            # In production, require the auth token strictly, ignoring client IPs
            if has_valid_token:
                return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
            return Response("Forbidden", status_code=403)
        else:
            # In other environments, allow trusted internal IPs or valid token
            client_ip = request.client.host if request.client else ""
            if _is_trusted_ip(client_ip) or has_valid_token:
                return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
            return Response("Forbidden", status_code=403)

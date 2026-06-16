"""Platform observability integration for Grafana and Prometheus."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DashboardDefinition:
    uid: str
    title: str
    slug: str
    category: str
    description: str


DASHBOARD_CATALOG: tuple[DashboardDefinition, ...] = (
    DashboardDefinition(
        uid="ragmind-overview",
        title="RAGMind Overview",
        slug="ragmind-overview",
        category="application",
        description="Backend, query pipeline, Celery, Qdrant, and incident health.",
    ),
    DashboardDefinition(
        uid="fastapi-observability-18739",
        title="FastAPI Observability",
        slug="fastapi-observability",
        category="api",
        description="Request volume, status mix, endpoint latency, and API saturation.",
    ),
    DashboardDefinition(
        uid="postgres-exporter-12485",
        title="PostgreSQL Exporter",
        slug="postgresql-exporter",
        category="database",
        description="Database connections, transaction rate, locks, buffers, and storage.",
    ),
    DashboardDefinition(
        uid="node-exporter-full-1860",
        title="Node Exporter Full",
        slug="node-exporter-full",
        category="infrastructure",
        description="Host CPU, memory, storage, process, and network telemetry.",
    ),
)

EXPECTED_PROMETHEUS_JOBS: tuple[tuple[str, str], ...] = (
    ("ragmind-backend", "Backend API"),
    ("postgres", "Postgres Exporter"),
    ("node", "Node Exporter"),
    ("qdrant", "Qdrant"),
    ("celery-worker", "Celery Worker"),
    ("prometheus", "Prometheus"),
)

PROMETHEUS_QUERIES: tuple[dict[str, str], ...] = (
    {
        "key": "backend_request_rate",
        "label": "Backend RPS",
        "unit": "requests_per_second",
        "query": "sum(rate(http_requests_total[5m]))",
        "description": "Current FastAPI request rate over 5 minutes.",
    },
    {
        "key": "backend_p95_latency",
        "label": "Backend P95",
        "unit": "seconds",
        "query": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
        "description": "95th percentile backend latency over 5 minutes.",
    },
    {
        "key": "backend_5xx_rate",
        "label": "5xx Rate",
        "unit": "requests_per_second",
        "query": 'sum(rate(http_requests_total{status_code=~"5.."}[5m]))',
        "description": "Server error rate over 5 minutes.",
    },
    {
        "key": "query_failures",
        "label": "Query Failures",
        "unit": "count",
        "query": "sum(increase(query_failures_total[1h]))",
        "description": "Query pipeline failures in the last hour.",
    },
    {
        "key": "document_failures",
        "label": "Document Failures",
        "unit": "count",
        "query": 'sum(increase(document_processing_total{status!="success"}[1h]))',
        "description": "Document processing failures in the last hour.",
    },
    {
        "key": "celery_p95_duration",
        "label": "Celery P95",
        "unit": "seconds",
        "query": "histogram_quantile(0.95, sum(rate(celery_task_duration_seconds_bucket[5m])) by (le))",
        "description": "95th percentile Celery task duration over 5 minutes.",
    },
)


def _clean_base_url(value: str) -> str:
    return str(value or "").strip().rstrip("/")


def _safe_range(value: str | None) -> str:
    normalized = str(value or "1h").strip().lower()
    return normalized if normalized in {"1h", "6h", "24h", "7d"} else "1h"


def _grafana_from_value(time_range: str) -> str:
    return f"now-{_safe_range(time_range)}"


def _extract_prometheus_value(payload: dict[str, Any]) -> float | None:
    result = payload.get("data", {}).get("result", [])
    if not result:
        return None

    value = result[0].get("value")
    if not isinstance(value, list) or len(value) < 2:
        return None

    try:
        return float(value[1])
    except (TypeError, ValueError):
        return None


class ObservabilityService:
    """Read-only integration with configured monitoring services."""

    def __init__(
        self,
        *,
        prometheus_base_url: str | None = None,
        grafana_public_url: str | None = None,
        grafana_internal_url: str | None = None,
        grafana_embed_enabled: bool | None = None,
        grafana_dashboard_org_id: int | None = None,
    ) -> None:
        prometheus_url = prometheus_base_url if prometheus_base_url is not None else settings.prometheus_base_url
        public_url = grafana_public_url if grafana_public_url is not None else settings.grafana_public_url
        self.prometheus_base_url = _clean_base_url(prometheus_url)
        self.grafana_public_url = _clean_base_url(public_url)
        internal_url = grafana_internal_url if grafana_internal_url is not None else settings.grafana_internal_url
        self.grafana_internal_url = _clean_base_url(internal_url or self.grafana_public_url)
        self.grafana_embed_enabled = (
            settings.grafana_embed_enabled if grafana_embed_enabled is None else bool(grafana_embed_enabled)
        )
        self.grafana_dashboard_org_id = int(grafana_dashboard_org_id or settings.grafana_dashboard_org_id)

    def list_dashboards(self, time_range: str = "1h") -> list[dict[str, Any]]:
        """Return allowlisted Grafana dashboards with server-approved browser URLs."""

        from_value = _grafana_from_value(time_range)
        dashboards: list[dict[str, Any]] = []
        for dashboard in DASHBOARD_CATALOG:
            url = (
                f"{self.grafana_public_url}/d/{dashboard.uid}/{dashboard.slug}"
                f"?orgId={self.grafana_dashboard_org_id}&from={from_value}&to=now&theme=light"
            )
            embed_url = f"{url}&kiosk" if self.grafana_embed_enabled else None
            dashboards.append(
                {
                    "uid": dashboard.uid,
                    "title": dashboard.title,
                    "category": dashboard.category,
                    "description": dashboard.description,
                    "url": url,
                    "embed_url": embed_url,
                }
            )
        return dashboards

    async def build_summary(self, time_range: str = "1h") -> dict[str, Any]:
        safe_range = _safe_range(time_range)
        grafana, prometheus, targets, metrics = await self._collect_monitoring_state()
        return {
            "range": safe_range,
            "generated_at": datetime.now(timezone.utc),
            "grafana": grafana,
            "prometheus": prometheus,
            "targets": targets,
            "metrics": metrics,
        }

    async def _collect_monitoring_state(self) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        async with httpx.AsyncClient(timeout=4.0) as client:
            grafana = await self._probe_grafana(client)
            targets_payload = await self._get_prometheus_json(client, "/api/v1/targets")
            prometheus = {
                "status": "ready" if targets_payload is not None else "unavailable",
                "base_url_configured": bool(self.prometheus_base_url),
            }
            targets = self._serialize_targets(targets_payload)
            metrics = await self._collect_metrics(client) if targets_payload is not None else self._empty_metrics("unavailable")
            return grafana, prometheus, targets, metrics

    async def _probe_grafana(self, client: httpx.AsyncClient) -> dict[str, Any]:
        payload = await self._get_json(client, self.grafana_internal_url, "/api/health")
        if payload is None:
            return {
                "status": "unavailable",
                "public_url": self.grafana_public_url,
                "embedding_enabled": self.grafana_embed_enabled,
            }

        database_status = str(payload.get("database") or "").lower()
        status = "ready" if database_status == "ok" or payload.get("commit") else "degraded"
        return {
            "status": status,
            "public_url": self.grafana_public_url,
            "embedding_enabled": self.grafana_embed_enabled,
            "version": payload.get("version"),
            "database": payload.get("database"),
        }

    async def _get_prometheus_json(
        self,
        client: httpx.AsyncClient,
        path: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        if not self.prometheus_base_url:
            return None
        return await self._get_json(client, self.prometheus_base_url, path, params=params)

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        path: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        if not base_url:
            return None

        try:
            response = await client.get(f"{base_url}{path}", params=params)
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else None
        except Exception as exc:
            safe_url = re.sub(r"//([^/@]+)@", "//***@", base_url)
            logger.debug("Observability probe failed for %s%s: %s", safe_url, path, exc)
            return None

    def _serialize_targets(self, payload: dict[str, Any] | None) -> list[dict[str, Any]]:
        by_job = {
            job: {
                "job": job,
                "label": label,
                "health": "unknown",
                "last_scrape": None,
                "scrape_url": None,
                "last_error": None,
            }
            for job, label in EXPECTED_PROMETHEUS_JOBS
        }

        active_targets = (payload or {}).get("data", {}).get("activeTargets", [])
        if not isinstance(active_targets, list):
            return list(by_job.values())

        for target in active_targets:
            labels = target.get("labels", {}) if isinstance(target, dict) else {}
            discovered_labels = target.get("discoveredLabels", {}) if isinstance(target, dict) else {}
            job = labels.get("job") or discovered_labels.get("__meta_job") or target.get("scrapePool")
            if job not in by_job:
                continue

            health = str(target.get("health") or "unknown").lower()
            by_job[job].update(
                {
                    "health": "ready" if health == "up" else "unavailable",
                    "last_scrape": target.get("lastScrape"),
                    "scrape_url": target.get("scrapeUrl"),
                    "last_error": target.get("lastError") or None,
                }
            )

        return list(by_job.values())

    async def _collect_metrics(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        metrics: list[dict[str, Any]] = []
        for definition in PROMETHEUS_QUERIES:
            payload = await self._get_prometheus_json(
                client,
                "/api/v1/query",
                params={"query": definition["query"]},
            )
            value = _extract_prometheus_value(payload or {}) if payload is not None else None
            metrics.append(
                {
                    "key": definition["key"],
                    "label": definition["label"],
                    "unit": definition["unit"],
                    "value": value,
                    "status": "ready" if value is not None else "unavailable",
                    "description": definition["description"],
                }
            )
        return metrics

    def _empty_metrics(self, status: str) -> list[dict[str, Any]]:
        return [
            {
                "key": definition["key"],
                "label": definition["label"],
                "unit": definition["unit"],
                "value": None,
                "status": status,
                "description": definition["description"],
            }
            for definition in PROMETHEUS_QUERIES
        ]

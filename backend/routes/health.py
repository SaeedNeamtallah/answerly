"""
Health Check Routes.
API endpoints for system health monitoring.
"""
import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.celery_app import celery_app
from backend.config import settings
from backend.database import get_db
from backend.runtime_config import get_runtime_value
from backend.services.embedding_service import EmbeddingService
from backend.shared_config_paths import get_app_config_path, get_bot_config_path

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    database: str
    broker: str
    result_backend: str
    celery_worker: str
    shared_config: str
    vector_store: str
    llm_provider: str
    embedding_provider: str
    embedding_provider_health: str
    vector_db_provider: str


def _default_port_for_scheme(scheme: str) -> int | None:
    return {
        "amqp": 5672,
        "amqps": 5671,
        "redis": 6379,
        "rediss": 6380,
        "http": 80,
        "https": 443,
    }.get((scheme or "").lower())


async def _probe_tcp_endpoint(raw_url: str) -> str:
    try:
        if raw_url.startswith("path://"):
            path = Path(raw_url.replace("path://", "", 1)).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            return "connected"

        parsed = urlparse(raw_url)
        host = parsed.hostname
        port = parsed.port or _default_port_for_scheme(parsed.scheme)
        if not host or not port:
            return "disconnected"

        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=2,
        )
        writer.close()
        await writer.wait_closed()
        return "connected"
    except Exception as exc:
        logger.debug("Health probe failed for %s: %s", raw_url, exc)
        return "disconnected"


async def _probe_celery_worker() -> str:
    def _ping_workers():
        inspector = celery_app.control.inspect(timeout=3.0)
        replies = inspector.ping() or {}
        if replies:
            return replies

        # Fallback for environments where inspect ping is flaky but workers are alive.
        stats = inspector.stats() or {}
        return stats

    try:
        replies = await asyncio.wait_for(asyncio.to_thread(_ping_workers), timeout=6)
        return "connected" if replies else "disconnected"
    except Exception as exc:
        logger.debug("Celery worker health probe failed: %s", exc)
        return "disconnected"


async def _probe_celery_worker_deep() -> str:
    """Run the deeper worker probe used by /health/full for internal monitoring."""
    return await _probe_celery_worker()


async def _probe_shared_config() -> str:
    try:
        app_config_path = get_app_config_path()
        bot_config_path = get_bot_config_path()
        app_config_path.parent.mkdir(parents=True, exist_ok=True)
        bot_config_path.parent.mkdir(parents=True, exist_ok=True)
        return "ready"
    except Exception as exc:
        logger.debug("Shared config health probe failed: %s", exc)
        return "unavailable"


async def _probe_vector_store(database_status: str) -> str:
    if settings.vector_db_provider == "qdrant":
        return await _probe_tcp_endpoint(settings.qdrant_url)
    return "connected" if database_status == "connected" else "disconnected"


async def _probe_embedding_provider() -> str:
    try:
        service = EmbeddingService()
        ok = await asyncio.wait_for(service.health_check(), timeout=35)
        return "connected" if ok else "disconnected"
    except Exception as exc:
        logger.warning("Embedding provider health probe failed: %s", exc)
        return "disconnected"


async def _build_health_response(db: AsyncSession, include_deep_checks: bool) -> dict:
    """Build a fast readiness response and optionally run the deeper Celery worker probe."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        logger.debug("Database health probe failed: %s", exc)
        db_status = "disconnected"

    broker_status, result_backend_status, shared_config_status, vector_store_status = (
        await asyncio.gather(
            _probe_tcp_endpoint(settings.celery_broker_url),
            _probe_tcp_endpoint(settings.celery_result_backend),
            _probe_shared_config(),
            _probe_vector_store(db_status),
        )
    )
    if include_deep_checks and broker_status == "connected":
        celery_worker_status, embedding_provider_health = await asyncio.gather(
            _probe_celery_worker_deep(),
            _probe_embedding_provider(),
        )
    else:
        # Keep the default health path fast so UI discovery does not wait on worker inspection.
        celery_worker_status = "skipped"
        embedding_provider_health = "skipped"

    overall_status = "healthy"
    if not all(
        (
            db_status == "connected",
            broker_status == "connected",
            result_backend_status == "connected",
            shared_config_status == "ready",
            vector_store_status == "connected",
            embedding_provider_health in ("connected", "skipped"),
        )
    ):
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "database": db_status,
        "broker": broker_status,
        "result_backend": result_backend_status,
        "celery_worker": celery_worker_status,
        "shared_config": shared_config_status,
        "vector_store": vector_store_status,
        "llm_provider": get_runtime_value("llm_provider", settings.llm_provider),
        "embedding_provider": get_runtime_value("embedding_provider", settings.embedding_provider),
        "embedding_provider_health": embedding_provider_health,
        "vector_db_provider": get_runtime_value("vector_db_provider", settings.vector_db_provider),
    }


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Fast readiness check used by UI startup and API discovery."""
    return await _build_health_response(db, include_deep_checks=False)


@router.get("/health/live")
async def health_live():
    return {"status": "alive"}


@router.get("/health/full", response_model=HealthResponse)
async def health_check_full(db: AsyncSession = Depends(get_db)):
    """Deeper health check for internal monitoring and diagnostics."""
    return await _build_health_response(db, include_deep_checks=True)


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
    }

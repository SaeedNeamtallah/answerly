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
        inspector = celery_app.control.inspect(timeout=1.0)
        return inspector.ping() or {}

    try:
        replies = await asyncio.wait_for(asyncio.to_thread(_ping_workers), timeout=3)
        return "connected" if replies else "disconnected"
    except Exception as exc:
        logger.debug("Celery worker health probe failed: %s", exc)
        return "disconnected"


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


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check full system readiness status."""
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
    celery_worker_status = (
        await _probe_celery_worker() if broker_status == "connected" else "disconnected"
    )

    overall_status = "healthy"
    if not all(
        (
            db_status == "connected",
            broker_status == "connected",
            result_backend_status == "connected",
            celery_worker_status == "connected",
            shared_config_status == "ready",
            vector_store_status == "connected",
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
        "llm_provider": settings.llm_provider,
        "vector_db_provider": settings.vector_db_provider,
    }


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
    }

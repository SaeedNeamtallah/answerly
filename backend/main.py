"""
Main FastAPI Application.
RAGMind Backend with Monitoring (Enhanced Version)
"""

import asyncio
import logging
import time
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager

from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator

from backend.config import settings
from backend.database.connection import init_db, close_db, async_session_maker
from backend.monitoring import db_metrics, vector_metrics, system_metrics
from backend.monitoring import db_metrics, vector_metrics, system_metrics
# ------------------------
# 🧠 RAG Specific Metrics
# ------------------------
LLM_LATENCY = Gauge('rag_llm_latency_seconds', 'Time spent in LLM API call')
VECTOR_DB_LATENCY = Gauge('rag_qdrant_search_seconds', 'Time spent in Vector DB search')
TOKEN_USAGE = Gauge('rag_token_usage_total', 'Total tokens consumed')

from backend.routes import (
    projects,
    documents,
    query,
    health,
    stats,
    bot_config,
    app_config
)

# ------------------------
# Logging
# ------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------------
# Prometheus General Metrics
# ------------------------
REQUEST_COUNT = Counter(
    "request_count_total",
    "Total API Requests",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
)

ERROR_COUNT = Counter(
    "error_count_total",
    "Total API Errors",
    ["method", "endpoint"]
)

# ------------------------
# Middleware
# ------------------------
async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
        status_code = response.status_code
        REQUEST_COUNT.labels(method=method, endpoint=path, http_status=status_code).inc()
        if status_code >= 400:
            ERROR_COUNT.labels(method=method, endpoint=path).inc()
        return response
    except Exception as e:
        ERROR_COUNT.labels(method=method, endpoint=path).inc()
        raise e
    finally:
        REQUEST_LATENCY.observe(time.time() - start_time)


# ------------------------
# Background Tasks (Metrics Updaters)
# ------------------------
async def db_metrics_updater():
    while True:
        try:
            await db_metrics.update_db_metrics(async_session_maker)
        except Exception as e:
            logger.warning(f"DB metrics update failed: {e}")
        await asyncio.sleep(5)

async def vector_metrics_updater():
    while True:
        try:
            await vector_metrics.update_vector_metrics()
        except Exception as e:
            logger.warning(f"Vector metrics update failed: {e}")
        await asyncio.sleep(10)

async def system_metrics_updater():
    while True:
        try:
            await system_metrics.update_system_metrics()
        except Exception as e:
            logger.warning(f"System metrics error: {e}")
        await asyncio.sleep(5)


# ------------------------
# Lifespan (Startup/Shutdown)
# ------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting RAGMind API with Enhanced Monitoring...")
    await init_db()

    # تشغيل مهام جمع الميتريكس في الخلفية
    db_task = asyncio.create_task(db_metrics_updater())
    vector_task = asyncio.create_task(vector_metrics_updater())
    system_task = asyncio.create_task(system_metrics_updater())

    yield

    logger.info("🛑 Shutting down...")
    db_task.cancel()
    vector_task.cancel()
    system_task.cancel()
    await close_db()


# ------------------------
# App Initialization
# ------------------------
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="RAGMind Backend with Advanced RAG Monitoring",
    lifespan=lifespan
)

# --- تفعيل الـ Instrumentator للمراقبة التلقائية ---
Instrumentator().instrument(app).expose(app)

# ------------------------
# Exception Handler
# ------------------------
@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logger.error(f"🔥 ERROR: {traceback.format_exc()}")
    ERROR_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    return PlainTextResponse("Internal Server Error", status_code=500)

# ------------------------
# Middleware Configuration
# ------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# تفعيل الميدل وير اليدوي
app.middleware("http")(monitoring_middleware)

# ------------------------
# Routes
# ------------------------
@app.get("/test")
def test():
    return {"message": "Server is alive and monitored!"}

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(stats.router)
app.include_router(security.router)
app.include_router(incidents.router)
app.include_router(admin_users.router)
app.include_router(admin_console.router)
app.include_router(bot_integrations.router)
app.include_router(conversations.router)
app.include_router(telegram_webhook.router)
app.include_router(bot_config.router)
app.include_router(app_config.router)
app.include_router(auth.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
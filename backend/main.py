"""
Main FastAPI Application.
Entry point for the RAGMind backend API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

try:
    from fastapi.responses import ORJSONResponse
    _default_response = ORJSONResponse
except ImportError:
    _default_response = None
# Configure logging
from backend.config import settings
import logging
from backend.security.middleware import SecurityRateLimitMiddleware
from backend.monitoring.metrics import register_metrics

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from backend.database import init_db, close_db
from backend.routes import (
    admin_console,
    admin_observability,
    admin_users,
    app_config,
    auth,
    bot_config,
    bot_integrations,
    conversations,
    documents,
    health,
    incidents,
    projects,
    query,
    security,
    stats,
    telegram_webhook,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting RAGMind API...")
    try:
        provider_state = app_config.normalize_provider_runtime_config()
        if provider_state.get("migrated"):
            logger.warning(
                "Migrated runtime provider config for fields: %s",
                ", ".join(provider_state.get("updated_fields", [])) or "none",
            )
    except Exception:
        logger.exception("Failed to normalize runtime provider config during startup")

    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAGMind API...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
_app_kwargs = dict(
    title=settings.api_title,
    version=settings.api_version,
    description="""
    RAGMind - Retrieval Augmented Generation System
    
    A powerful document processing and question-answering API using:
    - Google Gemini 2.5 Flash for LLM capabilities
    - PostgreSQL with pgvector for vector storage
    - LangChain for document processing
    
    ## Features
    - Project-based document organization
    - Multi-format document support (PDF, TXT, DOCX)
    - Automatic text chunking and embedding
    - Vector similarity search
    - AI-powered question answering
    - Multi-language support (Arabic/English)
    """,
    lifespan=lifespan
)
if _default_response:
    _app_kwargs['default_response_class'] = _default_response
app = FastAPI(**_app_kwargs)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware: global API throttling.
app.add_middleware(SecurityRateLimitMiddleware)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=500)

# Prometheus metrics endpoint and request instrumentation
register_metrics(app)

# Include routers
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(stats.router)
app.include_router(security.router)
app.include_router(incidents.router)
app.include_router(admin_users.router)
app.include_router(admin_console.router)
app.include_router(admin_observability.router)
app.include_router(bot_integrations.router)
app.include_router(conversations.router)
app.include_router(telegram_webhook.router)
app.include_router(bot_config.router)
app.include_router(app_config.router)
app.include_router(auth.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

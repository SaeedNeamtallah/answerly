"""
Configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration (Docker on port 5435)
    database_url: str = Field(
        default="postgresql+asyncpg://ragmind:ragmind123@localhost:5435/ragmind",
        alias="DATABASE_URL"
    )
    
    # LLM Provider Configuration
    gemini_api_key: str = Field(
        default="",
        alias="GEMINI_API_KEY"
    )
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_lite_model: str = Field(default="gemini-2.5-lite-flash", alias="GEMINI_LITE_MODEL")
    embedding_provider: str = Field(default="gemini", alias="EMBEDDING_PROVIDER")
    gemini_embed_model: str = Field(
        default="models/gemini-embedding-001",
        alias="GEMINI_EMBED_MODEL"
    )
    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")
    cohere_embed_model: str = Field(
        default="embed-multilingual-v3.0",
        alias="COHERE_EMBED_MODEL"
    )
    cohere_max_batch_tokens: int = Field(
        default=50000,
        alias="COHERE_MAX_BATCH_TOKENS"
    )
    cohere_max_retries: int = Field(
        default=12,
        alias="COHERE_MAX_RETRIES"
    )
    cohere_base_retry_delay: float = Field(
        default=2.0,
        alias="COHERE_BASE_RETRY_DELAY"
    )
    voyage_api_key: str = Field(default="", alias="VOYAGE_API_KEY")
    voyage_embed_model: str = Field(default="voyage-3-large", alias="VOYAGE_EMBED_MODEL")
    voyage_output_dimension: int = Field(default=1024, alias="VOYAGE_OUTPUT_DIMENSION")
    hf_embedding_model: str = Field(default="BAAI/bge-m3", alias="HF_EMBED_MODEL")
    # OpenAI-compatible LLM providers
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL"
    )
    openrouter_gemini_2_flash_model: str = Field(
        default="google/gemini-2.0-flash-001",
        alias="OPENROUTER_GEMINI_2_FLASH_MODEL"
    )
    openrouter_free_model: str = Field(
        default="openrouter/free",
        alias="OPENROUTER_FREE_MODEL"
    )
    openrouter_site_url: str = Field(default="", alias="OPENROUTER_SITE_URL")
    openrouter_app_name: str = Field(default="", alias="OPENROUTER_APP_NAME")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        alias="GROQ_BASE_URL"
    )
    groq_llama_3_3_70b_versatile_model: str = Field(
        default="llama-3.3-70b-versatile",
        alias="GROQ_LLAMA_3_3_70B_VERSATILE_MODEL"
    )
    groq_gpt_oss_120b_model: str = Field(
        default="gpt-oss-120b",
        alias="GROQ_GPT_OSS_120B_MODEL"
    )

    cerebras_api_key: str = Field(default="", alias="CEREBRAS_API_KEY")
    cerebras_base_url: str = Field(
        default="https://api.cerebras.ai/v1",
        alias="CEREBRAS_BASE_URL"
    )
    cerebras_llama_3_3_70b_model: str = Field(
        default="llama-3.3-70b",
        alias="CEREBRAS_LLAMA_3_3_70B_MODEL"
    )
    cerebras_llama_3_1_8b_model: str = Field(
        default="llama-3.1-8b",
        alias="CEREBRAS_LLAMA_3_1_8B_MODEL"
    )
    cerebras_gpt_oss_120b_model: str = Field(
        default="gpt-oss-120b",
        alias="CEREBRAS_GPT_OSS_120B_MODEL"
    )
    embedding_batch_size: int = Field(default=96, alias="EMBEDDING_BATCH_SIZE")
    embedding_concurrency: int = Field(default=4, alias="EMBEDDING_CONCURRENCY")
    voyage_max_batch_tokens: int = Field(default=120000, alias="VOYAGE_MAX_BATCH_TOKENS")
    
    # Vector DB Configuration
    vector_db_provider: str = Field(default="pgvector", alias="VECTOR_DB_PROVIDER")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_upsert_batch_size: int = Field(default=256, alias="QDRANT_UPSERT_BATCH_SIZE")
    
    # Storage Configuration
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_file_size_mb: int = Field(default=50, alias="MAX_FILE_SIZE_MB")
    
    # Chunking Configuration
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    parent_chunk_size: int = Field(default=3000, alias="PARENT_CHUNK_SIZE")
    parent_chunk_overlap: int = Field(default=600, alias="PARENT_CHUNK_OVERLAP")
    chunk_strategy: str = Field(default="parent_child", alias="CHUNK_STRATEGY")

    # Retrieval Configuration
    retrieval_top_k: int = Field(default=4, alias="RETRIEVAL_TOP_K")
    retrieval_top_k_max: int = Field(default=20, alias="RETRIEVAL_TOP_K_MAX")
    retrieval_candidate_k: int = Field(default=10, alias="RETRIEVAL_CANDIDATE_K")
    retrieval_hybrid_enabled: bool = Field(default=False, alias="RETRIEVAL_HYBRID_ENABLED")
    retrieval_hybrid_alpha: float = Field(default=0.7, alias="RETRIEVAL_HYBRID_ALPHA")
    retrieval_rerank_enabled: bool = Field(default=False, alias="RETRIEVAL_RERANK_ENABLED")
    retrieval_rerank_top_k: int = Field(default=10, alias="RETRIEVAL_RERANK_TOP_K")
    query_rewrite_enabled: bool = Field(default=False, alias="QUERY_REWRITE_ENABLED")
    retrieval_hnsw_ef_search: int = Field(default=40, alias="RETRIEVAL_HNSW_EF_SEARCH")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_title: str = Field(default="RAGMind API", alias="API_TITLE")
    api_version: str = Field(default="1.0.0", alias="API_VERSION")

    # Authentication and Security Configuration
    auth_jwt_secret_key: str = Field(default="change-me-in-env", alias="AUTH_JWT_SECRET_KEY")
    auth_jwt_algorithm: str = Field(default="HS256", alias="AUTH_JWT_ALGORITHM")
    auth_access_token_expire_minutes: int = Field(default=60, alias="AUTH_ACCESS_TOKEN_EXPIRE_MINUTES")
    auth_admin_username: str = Field(default="admin", alias="AUTH_ADMIN_USERNAME")
    auth_admin_password: str = Field(default="admin123", alias="AUTH_ADMIN_PASSWORD")
    auth_admin_password_hash: str = Field(default="", alias="AUTH_ADMIN_PASSWORD_HASH")
    security_require_auth_for_mutations: bool = Field(default=False, alias="SECURITY_REQUIRE_AUTH_FOR_MUTATIONS")
    security_user_suspension_default_minutes: int = Field(
        default=30,
        alias="SECURITY_USER_SUSPENSION_DEFAULT_MINUTES"
    )
    security_login_bruteforce_enabled: bool = Field(
        default=True,
        alias="SECURITY_LOGIN_BRUTEFORCE_ENABLED"
    )
    security_login_bruteforce_threshold: int = Field(
        default=5,
        alias="SECURITY_LOGIN_BRUTEFORCE_THRESHOLD"
    )
    security_login_bruteforce_window_seconds: int = Field(
        default=60,
        alias="SECURITY_LOGIN_BRUTEFORCE_WINDOW_SECONDS"
    )
    security_login_bruteforce_block_seconds: int = Field(
        default=300,
        alias="SECURITY_LOGIN_BRUTEFORCE_BLOCK_SECONDS"
    )
    security_cybersecurity_engineer_usernames: str = Field(
        default="",
        alias="SECURITY_CYBERSECURITY_ENGINEER_USERNAMES"
    )

    security_rate_limit_enabled: bool = Field(default=True, alias="SECURITY_RATE_LIMIT_ENABLED")
    security_rate_limit_global_enabled: bool = Field(default=False, alias="SECURITY_RATE_LIMIT_GLOBAL_ENABLED")
    security_rate_limit_requests_per_window: int = Field(
        default=300,
        alias="SECURITY_RATE_LIMIT_REQUESTS_PER_WINDOW"
    )
    security_rate_limit_window_seconds: int = Field(default=60, alias="SECURITY_RATE_LIMIT_WINDOW_SECONDS")
    security_rate_limit_exempt_paths: str = Field(
        default="/health,/docs,/openapi.json,/redoc",
        alias="SECURITY_RATE_LIMIT_EXEMPT_PATHS"
    )

    security_rate_limit_chat_requests_per_window: int = Field(
        default=90,
        alias="SECURITY_RATE_LIMIT_CHAT_REQUESTS_PER_WINDOW"
    )
    security_rate_limit_chat_window_seconds: int = Field(
        default=60,
        alias="SECURITY_RATE_LIMIT_CHAT_WINDOW_SECONDS"
    )
    security_rate_limit_chat_max_in_flight: int = Field(
        default=6,
        alias="SECURITY_RATE_LIMIT_CHAT_MAX_IN_FLIGHT"
    )

    security_rate_limit_upload_requests_per_window: int = Field(
        default=20,
        alias="SECURITY_RATE_LIMIT_UPLOAD_REQUESTS_PER_WINDOW"
    )
    security_rate_limit_upload_window_seconds: int = Field(
        default=60,
        alias="SECURITY_RATE_LIMIT_UPLOAD_WINDOW_SECONDS"
    )
    security_rate_limit_upload_max_in_flight: int = Field(
        default=4,
        alias="SECURITY_RATE_LIMIT_UPLOAD_MAX_IN_FLIGHT"
    )

    security_rate_limit_project_create_requests_per_window: int = Field(
        default=10,
        alias="SECURITY_RATE_LIMIT_PROJECT_CREATE_REQUESTS_PER_WINDOW"
    )
    security_rate_limit_project_create_window_seconds: int = Field(
        default=300,
        alias="SECURITY_RATE_LIMIT_PROJECT_CREATE_WINDOW_SECONDS"
    )
    security_rate_limit_project_create_max_in_flight: int = Field(
        default=2,
        alias="SECURITY_RATE_LIMIT_PROJECT_CREATE_MAX_IN_FLIGHT"
    )

    security_rate_limit_login_requests_per_window: int = Field(
        default=6,
        alias="SECURITY_RATE_LIMIT_LOGIN_REQUESTS_PER_WINDOW"
    )
    security_rate_limit_login_window_seconds: int = Field(
        default=60,
        alias="SECURITY_RATE_LIMIT_LOGIN_WINDOW_SECONDS"
    )
    security_rate_limit_login_max_in_flight: int = Field(
        default=2,
        alias="SECURITY_RATE_LIMIT_LOGIN_MAX_IN_FLIGHT"
    )

    security_upload_validate_magic: bool = Field(default=True, alias="SECURITY_UPLOAD_VALIDATE_MAGIC")
    security_upload_max_scan_bytes: int = Field(default=8192, alias="SECURITY_UPLOAD_MAX_SCAN_BYTES")
    
    # Telegram Bot Configuration
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_admin_id: str = Field(default="", alias="TELEGRAM_ADMIN_ID")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://52.188.226.80", "http://localhost:3000", "http://localhost:8080"],
        alias="CORS_ORIGINS"
    )
    
    # Celery Configuration
    celery_broker_url: str = Field(
        default="amqp://minirag_user:minirag_rabbitmq_2222@localhost:5729/minirag_vhost",
        alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://:minirag_redis_2222@localhost:6383/0",
        alias="CELERY_RESULT_BACKEND"
    )
    celery_task_serializer: str = Field(default="json", alias="CELERY_TASK_SERIALIZER")
    celery_task_time_limit: int = Field(default=600, alias="CELERY_TASK_TIME_LIMIT")
    celery_task_acks_late: bool = Field(default=True, alias="CELERY_TASK_ACKS_LATE")
    celery_worker_concurrency: int = Field(default=2, alias="CELERY_WORKER_CONCURRENCY")
    celery_flower_password: str = Field(default="", alias="CELERY_FLOWER_PASSWORD")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance - use default values if .env not found
try:
    settings = Settings()
except Exception as e:
    # If .env is missing, use defaults
    import warnings
    warnings.warn(f".env file not found or invalid, using default settings: {str(e)}")
    # In Pydantic v2, we can't just pass _env_file=None to the constructor easily if it fails
    # We'll try to create a default instance without loading from env
    try:
        settings = Settings(_env_file=None)
    except:
        # Fallback to a very basic settings if even that fails
        settings = Settings()

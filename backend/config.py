from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    # --- API META ---
    api_title: str = "RAGMind API"
    api_version: str = "1.0.0"

    # --- DATABASE (PostgreSQL) ---
    database_url: str

    # --- API KEYS ---
    google_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # --- LLM PROVIDERS & MODELS ---
    llm_provider: str = "gemini"
    embedding_provider: str = "gemini" 
    
    gemini_model: str = "gemini-1.5-flash" 
    gemini_lite_model: str = "gemini-1.5-flash-8b"
    gemini_embed_model: str = "models/text-embedding-004"

    # --- VECTOR DB (Qdrant) ---
    vector_db_provider: str = "qdrant"
    qdrant_url: str = "http://localhost:6381"  
    qdrant_api_key: Optional[str] = None
    # القيمة اللي كانت بتضرب معاك في الـ Provider
    qdrant_upsert_batch_size: int = 100

    # --- RETRIEVAL & CHUNKING ---
    chunk_strategy: str = "simple"   
    chunk_size: int = 500              
    chunk_overlap: int = 50           
    parent_chunk_size: int = 1000     
    parent_chunk_overlap: int = 200
    
    retrieval_top_k: int = 5
    retrieval_top_k_max: int = 20
    retrieval_candidate_k: int = 20
    retrieval_hybrid_enabled: bool = False
    retrieval_hybrid_alpha: float = 0.5
    retrieval_rerank_enabled: bool = False
    retrieval_rerank_top_k: int = 3
    query_rewrite_enabled: bool = False

    # --- EMBEDDING SERVICE ---
    # القيمة اللي صلحناها يدوي في الـ Service
    embedding_concurrency: int = 2
    embedding_batch_size: int = 100
    voyage_max_batch_tokens: int = 8000

    # --- LOGGING ---
    log_level: str = "INFO"

    # --- STORAGE SETTINGS ---
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50

    # --- CELERY & REDIS ---
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_task_serializer: str = "json"
    celery_task_time_limit: int = 600
    celery_task_acks_late: bool = True
    celery_worker_concurrency: int = 2

    class Config:
        env_file = ".env"
        extra = "ignore" # عشان لو فيه داتا زيادة في الـ .env ما تضربش الكود

settings = Settings()
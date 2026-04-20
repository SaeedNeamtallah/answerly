"""
Enumerations for supported vector database providers.
"""
from enum import Enum


class VectorDBProvider(str, Enum):
    PGVECTOR = "pgvector"
    QDRANT = "qdrant"

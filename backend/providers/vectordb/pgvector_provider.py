"""
PGVector Provider Implementation.
Uses PostgreSQL with pgvector extension for vector storage.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import cast, delete, func, select, text
from pgvector.sqlalchemy import Vector
from backend.providers.vectordb.interface import VectorDBInterface
from backend.database.models import Chunk, Project
from backend.database.connection import async_session_maker
from backend.config import settings
from backend.runtime_config import get_runtime_value
import logging

logger = logging.getLogger(__name__)


class PGVectorProvider(VectorDBInterface):
    """PostgreSQL pgvector implementation."""

    # SECURITY RULE: retrieval queries must include owner_id filtering.
    _ANN_VECTOR_INDEX_PREFIX = "ix_chunks_embedding_hnsw_"
    _ANN_HALFVEC_INDEX_PREFIX = "ix_chunks_embedding_hnsw_halfvec_"
    _ANN_MAX_VECTOR_DIMENSIONS = 2000
    _ANN_MAX_HALFVEC_DIMENSIONS = 4000

    @staticmethod
    def _get_session_maker(session_maker=None):
        return session_maker or async_session_maker

    @staticmethod
    def _is_native_pgvector_column() -> bool:
        return isinstance(Chunk.__table__.c.embedding.type, Vector)

    @classmethod
    def _normalize_dimension(cls, dimension: int) -> int:
        dim = int(dimension or 0)
        if dim <= 0:
            raise ValueError("Embedding dimension must be a positive integer")
        return dim

    @classmethod
    def _ann_mode(cls, dimension: int) -> Optional[str]:
        dim = cls._normalize_dimension(dimension)
        if dim <= cls._ANN_MAX_VECTOR_DIMENSIONS:
            return "vector"
        if dim <= cls._ANN_MAX_HALFVEC_DIMENSIONS:
            return "halfvec"
        return None

    @classmethod
    def _index_name_for_dimension(cls, dimension: int) -> str:
        dim = cls._normalize_dimension(dimension)
        mode = cls._ann_mode(dim)
        if mode == "vector":
            return f"{cls._ANN_VECTOR_INDEX_PREFIX}{dim}"
        if mode == "halfvec":
            return f"{cls._ANN_HALFVEC_INDEX_PREFIX}{dim}"
        raise ValueError(f"ANN index not supported for dimension {dim}")

    @classmethod
    def _ann_index_supported(cls, dimension: int) -> bool:
        return cls._ann_mode(dimension) is not None

    @classmethod
    def _create_ann_index_sql(cls, dimension: int) -> str:
        dim = cls._normalize_dimension(dimension)
        index_name = cls._index_name_for_dimension(dim)
        mode = cls._ann_mode(dim)
        if mode == "vector":
            return f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON chunks
            USING hnsw ((embedding::vector({dim})) vector_cosine_ops)
            WHERE embedding IS NOT NULL AND vector_dims(embedding) = {dim}
            """
        if mode == "halfvec":
            return f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON chunks
            USING hnsw ((embedding::halfvec({dim})) halfvec_cosine_ops)
            WHERE embedding IS NOT NULL AND vector_dims(embedding) = {dim}
            """
        raise ValueError(f"ANN index not supported for dimension {dim}")

    @classmethod
    def _use_halfvec_ann(cls, dimension: int) -> bool:
        return cls._ann_mode(dimension) == "halfvec"

    @staticmethod
    def _to_pgvector_literal(values: List[float]) -> str:
        return "[" + ",".join(format(float(v), ".12g") for v in values) + "]"

    async def _ensure_ann_index(self, dimension: int, session_maker=None) -> None:
        if not self._is_native_pgvector_column():
            raise RuntimeError("Chunk.embedding is not configured as a native pgvector column")

        if not self._ann_index_supported(dimension):
            logger.info(
                "Skipping pgvector HNSW index for dimension %s; exact native search remains enabled",
                dimension,
            )
            return

        session_maker = self._get_session_maker(session_maker)
        sql = text(self._create_ann_index_sql(dimension))
        async with session_maker() as session:
            await session.execute(sql)
            await session.commit()
        logger.info("Ensured pgvector HNSW index for dimension %s", dimension)

    async def _search_native_pgvector_halfvec(
        self,
        query_vector: List[float],
        query_dimension: int,
        top_k: int,
        filter_dict: Dict[str, Any],
        session_maker,
        ef_search: int,
    ) -> List[Tuple[Any, float, Dict[str, Any]]]:
        vector_literal = self._to_pgvector_literal(query_vector)

        where_clauses = [
            "c.embedding IS NOT NULL",
            "vector_dims(c.embedding) = :query_dimension",
            "p.owner_id = :owner_id",
        ]
        params: Dict[str, Any] = {
            "query_vector": vector_literal,
            "query_dimension": query_dimension,
            "owner_id": filter_dict["owner_id"],
            "top_k": top_k,
        }

        if "project_id" in filter_dict:
            where_clauses.append("c.project_id = :project_id")
            params["project_id"] = filter_dict["project_id"]
        if "asset_id" in filter_dict:
            where_clauses.append("c.asset_id = :asset_id")
            params["asset_id"] = filter_dict["asset_id"]

        sql = text(
            f"""
            SELECT
                c.id,
                c.content,
                c.metadata,
                c.asset_id,
                    ((c.embedding::halfvec({query_dimension})) <=> (CAST(:query_vector AS halfvec({query_dimension})))) AS distance
            FROM chunks c
            JOIN projects p ON c.project_id = p.id
            WHERE {' AND '.join(where_clauses)}
            ORDER BY distance
            LIMIT :top_k
            """
        )

        async with session_maker() as session:
            try:
                await session.execute(text(f"SET LOCAL hnsw.ef_search = {int(ef_search)}"))
            except Exception as config_error:
                logger.debug("Could not set hnsw.ef_search=%s: %s", ef_search, config_error)
                # Failed SET LOCAL leaves the transaction aborted; reset it before running the query.
                await session.rollback()

            try:
                result = await session.execute(sql, params)
            except Exception as query_error:
                # Recover from an aborted transaction and retry once.
                await session.rollback()
                logger.debug("Retrying halfvec search after rollback: %s", query_error)
                result = await session.execute(sql, params)
            rows = result.all()

        results = [
            (
                row.id,
                1.0 - float(row.distance),
                {
                    "content": row.content,
                    "metadata": row.metadata or {},
                    "asset_id": row.asset_id,
                },
            )
            for row in rows
        ]

        logger.info("Found %s similar chunks (native pgvector halfvec)", len(results))
        return results
    
    def __init__(self):
        """Initialize PGVector provider."""
        logger.info("PGVector provider initialized")
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        **kwargs
    ) -> bool:
        """
        Create collection (for pgvector, this is handled by table creation).
        
        Args:
            collection_name: Not used (using chunks table)
            dimension: Vector dimension
            
        Returns:
            True (table already exists from migrations)
        """
        dim = self._normalize_dimension(dimension)
        await self._ensure_ann_index(dim, session_maker=kwargs.get("session_maker"))

        # With pgvector, collections are handled by the chunks table plus ANN indexes per supported dimension.
        logger.info(f"Collection '{collection_name}' ready (using chunks table, dimension={dim})")
        return True
    
    async def add_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        ids: List[Any],
        metadata: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> bool:
        """
        Add/update vectors in chunks table.
        
        Args:
            collection_name: Project name or identifier
            vectors: List of embeddings
            ids: List of chunk IDs
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            if not self._is_native_pgvector_column():
                raise RuntimeError("Chunk.embedding is not configured as a native pgvector column")

            if not vectors:
                logger.info("No vectors to add for collection '%s'", collection_name)
                return True

            expected_dimension = self._normalize_dimension(len(vectors[0]))
            for vector in vectors:
                if len(vector) != expected_dimension:
                    raise ValueError("All embeddings in the batch must have the same dimension")

            await self._ensure_ann_index(expected_dimension, session_maker=kwargs.get("session_maker"))

            from sqlalchemy import update as sa_update
            session_maker = self._get_session_maker(kwargs.get("session_maker"))
            async with session_maker() as session:
                for i, (chunk_id, vector) in enumerate(zip(ids, vectors)):
                    await session.execute(
                        sa_update(Chunk)
                        .where(Chunk.id == chunk_id)
                        .values(embedding=vector)
                    )
                    if (i + 1) % 500 == 0:
                        await session.flush()
                await session.commit()
                logger.info(f"Added {len(vectors)} vectors to collection '{collection_name}'")
                return True
                
        except Exception as e:
            logger.error(f"Error adding vectors: {str(e)}")
            raise
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Tuple[Any, float, Dict[str, Any]]]:
        """
        Search for similar vectors.
        Uses native pgvector cosine distance in PostgreSQL.
        """
        try:
            if not filter_dict or "owner_id" not in filter_dict:
                raise ValueError("owner_id filter is required for vector search")

            if not self._is_native_pgvector_column():
                raise RuntimeError("Chunk.embedding is not configured as a native pgvector column")

            return await self._search_native_pgvector(
                collection_name=collection_name,
                query_vector=query_vector,
                top_k=top_k,
                filter_dict=filter_dict,
                session_maker=kwargs.get("session_maker"),
            )

        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            raise

    async def _search_native_pgvector(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int,
        filter_dict: Dict[str, Any],
        session_maker=None,
    ) -> List[Tuple[Any, float, Dict[str, Any]]]:
        session_maker = self._get_session_maker(session_maker)
        query_dimension = self._normalize_dimension(len(query_vector))
        ef_search = int(get_runtime_value("retrieval_hnsw_ef_search", settings.retrieval_hnsw_ef_search))
        ef_search = max(1, ef_search)

        if self._use_halfvec_ann(query_dimension):
            return await self._search_native_pgvector_halfvec(
                query_vector=query_vector,
                query_dimension=query_dimension,
                top_k=top_k,
                filter_dict=filter_dict,
                session_maker=session_maker,
                ef_search=ef_search,
            )

        embedding_expr = cast(Chunk.embedding, Vector(query_dimension))
        async with session_maker() as session:
            try:
                await session.execute(text(f"SET LOCAL hnsw.ef_search = {int(ef_search)}"))
            except Exception as config_error:
                # Keep queries working even if the current pgvector build does not expose this setting.
                logger.debug("Could not set hnsw.ef_search=%s: %s", ef_search, config_error)
                # Failed SET LOCAL leaves the transaction aborted; reset it before running the query.
                await session.rollback()

            query = select(
                Chunk.id,
                Chunk.content,
                Chunk.extra_metadata,
                Chunk.asset_id,
                embedding_expr.cosine_distance(query_vector).label("distance"),
            ).join(
                Project,
                Chunk.project_id == Project.id,
            ).where(
                Chunk.embedding.isnot(None),
                func.vector_dims(Chunk.embedding) == query_dimension,
                Project.owner_id == filter_dict["owner_id"],
            )

            if "project_id" in filter_dict:
                query = query.where(Chunk.project_id == filter_dict["project_id"])
            if "asset_id" in filter_dict:
                query = query.where(Chunk.asset_id == filter_dict["asset_id"])

            query = query.order_by("distance").limit(top_k)
            try:
                result = await session.execute(query)
            except Exception as query_error:
                # Recover from an aborted transaction and retry once.
                await session.rollback()
                logger.debug("Retrying vector search after rollback: %s", query_error)
                result = await session.execute(query)
            rows = result.all()

        results = [
            (
                row.id,
                1.0 - float(row.distance),
                {
                    "content": row.content,
                    "metadata": row.extra_metadata,
                    "asset_id": row.asset_id,
                },
            )
            for row in rows
        ]

        logger.info("Found %s similar chunks (native pgvector)", len(results))
        return results
    
    async def delete_collection(
        self,
        collection_name: str,
        **kwargs
    ) -> bool:
        """
        Delete all chunks for a project.
        
        Args:
            collection_name: Project ID or identifier
            
        Returns:
            True if successful
        """
        try:
            session_maker = self._get_session_maker(kwargs.get("session_maker"))
            async with session_maker() as session:
                project_id = kwargs.get('project_id')
                if project_id:
                    stmt = delete(Chunk).where(Chunk.project_id == project_id)
                    await session.execute(stmt)
                    await session.commit()
                    logger.info(f"Deleted collection '{collection_name}'")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise

    async def delete_vectors(
        self,
        collection_name: str,
        *,
        filter_dict: Dict[str, Any],
        **kwargs
    ) -> bool:
        """
        Delete chunk rows matching the provided filter.

        For pgvector, vectors live inside PostgreSQL rows, so deleting vectors
        means deleting the matching `chunks` rows.
        """
        try:
            if not isinstance(filter_dict, dict) or not filter_dict:
                raise ValueError("filter_dict is required when deleting vectors")

            allowed_keys = {"asset_id", "project_id", "owner_id"}
            unknown_keys = set(filter_dict).difference(allowed_keys)
            if unknown_keys:
                raise ValueError(
                    f"Unsupported filter keys for pgvector delete: {sorted(unknown_keys)}"
                )

            asset_id = filter_dict.get("asset_id")
            project_id = filter_dict.get("project_id")
            owner_id = filter_dict.get("owner_id")

            if asset_id is None and project_id is None and owner_id is None:
                raise ValueError(
                    "At least one non-null filter key is required for pgvector delete"
                )

            session_maker = self._get_session_maker(kwargs.get("session_maker"))
            async with session_maker() as session:
                stmt = delete(Chunk)

                if asset_id is not None:
                    stmt = stmt.where(Chunk.asset_id == asset_id)
                if project_id is not None:
                    stmt = stmt.where(Chunk.project_id == project_id)
                if owner_id is not None:
                    stmt = stmt.where(
                        Chunk.project_id.in_(
                            select(Project.id).where(Project.owner_id == owner_id)
                        )
                    )

                await session.execute(stmt)
                await session.commit()

            logger.info("Deleted pgvector-backed chunk rows for filter %s", filter_dict)
            return True

        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            raise

    async def delete_vector_ids(
        self,
        collection_name: str,
        *,
        ids: List[int],
        **kwargs
    ) -> bool:
        """Delete pgvector-backed chunks by exact chunk IDs."""
        if not ids:
            return True
        try:
            session_maker = self._get_session_maker(kwargs.get("session_maker"))
            async with session_maker() as session:
                await session.execute(delete(Chunk).where(Chunk.id.in_([int(item) for item in ids])))
                await session.commit()
            logger.info("Deleted pgvector-backed chunk rows by id for '%s'", collection_name)
            return True
        except Exception as e:
            logger.error("Error deleting vector ids: %s", e)
            raise
    
    async def collection_exists(
        self,
        collection_name: str,
        **kwargs
    ) -> bool:
        """
        Check if project exists.
        
        Args:
            collection_name: Project name
            
        Returns:
            True if exists
        """
        try:
            session_maker = self._get_session_maker(kwargs.get("session_maker"))
            async with session_maker() as session:
                project_id = kwargs.get('project_id')
                if project_id:
                    stmt = select(Project).where(Project.id == project_id)
                    owner_id = kwargs.get('owner_id')
                    if owner_id is not None:
                        stmt = stmt.where(Project.owner_id == owner_id)
                    result = await session.execute(stmt)
                    return result.scalar_one_or_none() is not None
                return False
                
        except Exception as e:
            logger.error(f"Error checking collection: {str(e)}")
            return False

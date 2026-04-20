import asyncio
import logging

from sqlalchemy import select

from backend.celery_app import celery_app, get_setup_utils
from backend.database.models import Project, Chunk

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="backend.tasks.data_indexing.index_project_task",
    queue="default",
    # autoretry_for=(Exception,),
    # retry_kwargs={"max_retries": 3, "countdown": 60},
)
def index_project_task(self, project_id: int, do_reset: bool = False):
    return asyncio.run(_index_project(self, project_id, do_reset))


async def _index_project(task_instance, project_id: int, do_reset: bool):
    try:
        (
            _db_engine,
            session_maker,
            document_loader,
            chunking_service,
            embedding_service,
            vector_db,
            file_service,
        ) = await get_setup_utils()

        async with session_maker() as db:
            # 1) Check project exists
            project_stmt = select(Project).where(Project.id == project_id)
            project_result = await db.execute(project_stmt)
            project = project_result.scalar_one_or_none()

            if project is None:
                # task_instance.update_state(
                #     state="FAILURE",
                #     meta={"error": f"Project not found: {project_id}"}
                # )
                raise ValueError(f"Project not found: {project_id}")

            # 2) Get all chunks for project
            chunk_stmt = (
                select(Chunk)
                .where(Chunk.project_id == project_id)
                .order_by(Chunk.asset_id, Chunk.chunk_index)
            )
            chunk_result = await db.execute(chunk_stmt)
            chunks = list(chunk_result.scalars().all())

            if not chunks:
                # task_instance.update_state(
                #     state="FAILURE",
                #     meta={"error": f"No chunks found for project: {project_id}"}
                # )
                raise ValueError(f"No chunks found for project: {project_id}")

            # 3) Create/reset collection if needed
            collection_name = f"project_{project_id}"

            # use embedding size from one generated vector later if provider doesn't expose size
            texts = [chunk.content for chunk in chunks]

            logger.info(f"Generating embeddings for project {project_id} ({len(texts)} chunks)")
            embeddings = await embedding_service.generate_embeddings(texts)
            if not embeddings:
                raise ValueError(f"No embeddings generated for project: {project_id}")

            dimension = len(embeddings[0]) if embeddings else 0

            await vector_db.create_collection(
                collection_name=collection_name,
                dimension=dimension,
                do_reset=do_reset,
                session_maker=session_maker,
            )

            # 4) Add vectors
            chunk_ids = [chunk.id for chunk in chunks]
            vector_metadata = [
                {
                    "owner_id": project.owner_id,
                    "asset_id": chunk.asset_id,
                    "project_id": chunk.project_id,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ]

            await vector_db.add_vectors(
                collection_name=collection_name,
                vectors=embeddings,
                ids=chunk_ids,
                metadata=vector_metadata,
                session_maker=session_maker,
            )

            logger.info(
                f"Completed project indexing for project {project_id}: "
                f"{len(chunks)} chunks indexed"
            )

            return {
                "project_id": project_id,
                "status": "completed",
                "total_chunks": len(chunks),
                "do_reset": do_reset,
            }

    except Exception as e:
        logger.error(f"Task failed for project_id={project_id}: {str(e)}")
        raise

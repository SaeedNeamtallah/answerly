import asyncio
from sqlalchemy import select

from backend.database.connection import async_session_maker
from backend.database.models import Project
from backend.tasks.data_indexing import _index_project


async def main() -> None:
    async with async_session_maker() as db:
        project_ids = list((await db.execute(select(Project.id))).scalars().all())

    print("PROJECT_IDS=" + ",".join(str(pid) for pid in project_ids))
    for pid in project_ids:
        print(f"REINDEX_START project={pid}")
        result = await _index_project(task_instance=None, project_id=pid, do_reset=False)
        print("REINDEX_DONE", result)


if __name__ == "__main__":
    asyncio.run(main())

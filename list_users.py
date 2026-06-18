import asyncio
import sys

sys.path.append("/app")

from backend.database.connection import async_session_maker
from backend.database.models import User
from sqlalchemy.future import select

async def main():
    async with async_session_maker() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()

        print(f"Total Users: {len(users)}")
        print("-" * 50)
        for u in users:
            print(f"ID: {u.id} | Username: {u.username} | Role: {u.role} | Status: {u.status}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())

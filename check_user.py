import asyncio
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models import User

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(User).where(User.username == 'cyber_sec'))
        u = res.scalar_one_or_none()
        if u:
            print(f"User: {u.username}, Role: {u.role}")
        else:
            print("User not found.")

if __name__ == "__main__":
    asyncio.run(main())

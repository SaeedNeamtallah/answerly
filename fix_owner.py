import asyncio
import os
import sys
import bcrypt

# Add the app path
sys.path.append("/app")

from backend.database.connection import async_session_maker
from backend.database.models import User
from backend.security.auth import ROLE_PLATFORM_OWNER
from sqlalchemy.future import select

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

async def main():
    async with async_session_maker() as session:
        owner_username = "OWNERSAEED"
        stmt_by_name = select(User).where(User.username == owner_username)
        result_by_name = await session.execute(stmt_by_name)
        existing_by_name = result_by_name.scalars().first()
        if existing_by_name:
            existing_by_name.hashed_password = get_password_hash("OWNERSAEED")
            await session.commit()
            print(f"Reset password for user: {owner_username}")
        else:
            print(f"User not found: {owner_username}")

if __name__ == "__main__":
    asyncio.run(main())

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
        owner_username = "OWNERPLATFORM"
        stmt_by_name = select(User).where(User.username == owner_username)
        result_by_name = await session.execute(stmt_by_name)
        existing_by_name = result_by_name.scalars().first()
        if not existing_by_name:
            owner_user = User(
                username=owner_username,
                hashed_password=get_password_hash("OWNERPLATFORM"),
                role=ROLE_PLATFORM_OWNER,
                status="ACTIVE"
            )
            session.add(owner_user)
            await session.commit()
            print(f"Created default platform owner account: {owner_username}")
        else:
            existing_by_name.role = ROLE_PLATFORM_OWNER
            existing_by_name.hashed_password = get_password_hash("OWNERPLATFORM")
            await session.commit()
            print(f"Promoted existing user to platform owner: {owner_username}")

if __name__ == "__main__":
    asyncio.run(main())

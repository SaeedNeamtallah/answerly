import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import async_session_maker
from backend.database.models import User, UserAccountStatus, UserRole
from backend.services.auth_service import AuthService

async def create_user(username: str, role: str, password: str):
    async with async_session_maker() as db:
        email = f"{username}@company.com"

        # Check if exists
        result = await db.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"User {username} already exists!")
            return

        new_user = User(
            username=username,
            email=email,
            hashed_password=AuthService._hash_password(password),
            role=role,
            status=UserAccountStatus.ACTIVE,
            company_name="Acme Corp"
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        print(f"Created user '{username}' with password '{password}' and role '{role}'")

if __name__ == "__main__":
    if len(sys.argv) == 4:
        asyncio.run(create_user(sys.argv[1], sys.argv[2], sys.argv[3]))
    else:
        print("Usage: python create_sec_eng.py <username> <role> <password>")

import asyncio
import sys

# To support being run from the current working directory
sys.path.append(".")

from backend.database.connection import async_session_maker
from backend.database.models import User, UserRole
from sqlalchemy import delete, select
from backend.services.auth_service import AuthService

async def main():
    async with async_session_maker() as db:
        # Ensure OWNERSAEED exists
        result = await db.execute(select(User).where(User.username == 'OWNERSAEED'))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                username='OWNERSAEED',
                hashed_password=AuthService._hash_password('OWNERSAEED'),
                role=UserRole.PLATFORM_OWNER.value
            )
            db.add(user)
            print('Created new PLATFORM OWNER user OWNERSAEED.')
            await db.commit()

        # Now delete everyone else
        stmt = delete(User).where(User.username != 'OWNERSAEED')
        await db.execute(stmt)
        await db.commit()
        print("Deleted all other users successfully.")

if __name__ == "__main__":
    asyncio.run(main())

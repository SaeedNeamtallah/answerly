from backend.services.auth_service import AuthService
from backend.database.connection import async_session_maker
from backend.database.models import User, UserRole
from sqlalchemy import select
import asyncio

async def create():
    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.username == 'OWNERSAEED'))
        user = result.scalar_one_or_none()
        if user:
            user.hashed_password = AuthService._hash_password('OWNERSAEED')
            user.role = UserRole.PLATFORM_OWNER.value
            print('User already exists. Updated password and role.')
        else:
            user = User(
                username='OWNERSAEED',
                hashed_password=AuthService._hash_password('OWNERSAEED'),
                role=UserRole.PLATFORM_OWNER.value
            )
            db.add(user)
            print('Created new PLATFORM OWNER user OWNERSAEED.')
        await db.commit()

asyncio.run(create())

import asyncio
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models import User
from backend.services.auth_service import AuthService

async def reset_saeed():
    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.username == 'saeed'))
        user = result.scalar_one_or_none()
        if user:
            user.hashed_password = AuthService._hash_password('saeed123')
            await db.commit()
            print('Password for saeed reset to saeed123')
        else:
            print('User saeed not found')

asyncio.run(reset_saeed())

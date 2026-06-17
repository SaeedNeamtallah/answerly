from backend.services.auth_service import AuthService
from backend.database.connection import async_session_maker
from backend.database.models import User
from sqlalchemy import select
import asyncio

async def reset():
    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.username == 'saeed'))
        user = result.scalar_one_or_none()
        if user:
            user.hashed_password = AuthService._hash_password('saeed123')
            await db.commit()
            print('Password reset successfully to saeed123')
        else:
            print('User saeed not found')

asyncio.run(reset())

import asyncio
from backend.database import async_session_maker
from backend.database.models import BotIntegration, User
from sqlalchemy import select

async def run():
    async with async_session_maker() as db:
        res = await db.execute(select(User).where(User.username == 'saeed'))
        user = res.scalar_one_or_none()
        if user:
            res2 = await db.execute(select(BotIntegration).where(BotIntegration.owner_id == user.id))
            bots = res2.scalars().all()
            for bot in bots:
                print(f"Bot: id={bot.id}, name={bot.name}, telegram_bot_id={bot.telegram_bot_id}, status={bot.status}")
            if not bots:
                print("No bots found for saeed")
        else:
            print("User saeed not found")

if __name__ == "__main__":
    asyncio.run(run())

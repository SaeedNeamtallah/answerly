import asyncio
from backend.database import async_session_maker
from backend.database.models import BotIntegration
from sqlalchemy import select

async def run():
    async with async_session_maker() as db:
        res = await db.execute(select(BotIntegration).where(BotIntegration.id == 44))
        bot = res.scalar_one_or_none()
        if bot:
            print(f"Webhook secret: {bot.webhook_secret}")
            print(f"Telegram Token hash: {bot.bot_token_hash}")
        else:
            print("Bot not found")

if __name__ == "__main__":
    asyncio.run(run())

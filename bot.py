import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import settings
from database.db import init_db
from handlers import start, menu, search, profile, privacy, admin

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    bot = Bot(settings.bot_token)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(search.router)
    dp.include_router(profile.router)
    dp.include_router(privacy.router)
    dp.include_router(admin.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

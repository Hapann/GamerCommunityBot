# bot/main.py
import asyncio
from aiogram import Bot, Dispatcher
from handlers.latest import news_router
from dotenv import load_dotenv
import os
from logger.logger import logger


from database.db import init_db
from handlers import user_handlers
from services.scheduler import setup_scheduler

load_dotenv()
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()

async def main():
    await init_db()
    dp.include_router(user_handlers.router)
    dp.include_router(news_router)

    setup_scheduler()

    print("🚀 Бот запущен и следит за новостями.")
    logger.info("Бот запущен 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

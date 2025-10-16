# main.py
import asyncio
from aiogram import Bot, Dispatcher
from handlers.latest import news_router
from dotenv import load_dotenv
import os
from logger.logger import logger

# Ваши другие импорты
from database.db import init_db
from handlers import user_handlers
from services.scheduler import setup_scheduler

load_dotenv()

# Проверяем сразу все переменные
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TOPIC_ID = os.getenv("TOPIC_ID")

logger.info(f"Загружены из .env: TOKEN={'***' if TOKEN else 'НЕТ'}, CHAT_ID={CHAT_ID}, TOPIC_ID={TOPIC_ID}")

if not os.getenv("TOKEN"):
    raise ValueError("❌ TOKEN не найден в переменных окружения")

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()

async def test_rss_manually():
    """Ручной тест RSS-читалки при старте."""
    logger.info("🔧 Запуск ручного теста RSS-читалки...")
    try:
        from services.rss_reader import get_all_rss_news
        news = await get_all_rss_news()
        logger.info(f"🔧 Результат ручного теста: {len(news)} новостей")

        if news:
            for i, item in enumerate(news[:3]):
                logger.info(f"🔧 Новость {i+1}: {item['title'][:50]}...")
        else:
            logger.warning("🔧 Ручной тест: новости не найдены!")

    except Exception as e:
        logger.exception(f"🔧 Ошибка в ручном тесте RSS: {e}")

async def main():
    try:
        await init_db()

        # Подключаем роутеры
        dp.include_router(user_handlers.router)
        dp.include_router(news_router)

        setup_scheduler()

        # Запускаем ручной тест RSS при старте
        await test_rss_manually()

        print("🚀 Бот запущен и следит за новостями.")
        logger.info("Бот запущен 🚀")

        await dp.start_polling(bot)

    except Exception as e:
        logger.exception(f"Критическая ошибка при запуске бота: {e}")
        print(f"❌ Ошибка запуска: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

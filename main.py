# main.py
import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from logger.logger import logger

# === 1. Сначала загружаем .env ===
load_dotenv()

# === 2. Теперь можно читать переменные окружения ===
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TOPIC_ID = os.getenv("TOPIC_ID")

logger.info(f"Загружены из .env: TOKEN={'***' if TOKEN else 'НЕТ'}, CHAT_ID={CHAT_ID}, TOPIC_ID={TOPIC_ID}")

if not TOKEN:
    raise ValueError("❌ TOKEN не найден в переменных окружения")

# === 3. И только теперь подключаем остальные модули ===
from database.db import init_db
from handlers import user_handlers
from handlers.latest import news_router
from services.scheduler import setup_scheduler

# === 4. Создаём бота и диспетчер ===
bot = Bot(token=TOKEN)
dp = Dispatcher()

# === 5. Тест RSS при старте ===
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

# === 6. Основной запуск ===
async def main():
    try:
        await init_db()
        dp.include_router(user_handlers.router)
        dp.include_router(news_router)

        setup_scheduler()
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

# bot/handlers/latest.py
from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message
from services.rss_reader import get_all_rss_news
from logger.logger import logger
import os

news_router = Router()

# ID супергруппы и топика из переменных окружения
CHAT_ID = os.getenv("CHAT_ID")
TOPIC_ID = os.getenv("TOPIC_ID")

# Преобразуем в правильные типы для надёжности
def safe_int(value, name):
    try:
        return int(value) if value else None
    except (ValueError, TypeError):
        logger.error(f"Неверный формат {name}: {value}")
        return None

CHAT_ID = safe_int(CHAT_ID, "CHAT_ID")
TOPIC_ID = safe_int(TOPIC_ID, "TOPIC_ID")

logger.info(f"Переменные окружения загружены: CHAT_ID={CHAT_ID}, TOPIC_ID={TOPIC_ID}")


def format_news_message(news_item, total_count=None):
    """Форматирует новость для отправки в Telegram."""
    message_parts = [
        f"<b>{news_item['title']}</b>",
        f"🔗 {news_item['link']}",
        f"📰 Источник: {news_item['source']}",
    ]

    if total_count is not None:
        message_parts.append(f"📊 Всего новостей: {total_count}")

    return "\n".join(message_parts)


@news_router.message(Command("latest"))
async def send_latest_news(message: Message, bot: Bot):
    """Отправляет последние новости из RSS‑лент."""
    logger.info(
        f"Получена команда /latest от пользователя {message.from_user.id} в чате {message.chat.id}"
    )

    try:
        await message.answer("🔄 Загружаю свежие новости...")
        logger.info("Начинается сбор новостей из RSS‑лент")

        news = await get_all_rss_news()
        count = len(news)
        logger.info(f"Получено {count} новостей")

        if not news:
            logger.warning("Новости не найдены — возвращаем пустой ответ пользователю")
            await message.answer("😴 Пока нет свежих новостей")
            return

        # Отправляем первую новость
        text = format_news_message(news[0], count)
        await message.answer(text, parse_mode="HTML")
        logger.info(f"Отправлена новость: {news[0]['title'][:50]}...")

    except Exception as e:
        logger.exception(f"Ошибка при выполнении команды /latest: {e}")
        await message.answer("❌ Произошла ошибка при получении новостей")

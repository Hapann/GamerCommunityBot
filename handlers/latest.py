from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from services.rss_reader import get_all_rss_news

news_router = Router()

@news_router.message(Command("latest"))
async def send_latest_news(message: Message):
    """Отправляет последнюю новость прямо из RSS‑лент."""
    news = await get_all_rss_news()

    count = len(news)
    if not count:
        await message.answer("Пока нет свежих новостей 😴")
        return

    latest = news[0]
    text = (
        f"<b>{latest['title']}</b>\n"
        f"{latest['link']}\n"
        f"Источник: {latest['source']}\n"
        f"Всего получено: {count} новостей 🗞"
    )
    await message.answer(text, parse_mode="HTML")

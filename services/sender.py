# bot/services/sender.py
import os
import asyncio
from aiogram import Bot
from sqlalchemy import select
from datetime import datetime

from database.db import AsyncSessionLocal
from database.models import News, SentNews
from services.rss_reader import get_all_rss_news  # подключаем твой ридер

BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
TOPIC_ID = os.getenv("TOPIC_ID")
TOPIC_ID = int(TOPIC_ID) if TOPIC_ID else None

bot = Bot(token=BOT_TOKEN)

async def sync_rss_to_db():
    """Парсит RSS и сохраняет новые новости в базу."""
    news_list = await get_all_rss_news()
    new_count = 0

    async with AsyncSessionLocal() as session:
        for item in news_list:
            # Проверяем, есть ли уже такая новость по URL
            stmt = select(News).where(News.url == item["link"])
            result = await session.execute(stmt)
            exists = result.scalar_one_or_none()
            if exists:
                continue  # уже есть, пропускаем

            news = News(
                title=item["title"],
                url=item["link"],
                created_at=datetime.utcnow(),
            )
            session.add(news)
            new_count += 1

        await session.commit()

    print(f"📰 Добавлено {new_count} новых новостей в базу.")
    return new_count

async def send_new_news():
    """Отправляет свежие новости в Telegram-группу и отмечает их как отправленные."""
    # Сначала синхронизация RSS → DB
    await sync_rss_to_db()

    async with AsyncSessionLocal() as session:
        stmt = (
            select(News)
            .outerjoin(SentNews, SentNews.news_id == News.id)
            .where(SentNews.id.is_(None))
        )
        result = await session.execute(stmt)
        unsent_news = result.scalars().all()

        if not unsent_news:
            print("Нет новых новостей для отправки 💤")
            return

        print(f"📢 Отправляем {len(unsent_news)} новых новостей...")
        for news in unsent_news:
            text = f"<b>{news.title}</b>\n{news.url}"

            try:
                if TOPIC_ID:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        message_thread_id=TOPIC_ID,
                        text=text,
                        parse_mode="HTML",
                    )
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")

                await asyncio.sleep(1)

                sent = SentNews(
                    user_id=None, news_id=news.id, sent_at=datetime.utcnow()
                )
                session.add(sent)
            except Exception as e:
                print(f"Ошибка отправки новости ({news.url}): {e}")

        await session.commit()
        print("✅ Отправка завершена.")

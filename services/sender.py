# bot/services/sender.py
import os
from aiogram import Bot
from database.db import AsyncSessionLocal
from database.models import News, SentNews, User
from sqlalchemy import select
from datetime import datetime

BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
TOPIC_ID = os.getenv("TOPIC_ID")
TOPIC_ID = int(TOPIC_ID) if TOPIC_ID else None

bot = Bot(token=BOT_TOKEN)

async def send_new_news():
    """Отправляет свежие новости в Telegram-группу и отмечает их как отправленные."""
    async with AsyncSessionLocal() as session:
        # Получаем новости, которые ещё не отправлялись
        stmt = select(News).outerjoin(SentNews, SentNews.news_id == News.id).where(SentNews.id.is_(None))
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
                    await bot.send_message(chat_id=CHAT_ID, message_thread_id=TOPIC_ID, text=text, parse_mode="HTML")
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")

                # Чтобы не забомбить Telegram API — небольшая задержка между сообщениями
                await asyncio.sleep(1)

                # Помечаем как отправленное (фиктивный user_id=0 – рассылка в группу)
                sent = SentNews(user_id=None, news_id=news.id, sent_at=datetime.utcnow())
                session.add(sent)
            except Exception as e:
                print(f"Ошибка отправки новости ({news.url}): {e}")

        await session.commit()
        print("✅ Отправка завершена.")

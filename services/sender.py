# services/sender.py
import os
import asyncio
import re
from datetime import datetime
import dateutil.parser
from aiogram import Bot
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import News, SentNews
from services.rss_reader import get_all_rss_news
from services.gigachat import generate_gigachat_summary
from logger.logger import logger

BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
TOPIC_ID = os.getenv("TOPIC_ID")
TOPIC_ID = int(TOPIC_ID) if TOPIC_ID else None

bot = Bot(token=BOT_TOKEN)

# --- Параметры ---
MAX_RETRIES = 3          # число попыток при сбое
RETRY_DELAY = 30         # пауза между попытками (сек)
DELAY_BETWEEN_NEWS = 10  # пауза между публикациями (сек)

# --- Вспомогательные функции ---
def to_datetime_safe(value):
    try:
        if not value:
            return datetime.utcnow()
        return dateutil.parser.parse(value)
    except Exception:
        return datetime.utcnow()


def sanitize_llm_reply(text: str) -> str:
    """Удаляет служебные метки и адаптирует формат под Telegram."""
    cleaned = text.strip()

    # Убираем обёртки вида ---PROMPT START---
    cleaned = re.sub(r"---(PROMPT|REPLY)\s+(START|END)---", "", cleaned)

    # Меняем "### " на более дружелюбный символ
    cleaned = re.sub(r"^###\s*", "📰 ", cleaned, flags=re.MULTILINE)

    # Телега не любит markdown-символы, экранируем
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    cleaned = re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", cleaned)

    return cleaned.strip()


async def sync_rss_to_db():
    """Сохраняет новые записи из RSS."""
    news_list = await get_all_rss_news()
    new_count = 0

    async with AsyncSessionLocal() as session:
        for item in news_list:
            stmt = select(News).where(News.url == item["link"])
            result = await session.execute(stmt)
            exists = result.scalar_one_or_none()
            if exists:
                continue

            published_at = to_datetime_safe(item.get("published") or item.get("updated"))
            news = News(
                title=item["title"],
                url=item["link"],
                published_at=published_at,
            )
            session.add(news)
            new_count += 1

        await session.commit()

    logger.info(f"📰 Добавлено {new_count} новых новостей.")
    return new_count


# --- Основная логика ---
async def send_new_news():
    """Обрабатывает и публикует новые новости."""
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
        logger.info("😴 Нет новых новостей для публикации.")
        return

    logger.info(f"🌐 Найдено {len(unsent_news)} новостей. Начинаем обработку...")

    for news in unsent_news:
        success = False

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"🧠 [{attempt}/{MAX_RETRIES}] Анализ: {news.url}")
                generated_text = generate_gigachat_summary(news.url)

                if not generated_text:
                    raise ValueError("LLM вернул пустой ответ")

                # Очищаем, проверяем, логируем
                clean_text = sanitize_llm_reply(generated_text)
                logger.debug(f"Текст после очистки ({len(clean_text)} симв.): {clean_text[:100]!r}")

                if len(clean_text) < 50:
                    raise ValueError("ответ от LLM слишком короткий")

                # Не роняем публикацию, если теги не совпали
                if not any(tag in clean_text.lower() for tag in ["заголовок", "текст", "📰", "новость"]):
                    logger.warning("⚠️ Ответ без ключевых тегов, публикуем в любом случае.")

                logger.info(f"🚀 Отправляем в Telegram: {news.title[:60]}...")

                try:
                    if TOPIC_ID:
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            message_thread_id=TOPIC_ID,
                            text=clean_text,
                            parse_mode="MarkdownV2",
                            disable_web_page_preview=True,
                        )
                    else:
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=clean_text,
                            parse_mode="MarkdownV2",
                            disable_web_page_preview=True,
                        )
                except Exception as parse_err:
                    # если Markdown рвётся — повтор без форматирования
                    logger.error(f"💥 Ошибка при форматировании Markdown: {parse_err}, пробуем без parse_mode.")
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        message_thread_id=TOPIC_ID if TOPIC_ID else None,
                        text=clean_text,
                        parse_mode=None,
                        disable_web_page_preview=True,
                    )

                # ✅ сохраняем факт отправки
                async with AsyncSessionLocal() as session:
                    sent = SentNews(
                        user_id=None,
                        news_id=news.id,
                        sent_at=datetime.utcnow(),
                    )
                    session.add(sent)
                    await session.commit()

                logger.info(f"✅ Новость опубликована: {news.url}")
                success = True
                break

            except Exception as e:
                logger.error(f"❌ Попытка {attempt} не удалась для {news.url}: {e}")
                if attempt < MAX_RETRIES:
                    logger.info(f"⏳ Повтор через {RETRY_DELAY} сек...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    logger.error(f"💀 Все попытки исчерпаны для {news.url}")

        if not success:
            logger.warning(f"⚠️ Новость {news.url} останется на повторную попытку.")
        else:
            await asyncio.sleep(DELAY_BETWEEN_NEWS)

    logger.info("🏁 Цикл отправки завершён.")

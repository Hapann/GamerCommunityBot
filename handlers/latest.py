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

# Преобразуем в правильные типы
if CHAT_ID:
    try:
        CHAT_ID = int(CHAT_ID)
    except (ValueError, TypeError):
        logger.error(f"Неверный формат CHAT_ID: {CHAT_ID}")
        CHAT_ID = None

if TOPIC_ID:
    try:
        TOPIC_ID = int(TOPIC_ID)
    except (ValueError, TypeError):
        logger.error(f"Неверный формат TOPIC_ID: {TOPIC_ID}")
        TOPIC_ID = None

logger.info(f"Загружены переменные: CHAT_ID={CHAT_ID}, TOPIC_ID={TOPIC_ID}")

def format_news_message(news_item, total_count=None):
    """Форматирует новость для отправки."""
    message_parts = [
        f"<b>{news_item['title']}</b>",
        f"🔗 {news_item['link']}",
        f"📰 Источник: {news_item['source']}"
    ]

    if total_count is not None:
        message_parts.append(f"📊 Всего новостей: {total_count}")

    return "\n".join(message_parts)

@news_router.message(Command("latest"))
async def send_latest_news(message: Message, bot: Bot):
    """Отправляет последние новости из RSS‑лент."""
    logger.info(f"Получена команда /latest от пользователя {message.from_user.id} в чате {message.chat.id}")

    try:
        await message.answer("🔄 Загружаю свежие новости...")
        logger.info("Начинаем загрузку новостей")

        news = await get_all_rss_news()
        logger.info(f"Получено {len(news)} новостей из RSS-лент")

        if not news:
            logger.warning("Новости не найдены - возвращаем пустой список")
            await message.answer("😴 Пока нет свежих новостей")
            return

        # Отправляем первую новость
        text = format_news_message(news[0], len(news))
        await message.answer(text, parse_mode="HTML")
        logger.info(f"Успешно отправлена новость: {news[0]['title'][:30]}...")

    except Exception as e:
        logger.exception(f"Ошибка в команде /latest: {e}")
        await message.answer("❌ Произошла ошибка при получении новостей")

@news_router.message(Command("send_to_group"))
async def send_to_group_test(message: Message, bot: Bot):
    """Тестовая команда для отправки сообщения в группу."""
    logger.info(f"Тест отправки в группу от пользователя {message.from_user.id}")

    try:
        if not CHAT_ID:
            await message.answer("❌ CHAT_ID не установлен в .env файле")
            logger.error("CHAT_ID не установлен")
            return

        if not TOPIC_ID:
            await message.answer("❌ TOPIC_ID не установлен в .env файле")
            logger.error("TOPIC_ID не установлен")
            return

        test_text = "🧪 <b>Тестовое сообщение</b>\nЭто проверка отправки в супергруппу с топиком!"

        # Пытаемся отправить в группу
        await bot.send_message(
            chat_id=CHAT_ID,
            message_thread_id=TOPIC_ID,
            text=test_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        await message.answer("✅ Тестовое сообщение отправлено в группу!")
        logger.info(f"Тестовое сообщение отправлено в группу {CHAT_ID}, топик {TOPIC_ID}")

    except Exception as e:
        error_msg = f"❌ Ошибка отправки в группу: {e}"
        logger.error(error_msg)
        await message.answer(error_msg)

@news_router.message(Command("check_env"))
async def check_env_vars(message: Message):
    """Проверяет переменные окружения."""
    env_info = (
        "🔍 <b>Проверка переменных окружения:</b>\n"
        f"CHAT_ID: {CHAT_ID} (тип: {type(CHAT_ID).__name__})\n"
        f"TOPIC_ID: {TOPIC_ID} (тип: {type(TOPIC_ID).__name__})\n"
        f"TOKEN установлен: {'Да' if os.getenv('TOKEN') else 'Нет'}"
    )

    logger.info(f"Проверка env: CHAT_ID={CHAT_ID}, TOPIC_ID={TOPIC_ID}")
    await message.answer(env_info, parse_mode="HTML")

@news_router.message(Command("debug_rss"))
async def debug_rss(message: Message):
    """Принудительная проверка работы RSS."""
    logger.info("=== НАЧАЛО ОТЛАДКИ RSS ===")

    try:
        # Тестируем каждый фид отдельно
        import aiohttp
        from services.rss_reader import RSS_FEEDS, HEADERS

        async with aiohttp.ClientSession() as session:
            for url in RSS_FEEDS:
                logger.info(f"🔍 Тестируем: {url}")
                try:
                    async with session.get(url, headers=HEADERS, timeout=10) as response:
                        status = response.status
                        content_type = response.headers.get('content-type', 'unknown')
                        logger.info(f"📡 {url} - статус: {status}, тип: {content_type}")

                        if status == 200:
                            content = await response.text()
                            logger.info(f"📥 {url} - получено {len(content)} символов")

                            # Быстрый парсинг
                            import feedparser
                            parsed = feedparser.parse(content)
                            logger.info(f"📊 {url} - записей: {len(parsed.entries)}, ошибка: {parsed.bozo}")

                            if parsed.entries:
                                for i, entry in enumerate(parsed.entries[:2]):
                                    title = getattr(entry, 'title', 'Без названия')[:50]
                                    logger.info(f"📰 {url} - запись {i+1}: {title}...")
                        else:
                            logger.warning(f"❌ {url} - плохой статус: {status}")

                except Exception as e:
                    logger.error(f"💥 Ошибка при тесте {url}: {e}")

        # Тестируем основную функцию
        from services.rss_reader import get_all_rss_news
        news = await get_all_rss_news()
        logger.info(f"🎯 Итог основной функции: {len(news)} новостей")

        await message.answer(f"🔧 Отладка завершена. Найдено {len(news)} новостей. Проверьте логи.")

    except Exception as e:
        logger.exception(f"💥 Критическая ошибка при отладке: {e}")
        await message.answer("❌ Ошибка при отладке RSS")

    logger.info("=== КОНЕЦ ОТЛАДКИ RSS ===")

@news_router.message(Command("test"))
async def test_command(message: Message):
    """Тестовая команда для проверки работы бота."""
    logger.info("Тестовая команда вызвана")
    await message.answer("🤖 Бот работает! Команда /test получена.")

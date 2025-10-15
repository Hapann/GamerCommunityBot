# bot/services/rss_reader.py
import aiohttp
import feedparser
import asyncio
from datetime import datetime
from logger.logger import logger

RSS_FEEDS = [
    "https://news.yandex.ru/index.rss",
    "https://habr.com/ru/rss/all/all/?fl=ru",
    "https://lenta.ru/rss/news",
    "https://www.goha.ru/rss/news"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


async def fetch_feed(session, url):
    """Загружает и парсит один RSS‑фид."""
    logger.debug(f"Загружаем RSS‑фид: {url}")
    try:
        async with session.get(url, headers=HEADERS, timeout=15) as response:
            status = response.status
            logger.debug(f"Ответ {url}: {status}")
            if status != 200:
                logger.warning(f"❌ Некорректный статус {status} при загрузке {url}")
                return []

            content_bytes = await response.read()
            encoding = response.charset or "utf-8"
            content = content_bytes.decode(encoding, errors="ignore")

        parsed = await asyncio.to_thread(feedparser.parse, content)
        logger.debug(f"Результат парсинга {url}: {len(parsed.entries)} записей")

        items = []
        for entry in parsed.entries:
            items.append({
                "title": getattr(entry, "title", "Без названия"),
                "link": getattr(entry, "link", ""),
                "published": getattr(entry, "published", None),
                "source": url
            })
        return items

    except Exception as e:
        logger.exception(f"Ошибка загрузки или парсинга RSS {url}: {e}")
        return []


async def get_all_rss_news():
    """Асинхронно собирает новости со всех RSS."""
    logger.debug("Начинаем сбор всех RSS‑фидов")
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[fetch_feed(session, url) for url in RSS_FEEDS],
            return_exceptions=True
        )

    # результаты могут содержать исключения — выводим их
    all_items = []
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Ошибка в RSS‑фиде {RSS_FEEDS[idx]}: {result}")
        else:
            all_items.extend(result)

    logger.debug(f"Всего собрано {len(all_items)} новостей со всех источников")
    return all_items

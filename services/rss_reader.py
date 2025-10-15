# bot/services/rss_reader.py
import aiohttp
import feedparser
import asyncio
from datetime import datetime
from logger.logger import logger  # если есть логгер

RSS_FEEDS = [
    "https://news.yandex.ru/index.rss",
    "https://habr.com/ru/rss/all/all/?fl=ru",
    "https://lenta.ru/rss/news",
    "https://www.goha.ru/rss/news"
]

async def fetch_feed(session, url):
    try:
        async with session.get(url, timeout=15) as response:
            content_bytes = await response.read()
            encoding = response.charset or "utf-8"
            content = content_bytes.decode(encoding, errors="ignore")

        parsed = await asyncio.to_thread(feedparser.parse, content)

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
        logger.warning(f"Ошибка загрузки RSS {url}: {e}")
        return []

async def get_all_rss_news():
    """Собирает новости со всех RSS."""
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[fetch_feed(session, url) for url in RSS_FEEDS])
    # превращаем список списков в один общий
    return [item for sublist in results for item in sublist]

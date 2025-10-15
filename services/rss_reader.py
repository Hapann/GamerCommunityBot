# bot/services/rss_reader.py
import aiohttp
import feedparser
from datetime import datetime
from asyncio import gather

RSS_FEEDS = [
    "https://news.yandex.ru/index.rss",
    "https://habr.com/ru/rss/all/all/?fl=ru",
    "https://lenta.ru/rss/news",
]

async def fetch_feed(session, url):
    try:
        async with session.get(url, timeout=15) as response:
            content = await response.text()
            parsed = feedparser.parse(content)
            items = []
            for entry in parsed.entries:
                items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": getattr(entry, "published", None),
                    "source": url
                })
            return items
    except Exception as e:
        print(f"Ошибка загрузки RSS {url}: {e}")
        return []

async def get_all_rss_news():
    """Собирает новости со всех RSS."""
    async with aiohttp.ClientSession() as session:
        results = await gather(*[fetch_feed(session, url) for url in RSS_FEEDS])
    # Объединяем во flat список
    return [item for sublist in results for item in sublist]

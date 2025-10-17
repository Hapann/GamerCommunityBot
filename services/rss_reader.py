# bot/services/rss_reader.py
import aiohttp
import feedparser
import asyncio
from datetime import datetime
from logger.logger import logger

RSS_FEEDS = [
    "https://www.goha.ru/rss/news",
    "https://www.playground.ru/rss/news.xml",
    "https://dtf.ru/rss/all"
]
#https://www.gamedeveloper.com/rss.xml - eng
#https://www.uploadvr.com/feed/ - eng
#https://www.roadtovr.com/feed/ - eng
#https://www.polygon.com/feed/ - eng
#https://www.pcgamer.com/rss/ - eng
#https://www.gamespot.com/feeds/news/ - eng
#https://kotaku.com/feed - eng

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

async def fetch_feed_simple(session, url):
    """Упрощенная загрузка одного RSS-фида."""
    logger.info(f"🔄 Пытаемся загрузить: {url}")
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as response:
            if response.status != 200:
                logger.warning(f"❌ {url} - статус {response.status}")
                return []

            content = await response.text()
            logger.info(f"✅ {url} - загружено {len(content)} символов")

            # Парсим синхронно для простоты
            parsed = feedparser.parse(content)
            logger.info(f"📊 {url} - распаршено {len(parsed.entries)} записей")

            items = []
            for entry in parsed.entries[:5]:  # Берем только первые 5
                if hasattr(entry, 'title') and hasattr(entry, 'link'):
                    items.append({
                        "title": entry.title,
                        "link": entry.link,
                        "source": url
                    })
                    logger.info(f"📰 Добавлена: {entry.title[:30]}...")

            return items

    except Exception as e:
        logger.error(f"💥 Ошибка с {url}: {e}")
        return []

async def get_all_rss_news():
    """Упрощенная версия сбора новостей."""
    logger.info("🎯 ЗАПУСК get_all_rss_news()")

    try:
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_feed_simple(session, url) for url in RSS_FEEDS]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)

        logger.info(f"🎉 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ: {len(all_items)} новостей")

        if all_items:
            for i, item in enumerate(all_items[:3]):
                logger.info(f"🏆 Пример {i+1}: {item['title'][:50]}...")

        return all_items

    except Exception as e:
        logger.exception(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return []

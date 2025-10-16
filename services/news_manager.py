# services/news_manager.py
from database.db import AsyncSessionLocal
from database.models import News, Feed
from services.rss_reader import get_all_rss_news
from sqlalchemy import select
from datetime import datetime

async def collect_and_save_news():
    async with AsyncSessionLocal() as session:
        rss_news = await get_all_rss_news()
        created_count = 0

        for item in rss_news:
            stmt = select(News).where(News.url == item["link"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                feed = await session.execute(select(Feed).where(Feed.url == item["source"]))
                feed_obj = feed.scalar_one_or_none()

                # Если источник ещё не в Feed — добавим
                if not feed_obj:
                    feed_obj = Feed(name=item["source"], url=item["source"], type="rss")
                    session.add(feed_obj)
                    await session.flush()

                news_obj = News(
                    title=item["title"],
                    url=item["link"],
                    source_id=feed_obj.id,
                    published_at=datetime.utcnow()
                )
                session.add(news_obj)
                created_count += 1

        await session.commit()
        print(f"✅ Добавлено {created_count} новых новостей.")

# services/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.news_manager import collect_and_save_news
from services.sender import send_new_news

async def scheduled_job():
    await collect_and_save_news()
    await send_new_news()

def setup_scheduler():
    scheduler = AsyncIOScheduler(timezone="UTC")
    # 🔹 Запускать задачу каждые 300 секунд
    scheduler.add_job(scheduled_job, "interval", minutes=5, id="news_collector")
    scheduler.start()
    print("🔁 Планировщик запущен: сбор и рассылка новостей каждую минуту.")
    return scheduler

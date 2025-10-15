# bot/handlers/user_handlers.py
from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот, который следит за новостями 🗞")

@router.message(Command("latest"))
async def cmd_latest(message: types.Message):
    from sqlalchemy import select
    from database.db import AsyncSessionLocal
    from database.models import News

    async with AsyncSessionLocal() as session:
        stmt = select(News).order_by(News.published_at.desc()).limit(5)
        result = await session.execute(stmt)
        news_list = result.scalars().all()

    if not news_list:
        await message.answer("Пока нет свежих новостей 😴")
        return

    response = "\n\n".join([f"<b>{n.title}</b>\n{n.url}" for n in news_list])
    await message.answer(response, parse_mode="HTML")

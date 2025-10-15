# bot/database/db.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from dotenv import load_dotenv
import os

load_dotenv()  # Загружаем .env

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Базовый класс для ORM моделей
class Base(DeclarativeBase):
    pass

# Создаём движок и фабрику сессий
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def init_db():
    """Проверяет наличие таблиц и создаёт их при необходимости"""
    import database.models  # Импортируем модели, чтобы SQLAlchemy их увидел

    async with engine.begin() as conn:
        # Проверка, есть ли таблицы
        result = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        ))
        tables = [row[0] for row in result]
        if not tables:
            print("Таблицы не найдены, создаём...")
            await conn.run_sync(Base.metadata.create_all)
        else:
            print("Все таблицы уже существуют ✅")

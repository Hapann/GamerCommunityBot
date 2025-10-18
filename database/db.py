# database/db.py
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from dotenv import load_dotenv
import psycopg2

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Базовый класс для ORM моделей
class Base(DeclarativeBase):
    pass


def ensure_database_exists():
    """Создаёт базу данных, если она отсутствует."""
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (POSTGRES_DB,))
        exists = cur.fetchone()
        if not exists:
            print(f"База данных '{POSTGRES_DB}' не найдена – создаём…")
            cur.execute(f'CREATE DATABASE "{POSTGRES_DB}";')
        else:
            print(f"База данных '{POSTGRES_DB}' уже существует ✅")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при проверке/создании базы данных: {e}")
        raise


# Создаём движок и фабрику сессий
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def init_db():
    """Создаёт таблицы в целевой базе, если их нет."""
    import database.models  # Импортируем модели, чтобы SQLAlchemy их увидел

    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        ))
        tables = [row[0] for row in result]
        if not tables:
            print("Таблицы не найдены, создаём…")
            await conn.run_sync(Base.metadata.create_all)
        else:
            print("Все таблицы уже существуют ✅")


if __name__ == "__main__":
    # Шаг 1 — убедиться, что база существует
    ensure_database_exists()
    # Шаг 2 — инициализировать таблицы
    asyncio.run(init_db())

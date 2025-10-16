# config.py
import os
from dotenv import load_dotenv
from datetime import datetime

# Загружаем .env
load_dotenv()

# --- Настройки БД ---
DB_CONFIG = {
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
}

# --- Основные параметры бота ---
TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

# --- Админы ---
# Строка вида: ADMIN_IDS=123456,789012
ADMIN_IDS = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]

# --- Ограничения медиа ---
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ
MAX_VOICE_SIZE = 20 * 1024 * 1024  # 20 МБ

# --- Настройки логирования ---
# Размер ротации, резервные файлы, включена ли ротация по дате и размеру
LOG_FILE_MAX_SIZE_MB = 5  # Макс. размер отдельного лога (в МБ)
LOG_FILE_MAX_SIZE = LOG_FILE_MAX_SIZE_MB * 1024 * 1024  # В байтах
LOG_FILE_BACKUP_COUNT = 20  # Сколько старых логов хранить

LOG_ROTATE = True                 # Включить ротацию
LOG_ROTATE_BY_SIZE = True        # Не используем ротацию по размеру (handled by date)
LOG_ROTATE_BY_TIME = True         # Да, ротация по дате (ежедневные папки)

# Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

# --- Дополнительные пути ---
def get_today_log_dir():
    """Возвращает путь к папке логов с текущей датой."""
    return os.path.join("logs", datetime.now().strftime("%Y-%m-%d"))

# --- Проверки обязательных параметров ---
# Проверка токена
if not TOKEN:
    raise EnvironmentError("❌ Не найден TOKEN в .env")

# Проверка БД
if not all(DB_CONFIG.values()):
    missing = [k for k, v in DB_CONFIG.items() if not v]
    raise EnvironmentError(f"❌ Отсутствуют параметры БД: {', '.join(missing)}")

# Проверка ID группы
try:
    if GROUP_CHAT_ID:
        GROUP_CHAT_ID = int(GROUP_CHAT_ID)
except (ValueError, TypeError):
    raise ValueError("❌ GROUP_CHAT_ID должен быть целым числом")

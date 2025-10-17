# logger/logger.py
import logging
import sys
from pathlib import Path
from datetime import datetime

# === Настройка путей для логов ===
# Базовая директория для логов
BASE_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

# Создаём основную папку logs/ при старте, если нет
BASE_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Подпапка для текущей даты
TODAY_DIR = BASE_LOG_DIR / datetime.now().strftime("%Y-%m-%d")
TODAY_DIR.mkdir(parents=True, exist_ok=True)

# Файл лога
LOG_FILE = TODAY_DIR / "gamecom_bot.log"

# === Настройка логгера ===
logger = logging.getLogger("gamecom_bot")
logger.setLevel(logging.DEBUG)

# Формат вывода
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# === Обработчик вывода в консоль ===
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# === Обработчик для записи в файл ===
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

# === Добавляем обработчики ===
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# --- Подавляем шум от некоторых библиотек ---
for noisy in ["aiogram", "aiohttp.access", "httpx", "httpcore"]:
    logging.getLogger(noisy).setLevel(logging.WARNING)
    logging.getLogger(noisy).propagate = False

# === Готово ===
logger.info(f"Инициализация логгера: {LOG_FILE}")

# logger/logger.py
import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent
LOG_FILE = LOG_DIR / "bot.log"

# Настройка логгера
logger = logging.getLogger("gamer_bot")
logger.setLevel(logging.DEBUG)

# Формат вывода
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Вывод в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Лог в файл
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

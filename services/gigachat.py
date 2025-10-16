# services/gigachat.py
import json
import requests
from logger.logger import logger

PROXY_HOST = "http://10.63.0.110:8000"

PROMPT_TEMPLATE = """
Ты — опытный игровой журналист. На вход ты получаешь ссылку на сайт или текст статьи.
Твоя задача — проанализировать материал и подготовить новостную заметку для игрового паблика в социальные сети.

Правила и цели:

Структура новости:
Заголовок: короткий, привлекательный, с динамикой (до 10 слов).
Подзаголовок (опционально): уточняет контекст или подтемы.
Основной текст (5–10 предложений):
изложи суть новости просто и увлекательно;
упомяни ключевые факты (что, кто, когда, почему, последствия/реакция);
добавь лёгкий публицистический стиль, но избегай кликбейта;
при упоминании источников – делай это естественно ("сообщает [название]").
Теги/хэштеги: 3–5 релевантных по теме (название игры, жанр, платформа, событие, студия).
Тон подачи: дружелюбный, умеренно эмоциональный, без грубости и фанатизма.
Imagine — ты автор игрового Telegram-канала или паблика во «ВКонтакте», где аудитория любит игры, но ценит точность.

Стиль:
избегай сложных оборотов, пиши живо;
допускается лёгкая ирония, если уместна;
помни о ясности и лаконичности.

На выходе верни результат в формате:

Заголовок: "Текст"

Текст: "Само содержание"

Ссылка на источник: {url_or_text}
🔖 Теги:
#пример #игры #новости

Входные данные:
URL сайта или полный текст статьи: {url_or_text}
"""


def get_gigachat_token():
    """Получаем access_token у прокси."""
    try:
        logger.debug("🔑 Запрашиваем токен у GigaChat-прокси...")
        resp = requests.post(f"{PROXY_HOST}/oauth/", timeout=5)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise ValueError("Прокси не вернул access_token")
        logger.debug("✅ Токен успешно получен.")
        return token
    except Exception as e:
        logger.error(f"💥 Ошибка получения токена: {e}")
        raise


def generate_gigachat_summary(url_or_text):
    """Отправка запроса в GigaChat и получение готовой новости с детализированным логированием."""
    try:
        token = get_gigachat_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        prompt = PROMPT_TEMPLATE.format(url_or_text=url_or_text)
        payload = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "repetition_penalty": 1,
        }

        # Логируем отправляемый промт (в разумных пределах)
        trimmed_prompt = prompt[:600] + ("…" if len(prompt) > 600 else "")
        logger.debug(f"➡️ Отправляем запрос в GigaChat для URL: {url_or_text}\n---PROMPT START---\n{trimmed_prompt}\n---PROMPT END---")

        resp = requests.post(f"{PROXY_HOST}/chat/completions", headers=headers, json=payload, timeout=90)
        resp.raise_for_status()

        data = resp.json()
        reply = data["choices"][0]["message"]["content"]

        # Урезаем длинный ответ для читаемости логов
        trimmed_reply = reply[:600] + ("…" if len(reply) > 600 else "")
        logger.debug(f"⬅️ Ответ GigaChat для URL: {url_or_text}\n---REPLY START---\n{trimmed_reply}\n---REPLY END---")

        logger.info(f"✨ Ответ получен от GigaChat ({len(reply)} символов).")
        return reply

    except requests.Timeout:
        logger.error(f"⏰ Таймаут при обращении к GigaChat для {url_or_text}")
        return f"⚠️ Сервер GigaChat не ответил вовремя. Источник: {url_or_text}"
    except Exception as e:
        # Сохраняем с деталями JSON для последующей диагностики
        try:
            debug_data = json.dumps(resp.json(), ensure_ascii=False, indent=2)[:1000]
            logger.debug(f"📦 Ответ сервера при ошибке: {debug_data}")
        except Exception:
            pass

        logger.error(f"💥 Ошибка во время общения с GigaChat для {url_or_text}: {e}")
        return f"⚠️ Ошибка генерации новости\n{url_or_text}"

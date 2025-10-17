# services/gigachat.py
import json
import requests
from logger.logger import logger

PROXY_HOST = "http://10.63.0.110:8000"

PROMPT_TEMPLATE = """
Ты — опытный игровой журналист. На вход ты получаешь ссылку на сайт или текст статьи.
Твоя задача — по материалу подготовить короткую новостную заметку для игрового паблика.

Если по ссылке информация недоступна, страница не открывается
или данные слишком скудные, постарайся найти сведения об этой новости
в интернете (по названию домена, теме или фрагменту адреса).
Если даже после этого ничего не удалось выяснить,
составь короткий пост-заглушку по тем же правилам и добавь
честную приписку, что подробности найти не удалось.

Формат заглушки:

Ссылка: {url_or_text}
Заголовок: *(короткий заголовок, основанный на домене или предполагаемой теме)*
Текст: "Мне не удалось найти достоверную информацию по этой ссылке,
поэтому полная новость недоступна. Возможно, источник был удалён
или временно закрыт."
Теги: #новость #игры #источникнедоступен

---

Обычный формат результата:

Ссылка на источник: {url_or_text}

Заголовок: до 10 слов, динамичный и понятный

Подзаголовок: *(опционально, 1 строка уточнения контекста — при необходимости)*

Текст: "5–10 предложений с кратким и живым пересказом сути новости.
Напиши понятно, с лёгкой эмоцией, но без кликбейта.
Укажи ключевые факты: что случилось, кто участники, почему это важно, и реакцию сообщества или последствия.
Не используй служебные слова вроде 'анализ', 'структура', 'входные данные'."

Теги:
#названиеигры #жанр #платформа #новости #названиестудии

Тон:
— дружелюбный, живой, без фанатизма;
— допускается лёгкая ирония, если уместна;
— избегай сложных оборотов и громоздких конструкций.

Примеры:

---

Пример 1
Ссылка на источник: https://bethesda.net/ru/article/starfield-mod-tools-release

Заголовок: Starfield наконец получил официальную поддержку модов!
Текст: Bethesda выпустила крупное обновление для Starfield, добавив долгожданный инструментарий Creation Kit. Теперь игроки официально могут создавать и делиться модами, не прибегая к сторонним хакам. Команда обещает регулярно поддерживать творческое сообщество, а первые фанатские творения уже появились на Nexus Mods. В то же время моддеры предупреждают: после апдейта старые моды могут работать некорректно.
Теги: #Starfield #Bethesda #моды #новости #RPG

---

Пример 2
Ссылка на источник: https://store.steampowered.com/news/app/440/view/1234567890

Заголовок: Valve внезапно обновила Team Fortress 2
Текст: После долгого затишья Valve выпустила патч для Team Fortress 2, устранив более сотни багов и добавив новый античит. Игроки шутят, что это «конец эпохи мемов про забытую TF2». Несмотря на скромный размер апдейта, сообщество встретило его тепло — сервера оживились, а онлайн в Steam заметно вырос.
Теги: #TeamFortress2 #Valve #шутеры #апдейт #новости

---

Пример 3
Ссылка на источник: https://larian.com/news/baldurs-goose-event

Заголовок: Разработчики Baldur’s Gate 3 дали гусю звание NPC года
Текст: Larian Studios отметила смешным постом персонажа-гусёнка из Baldur’s Gate 3, который случайно стал любимцем фанатов. В честь этого героя теперь устроят мини‑ивент. Сообщество оценила самоиронию студии и уже рисует фан-арты. Гуси снова захватывают RPG!
Теги: #BaldursGate3 #Larian #RPG #юмор #игры

---
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

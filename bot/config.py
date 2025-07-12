"""Global configuration, country data and text templates for 5592 CARGO bot.
All outgoing texts are wrapped in <b>…</b> so that Telegram shows them bold.
If you need to tweak wording – change here, handlers read only these constants.
"""
from __future__ import annotations

import os
from typing import Dict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Default location of the Excel file that stores user data. Adjust if needed.
EXCEL_FILE_PATH: str = os.path.join("data", "5592карго.xlsx")

# ---------------------------------------------------------------------------
# Tokens / secrets
# ---------------------------------------------------------------------------
# Telegram bot token: в продакшен-окружении задайте переменную среды
# TELEGRAM_BOT_TOKEN, иначе бот не запустится.
# Используем токен, сохранённый в исходном проекте. При необходимости можно
# переопределить переменной среды TELEGRAM_BOT_TOKEN.
BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN") or "7044487894:AAGJ12igzGp3Kb0pmsf6eDtxJRjWc8LTclo"

# Если подключаете Notion или иной бекенд – храните токены тоже здесь
NOTION_TOKEN: str | None = os.getenv("NOTION_TOKEN") or "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"
NOTION_DATABASE_ID: str | None = os.getenv("NOTION_DATABASE_ID") or "1f24d0db264a80428562f4930c52f95e"

# ---------------------------------------------------------------------------
# Countries: dial-code and phone-digits rules
# ---------------------------------------------------------------------------
COUNTRIES: Dict[str, Dict[str, int]] = {
    "Кыргызстан": {"code": "996", "digits": 9},
    "Казахстан": {"code": "7", "digits": 10},
    "Россия": {"code": "7", "digits": 10},
    "Узбекистан": {"code": "998", "digits": 9},
    "Таджикистан": {"code": "992", "digits": 9},
    "Китай": {"code": "86", "digits": 11},
}

# ---------------------------------------------------------------------------
# Text templates (HTML bold by default). Use .format(**kwargs) where needed.
# ---------------------------------------------------------------------------
T_START_WELCOME = (
    "<b>Здравствуйте! Вас приветствует бот 5592 CARGO.</b>\n"
    "<b>У вас есть уникальный код?</b>"
)

T_START_LOGGED = (
    "<b>Здравствуйте! Вы уже зарегистрированы.</b>\n"
    "<b>Хотите пройти регистрацию заново?</b>\n\n"
    "<b>/info – мой профиль</b>\n"
    "<b>/myproducts – мои товары</b>"
)

T_HELP = (
    "<b>Доступные команды:</b>\n"
    "/start – начало работы\n"
    "/myproducts – список ваших товаров\n"
    "/info – ваш профиль\n"
    "/cancel – отменить текущее действие\n"
    "/help – эта справка"
)

# --- Авторизация по коду
T_ASK_HAVE_CODE = {
    "yes": "Да, у меня есть код",
    "no": "Нет, у меня нет кода",
}

T_ENTER_CODE = "<b>Введите ваш уникальный код:</b>"
T_LOGIN_SUCCESS = "<b>Вход выполнен успешно! Ваш код: <code>{code}</code></b>"
T_CODE_NOT_FOUND = (
    "<b>Не удалось найти введённый код.</b>\n"
    "<b>Попробуйте ещё раз или зарегистрируйтесь.</b>"
)

# --- Регистрация: шаги вопросов
T_REGISTER_BEGIN = "<b>Хорошо, давайте начнём регистрацию.</b>"
# --- Город
T_ASK_CITY = "<b>Шаг 1. Выберите город, в котором проживаете:</b>"
T_OTHER_CITY_MSG = "<b>В ближайшее время с вами свяжутся наши сотрудники, можете продолжать регистрацию</b>"
T_ASK_NAME = "<b>Шаг 2. Введите ваше имя:</b>"
T_ASK_SURNAME = "<b>Шаг 3. Введите вашу фамилию:</b>"
T_ASK_PHONE = ("<b>Шаг 4. Введите ваш мобильный номер телефона.\n</b>"
    "<b>Шаблон:\n</b>"
    "<b>Кыргызстан - 0 XXX XXX XXX\n</b>"
    "<b>Казахстан - 8 XXX XXX XXXX\n</b>"
    "<b>Россия - 8 XXX XXX XX XX\n</b>"
    "<b>Узбекистан - 8 XX XXX XX XX\n</b>"
    "<b>Таджикистан - 0 XX XXX XX XX\n</b>"
    "<b>Китай - 1XX XXXX XXXX </b>"
)
T_PHONE_EXISTS = (
    "<b>Этот номер телефона уже есть в базе данных.</b>\n"
    "<b>Введите другой номер телефона.</b>"
)
T_ASK_COUNTRY = "<b>Шаг 5. Выберите страну, где был зарегистрирован ваш WhatsApp-номер телефона:</b>"
T_PHONE_LENGTH_ERR = (
    "<b>Ошибка!</b> Длина номера <code>{digits}</code> цифр не подходит для страны {country} (нужно {need}).\n"
    "<b>Введите номер заново.</b>"
)

# --- Validation error texts for new registration flow
T_ERR_INVALID_NAME = "<b>Имя и фамилия могут содержать только буквы, пробел или дефис.</b>"
T_ERR_INVALID_PHONE = "<b>Пожалуйста, введите корректный номер телефона (только цифры).</b>"
T_ASK_WHATSAPP = "<b>Шаг 5. Введите WhatsApp-номер телефона. Вы выбрали {country}. Введите {digits} цифр после +{code}...</b>"
T_WHATSAPP_FORMAT_ERR = (
    "<b>Неверный формат номера WhatsApp.</b> Ожидается {need} цифр."
)
T_WHATSAPP_EXISTS = "<b>Этот номер WhatsApp уже зарегистрирован. Введите другой.</b>"
T_REGISTER_SUCCESS = (
    "<b>Регистрация прошла успешно!</b>\n"
    "<b>Ваш уникальный код: <code>{code}</code></b>\n\n"
    "<b>/myproducts</b> – мои товары\n"
    "<b>/info</b> – мой профиль\n"
    "<b>/help</b> – помощь"
)

# Unified success text used in new inline registration flow
T_REG_COMPLETE = (
    "<b>✅ Регистрация завершена!</b>\n\n"
    "<b>👤 Ваш профиль:</b>\n\n"
    "<b>Код:</b> {code}\n"
    "<b>Имя:</b> {name}\n"
    "<b>Фамилия:</b> {surname}\n"
    "<b>Мобильный номер:</b> {phone}\n"
    "<b>WhatsApp номер:</b> {whatsapp}\n"
    "<b>Город:</b> {city}\n\n"
    "<b>/myproducts</b> – мои товары\n"
    "<b>/info</b> – мой профиль\n"
    "<b>/help</b> – помощь"
)

# --- Логин
T_LOGIN_SUCCESS = (
    "<b>Вход выполнен успешно!</b>\n\n"
    "<b>Доступные команды</b>\n"
    "/myproducts – список ваших товаров\n"
    "/info – ваш профиль\n"
    "/help – эта справка"
)

# --- Профиль / товары
T_NO_LOGIN = (
    "<b>Чтобы воспользоваться этой командой, войдите или зарегистрируйтесь.</b>\n"
    "<b>У вас есть уникальный код?</b>"
)
T_PRODUCTS_HEADER = "<b>📦 Ваши товары:</b>\n\n"
T_NO_PRODUCTS = "<b>У вас пока нет зарегистрированных товаров.</b>"
T_PROFILE = (
    "<b>👤 Ваш профиль:</b>\n\n"
    "<b>Код:</b> <code>{code}</code>\n"
    "<b>Имя:</b> {name}\n"
    "<b>Фамилия:</b> {surname}\n"
    "<b>Мобильный номер:</b> {phone}\n"
    "<b>WhatsApp номер:</b> {whatsapp}\n"
    "<b>Город:</b> {city}"
)

# --- Навигация
T_REG_CANCELLED = "<b>Регистрация отменена. Вы можете начать заново с /start.</b>"

# Mapping для Reply-кнопок «Попробовать снова / Регистрация»
T_RETRY = {
    "retry": "Попробовать снова",
    "register": "Регистрация",
}

"""Helper functions that build Reply- and Inline- keyboards for the bot.
Keeps UI logic in one place so handlers remain clean.
"""
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from .config import COUNTRIES, T_RETRY

__all__ = [
    "yes_no_reply_kb",  # legacy name, returns reply keyboard or inline wrapper
    "retry_register_reply_kb",  # legacy name, returns inline kb for retry/register
    "create_retry_register_inline_kb",
    "create_country_inline_kb",
    "create_nav_inline_kb",
    "create_city_inline_kb",
    "create_yes_no_inline_kb",

    "KB_REMOVE",
]

# ---------------------------------------------------------------------------
# Single instance to remove reply keyboard
# ---------------------------------------------------------------------------
KB_REMOVE = ReplyKeyboardRemove()

# ---------------------------------------------------------------------------
# Legacy wrapper keyboards for backward compatibility
# ---------------------------------------------------------------------------

def yes_no_reply_kb() -> ReplyKeyboardMarkup:
    """Legacy function kept for backward compatibility.
    Returns a simple Yes/No reply keyboard used in /start and other flows.
    """
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("Да, у меня есть код"))
    kb.add(KeyboardButton("Нет, у меня нет кода"))
    return kb


def retry_register_reply_kb():
    """Legacy alias that returns the inline retry/register keyboard."""
    return create_retry_register_inline_kb()

# ---------------------------------------------------------------------------
# Inline-only keyboards (preferred going forward)
# ---------------------------------------------------------------------------

def create_retry_register_inline_kb() -> InlineKeyboardMarkup:
    """Inline keyboard for when code not found: Retry or Register."""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(T_RETRY["retry"], callback_data="code_retry"))
    kb.add(InlineKeyboardButton(T_RETRY["register"], callback_data="code_register"))
    return kb


def create_yes_no_inline_kb() -> InlineKeyboardMarkup:
    """Inline keyboard for Yes/No questions."""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Да", callback_data="reg_whatsapp_yes"),
        InlineKeyboardButton("Нет", callback_data="reg_whatsapp_no")
    )
    kb.row(
        InlineKeyboardButton("Назад", callback_data="reg_back_to_country"),
        InlineKeyboardButton("Отменить регистрацию", callback_data="reg_cancel")
    )
    return kb

def create_country_inline_kb() -> InlineKeyboardMarkup:
    """Inline keyboard with a list of countries."""
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text, callback_data=f"country_select_{text}") for text in COUNTRIES.keys()]
    kb.add(*buttons)
    kb.row(
        InlineKeyboardButton("Назад", callback_data="reg_back_to_phone"),
        InlineKeyboardButton("Отменить регистрацию", callback_data="reg_cancel")
    )
    return kb

# ---------------------------------------------------------------------------
# Клавиатура выбора города (первый шаг регистрации)
# ---------------------------------------------------------------------------

def create_city_inline_kb() -> InlineKeyboardMarkup:
    """Inline keyboard for city selection at the first step."""
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("Кыргызстан: Бишкек", callback_data="city_select_Бишкек"),
        InlineKeyboardButton("Казахстан: Астана", callback_data="city_select_Астана"),
        InlineKeyboardButton("Другой город", callback_data="city_select_Другой"),
    )
    kb.add(InlineKeyboardButton("Отменить регистрацию", callback_data="reg_cancel"))
    return kb

# ---------------------------------------------------------------------------
# Inline keyboard for /start question (есть ли код?)
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Inline keyboards (Back / Cancel for registration flow)
# ---------------------------------------------------------------------------

def create_nav_inline_kb(previous_step: str) -> InlineKeyboardMarkup:
    """Create inline "Back" and "Cancel" buttons.
    If previous_step is 'start', only shows a 'Cancel' button.
    """
    kb = InlineKeyboardMarkup(row_width=1)
    if previous_step in ("start", "cancel"):
        kb.add(InlineKeyboardButton("Отменить регистрацию", callback_data="reg_cancel"))
    else:
        kb.add(InlineKeyboardButton("Назад", callback_data=f"reg_back_to_{previous_step}"))
        kb.add(InlineKeyboardButton("Отменить регистрацию", callback_data="reg_cancel"))
    return kb

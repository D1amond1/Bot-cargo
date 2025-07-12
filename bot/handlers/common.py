"""Common command handlers: /start, /help, /cancel, /info, /myproducts"""
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

from ..config import (
    T_START_WELCOME,

    T_HELP,
    T_ASK_HAVE_CODE,
    T_ENTER_CODE,
    T_NO_LOGIN,
    T_PRODUCTS_HEADER,
    T_NO_PRODUCTS,
    T_PROFILE,
    EXCEL_FILE_PATH,
)
import os
import json
from ..keyboards import (
    yes_no_reply_kb,
    retry_register_reply_kb,
    KB_REMOVE,
)
# Legacy database/Notion helpers were removed. Provide minimal fallbacks.
from ..utils import generate_unique_code  # placeholder import, not used here


USER_CODES_JSON = os.path.join(os.path.dirname(EXCEL_FILE_PATH), "user_codes.json")

def _load_user_codes():
    if os.path.exists(USER_CODES_JSON):
        with open(USER_CODES_JSON, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def _save_user_codes(data: dict):
    os.makedirs(os.path.dirname(USER_CODES_JSON), exist_ok=True)
    with open(USER_CODES_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_code(user_id: int):
    """Возвращает активный уникальный код, выбранный пользователем ранее (login), или None."""
    codes = _load_user_codes()
    return codes.get(str(user_id))


def get_products_by_code(code: str):
    """Возвращает список товаров из базы Notion по уникальному коду.

    Каждый элемент:
    {"track": str, "status": str, "date": str}
    При ошибке или пустом результате — возвращает []."""
    from bot.config import NOTION_TOKEN, NOTION_DATABASE_ID
    try:
        if not (NOTION_TOKEN and NOTION_DATABASE_ID):
            return []
        from notion_client import Client
        notion = Client(auth=NOTION_TOKEN)
        # Фильтр: колонка "Уникальный код" содержит exact code
        query = notion.databases.query(
            **{
                "database_id": NOTION_DATABASE_ID,
                "filter": {
                    "property": "Уникальный код пользователя",
                    "rich_text": {"equals": code},
                },
            }
        )
        items = []
        for res in query.get("results", []):
            props = res.get("properties", {})
            track = _extract_text(props.get("Трек-код"))
            status = _extract_multi_select(props.get("Статус"))
            date_val = _extract_date(props.get("Обновлено"))
            items.append({"track": track or "-", "status": status or "-", "date": date_val or "-"})
        return items
    except Exception:
        return []

def _extract_text(prop):
    if not prop:
        return ""
    if prop.get("type") == "title":
        return "".join([t.get("plain_text", "") for t in prop["title"]])
    if prop.get("type") == "rich_text":
        return "".join([t.get("plain_text", "") for t in prop["rich_text"]])
    return ""

def _extract_multi_select(prop):
    if not prop or prop.get("type") != "multi_select":
        return ""
    arr = prop.get("multi_select", [])
    return ", ".join([v.get("name", "") for v in arr])

def _extract_date(prop):
    if not prop or prop.get("type") != "date":
        return ""
    dt = prop.get("date")
    return dt.get("start") if dt else ""
from ..states import Registration

from aiogram import Dispatcher, Bot


def register_common_handlers(dp: Dispatcher, bot: Bot):
    # /start
    @dp.message_handler(Command("start"), state="*")
    async def cmd_start(message: types.Message, state: FSMContext):
        await state.finish()
        await bot.send_photo(
            message.chat.id,
            photo=open("assets/welcome.jpg", "rb"),
            caption=T_START_WELCOME,
            parse_mode="HTML",
            reply_markup=yes_no_reply_kb(),
        )

    # /help
    @dp.message_handler(Command("help"), state="*")
    async def cmd_help(message: types.Message):
        await message.answer(T_HELP, parse_mode="HTML", reply_markup=KB_REMOVE)

    # /cancel during registration
    @dp.message_handler(Command("cancel"), state=Registration.all_states)
    async def cmd_cancel(message: types.Message, state: FSMContext):
        await state.finish()
        await message.answer("<b>Регистрация отменена.</b>", parse_mode="HTML", reply_markup=KB_REMOVE)

    # /myproducts
    @dp.message_handler(Command("myproducts"), state="*")
    async def cmd_products(message: types.Message):
        args = message.get_args()
        code = args.strip() if args else get_user_code(message.from_user.id)
        if not code:
            await message.answer("Укажите код после команды, например: /myproducts ABC123", parse_mode="HTML")
            return
        products = get_products_by_code(code)
        if not products:
            await message.answer(T_NO_PRODUCTS, parse_mode="HTML", reply_markup=KB_REMOVE)
            return
        response = T_PRODUCTS_HEADER
        for p in products:
            response += (
                f"<b>Трек-код:</b> {p['track']}\n"
                f"<b>Статус:</b> {p['status']}\n"
                f"<b>Дата:</b> {p['date']}\n\n"
            )
        await message.answer(response, parse_mode="HTML", reply_markup=KB_REMOVE)

    # /info
    @dp.message_handler(Command("info"), state="*")
    async def cmd_info(message: types.Message):
        args = message.get_args()
        code = args.strip() if args else get_user_code(message.from_user.id)
        if not code:
            await message.answer("Укажите код после команды, например: /info ABC123", parse_mode="HTML")
            return
        # Retrieve profile data from DB/Excel (simplified)
        from pandas import read_excel  # lazy import
        import os
        excel_path = os.path.join("data", "5592карго.xlsx")
        try:
            df = read_excel(excel_path, engine="openpyxl")
            row = df[df["Уникальный код"].astype(str) == code]
            if row.empty:
                await message.answer("<b>Профиль не найден.</b>", parse_mode="HTML")
                return
            record = row.iloc[0]
            caption = T_PROFILE.format(
                code=code,
                name=record.get("Имя", "-"),
                surname=record.get("Фамилия", "-"),
                phone=record.get("Моб.номер", "-"),
                country=record.get("Страна", "-"),
                whatsapp=record.get("WhatsApp номер", record.get("WhatsApp", "-")),
                city=record.get("Город", "-")
            )
            await bot.send_photo(
                message.chat.id,
                photo=open("assets/success.jpg", "rb"),
                caption=caption,
                parse_mode="HTML",
                reply_markup=KB_REMOVE,
            )
        except FileNotFoundError:
            await message.answer("<b>Файл данных не найден.</b>", parse_mode="HTML")

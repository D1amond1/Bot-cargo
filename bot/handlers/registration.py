# bot/handlers/registration.py

import os
import re
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageToDeleteNotFound
from string import ascii_letters

from ..config import (
    BOT_TOKEN,
    EXCEL_FILE_PATH,
    COUNTRIES,
    T_ASK_NAME,
    T_ASK_SURNAME,
    T_ASK_PHONE,
    T_ASK_COUNTRY,
    T_ASK_CITY,
    T_OTHER_CITY_MSG,
    T_ASK_WHATSAPP,
    T_REG_COMPLETE,
    T_REG_CANCELLED,
    T_WHATSAPP_FORMAT_ERR,
    T_WHATSAPP_EXISTS,
    T_REGISTER_SUCCESS,
    T_ERR_INVALID_NAME,
    T_ERR_INVALID_PHONE,
    T_PHONE_EXISTS,
    T_CODE_NOT_FOUND,
    T_LOGIN_SUCCESS,
    T_ASK_HAVE_CODE,
    T_ENTER_CODE,
)
from ..keyboards import (
    create_retry_register_inline_kb,
    create_country_inline_kb,
    create_nav_inline_kb,
    create_city_inline_kb,
    create_yes_no_inline_kb,
    KB_REMOVE,
)
from ..states import Registration
# Legacy database functions removed; provide stubs for now.

def save_user_data(data: dict):
    """Сохраняем профиль пользователя в Excel-файл.

    Ожидает, что в *data* уже лежат все необходимые поля,
    включая city, name, surname, phone_raw, country, whatsapp, code
    и Telegram ID (можно добавить позже). Если файла нет – создаёт.
    """
    required_cols = [
        "Город",
        "Имя",
        "Фамилия",
        "Моб.номер",
        "Страна",
        "WhatsApp номер",
        "Уникальный код",
        "Telegram ID",
    ]

    row = {
        "Город": data.get("city", ""),
        "Имя": data.get("name", ""),
        "Фамилия": data.get("surname", ""),
        "Моб.номер": data.get("phone_raw", ""),
        "Страна": data.get("country", ""),
        "WhatsApp номер": data.get("whatsapp", ""),
        "Уникальный код": data.get("code", ""),
        "Telegram ID": data.get("telegram_id", ""),
    }

    # Создаём/обновляем файл
    if os.path.exists(EXCEL_FILE_PATH):
        try:
            df = pd.read_excel(EXCEL_FILE_PATH, engine="openpyxl")
        except Exception:
            df = pd.DataFrame(columns=required_cols)
    else:
        df = pd.DataFrame(columns=required_cols)

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    # Обеспечиваем порядок колонок
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
    df = df[required_cols]
    df.to_excel(EXCEL_FILE_PATH, index=False)

def save_user_code(user_id: int, phone: str, code: str):
    """Link Telegram user ID to existing code row in Excel (login) or update current row."""
    if not os.path.exists(EXCEL_FILE_PATH):
        return
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, engine="openpyxl")
    except Exception:
        return
    # locate row by code
    idx = df.index[df["Уникальный код"].astype(str) == str(code)]
    if not idx.empty:
        df.at[idx[0], "Telegram ID"] = user_id
        # также при желании можем обновить мобильный номер, если передан
        if phone:
            df.at[idx[0], "Моб.номер"] = phone
        df.to_excel(EXCEL_FILE_PATH, index=False)
from bot.utils import generate_unique_code

bot = Bot(token=BOT_TOKEN)

# --- Helper functions to manage UI --- 

async def delete_last_bot_message(chat_id: int, state: FSMContext, bot: Bot):
    """Deletes the last message sent by the bot if its ID is in state."""
    data = await state.get_data()
    last_bot_msg_id = data.get("last_bot_message_id")
    if last_bot_msg_id:
        try:
            await bot.delete_message(chat_id, last_bot_msg_id)
        except MessageToDeleteNotFound:
            pass # Message already deleted

async def ask_question(chat_id: int, text: str, reply_markup, state: FSMContext, bot: Bot):
    """Sends a question and saves its message_id to state."""
    await delete_last_bot_message(chat_id, state, bot)
    msg = await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode="HTML")
    await state.update_data(last_bot_message_id=msg.message_id)

# --- Helper functions for each registration step ---

async def ask_for_city(chat_id: int, state: FSMContext, bot: Bot):
    """Первый шаг – выбор города."""
    # если ранее было информационное сообщение about other city – удаляем
    data = await state.get_data()
    extra_id = data.get("extra_msg_id")
    if extra_id:
        try:
            await bot.delete_message(chat_id, extra_id)
        except MessageToDeleteNotFound:
            pass
        await state.update_data(extra_msg_id=None)
    await Registration.city.set()
    await ask_question(chat_id, T_ASK_CITY, create_city_inline_kb(), state, bot)



async def ask_for_name(chat_id: int, state: FSMContext, bot: Bot):
    # Удаляем инфо-сообщение, если ещё не удалили
    data = await state.get_data()
    info_id = data.get("info_msg_id")
    if info_id:
        try:
            await bot.delete_message(chat_id, info_id)
        except MessageToDeleteNotFound:
            pass
        await state.update_data(info_msg_id=None)

    await Registration.name.set()
    await ask_question(chat_id, T_ASK_NAME, create_nav_inline_kb("city"), state, bot)

async def ask_for_surname(chat_id: int, state: FSMContext, bot: Bot):
    await Registration.surname.set()
    await ask_question(chat_id, T_ASK_SURNAME, create_nav_inline_kb("name"), state, bot)

async def ask_for_phone(chat_id: int, state: FSMContext, bot: Bot):
    await Registration.phone.set()
    await ask_question(chat_id, T_ASK_PHONE, create_nav_inline_kb("surname"), state, bot)

async def ask_for_country(chat_id: int, state: FSMContext, bot: Bot):
    await Registration.country.set()
    await ask_question(chat_id, T_ASK_COUNTRY, create_country_inline_kb(), state, bot)

async def ask_for_whatsapp(chat_id: int, state: FSMContext, bot: Bot):
    """Ask for WhatsApp phone: text is formatted with actual country info."""
    data = await state.get_data()
    country_name = data.get("country")
    country_info = COUNTRIES[country_name]
    text = T_ASK_WHATSAPP.format(
        country=country_name,
        digits=country_info["digits"],
        code=country_info["code"],
    )
    await Registration.whatsapp.set()
    # Показываем только кнопки «Назад»/«Отмена», без Да/Нет
    await ask_question(chat_id, text, create_nav_inline_kb("country"), state, bot)

async def process_final_data(message: types.Message, state: FSMContext, bot: Bot):
    await delete_last_bot_message(message.chat.id, state, bot)
    data = await state.get_data()
    # добавляем telegram_id
    data["telegram_id"] = message.from_user.id
    save_user_data(data)
    # сохраняем маппинг user_id -> code в user_codes.json
    try:
        from ..handlers.common import _load_user_codes, _save_user_codes
        codes = _load_user_codes()
        codes[str(message.from_user.id)] = data.get("code")
        _save_user_codes(codes)
    except Exception:
        pass
    await message.answer(T_REG_COMPLETE.format(**data), parse_mode="HTML", reply_markup=KB_REMOVE)
    await state.finish()


# ---------------------------------------------------------------------------
# Обработчик inline-кнопок выбора города (первый шаг)
# ---------------------------------------------------------------------------

async def process_city_callback(call: types.CallbackQuery, state: FSMContext):
    """Сохраняем выбранный город и переходим к вводу имени."""
    await call.answer()
    city_raw = call.data.replace("city_select_", "")
    # Если "Другой город" – отправляем доп. сообщение и сохраняем его ID
    if city_raw == "Другой":
        info_msg = await call.message.answer(T_OTHER_CITY_MSG, parse_mode="HTML")
        await state.update_data(extra_msg_id=info_msg.message_id)
    # Для Excel хотим видеть строку "Другой город"
    stored_city = "Другой город" if city_raw == "Другой" else city_raw
    await state.update_data(city=stored_city)
    # Переходим к следующему шагу
    await ask_for_name(call.message.chat.id, state, bot)

# --- Main registration function ---




def register_registration_handlers(dp: Dispatcher, bot: Bot):
    # Регистрируем обработчик выбора города
    dp.callback_query_handler(lambda c: c.data.startswith("city_select_"), state=Registration.city)(process_city_callback)

    from ..config import T_ASK_HAVE_CODE, T_ENTER_CODE  # texts
    from ..keyboards import KB_REMOVE as _KB_REMOVE

    # --- Handle Yes/No reply from start message ---
    @dp.message_handler(lambda m: m.text == T_ASK_HAVE_CODE["no"], state="*")
    async def handle_no_code(message: types.Message, state: FSMContext):
        await message.answer("<b>Хорошо, давайте начнём регистрацию.</b>", parse_mode="HTML", reply_markup=KB_REMOVE)

        await state.finish()
        await message.delete()
        await ask_for_city(message.chat.id, state, bot)

    @dp.message_handler(lambda m: m.text == T_ASK_HAVE_CODE["yes"], state="*")
    async def handle_yes_code(message: types.Message, state: FSMContext):
        await state.finish()
        await Registration.check_code.set()
        await ask_question(message.chat.id, T_ENTER_CODE, KB_REMOVE, state, bot)


    # --- Navigation Callbacks ---
    @dp.callback_query_handler(lambda c: c.data.startswith("reg_back_to_"), state=Registration.all_states)
    async def reg_back_callback(call: types.CallbackQuery, state: FSMContext):
        step = call.data.split("_")[-1]

        if step == "city":
            await ask_for_city(call.message.chat.id, state, bot)
        elif step == "name":
            await ask_for_name(call.message.chat.id, state, bot)
        elif step == "surname":
            await ask_for_surname(call.message.chat.id, state, bot)
        elif step == "phone":
            await ask_for_phone(call.message.chat.id, state, bot)
        elif step == "country":
            await ask_for_country(call.message.chat.id, state, bot)

    @dp.callback_query_handler(text="reg_cancel", state=Registration.all_states)
    async def reg_cancel_callback(call: types.CallbackQuery, state: FSMContext):
        await delete_last_bot_message(call.message.chat.id, state, bot)
        await call.message.answer(T_REG_CANCELLED, parse_mode="HTML", reply_markup=KB_REMOVE)
        await state.finish()

    # --- State Handlers (Input Processing) ---

    @dp.message_handler(state=Registration.name)
    async def process_name(message: types.Message, state: FSMContext):
        name = message.text.strip()
        await message.delete()
        if not re.match(r"^[A-Za-zА-Яа-яЁё]+([ -][A-Za-zА-Яа-яЁё]+)*$", name):
            await ask_question(message.chat.id, f"{T_ERR_INVALID_NAME}\n\n{T_ASK_NAME}", create_nav_inline_kb("cancel"), state, bot)
            return
        await state.update_data(name=name)
        await ask_for_surname(message.chat.id, state, bot)

    @dp.message_handler(state=Registration.surname)
    async def process_surname(message: types.Message, state: FSMContext):
        surname = message.text.strip()
        await message.delete()
        if not re.match(r"^[A-Za-zА-Яа-яЁё]+([ -][A-Za-zА-Яа-яЁё]+)*$", surname):
            await ask_question(message.chat.id, f"{T_ERR_INVALID_NAME}\n\n{T_ASK_SURNAME}", create_nav_inline_kb("name"), state, bot)
            return
        await state.update_data(surname=surname)
        await ask_for_phone(message.chat.id, state, bot)

    @dp.message_handler(state=Registration.phone)
    async def process_phone(message: types.Message, state: FSMContext):
        phone_raw = "".join(re.findall(r"\d+", message.text))
        await message.delete()
        if not phone_raw:
            await ask_question(message.chat.id, f"{T_ERR_INVALID_PHONE}\n\n{T_ASK_PHONE}", create_nav_inline_kb("surname"), state, bot)
            return

        # Проверяем, нет ли такого номера уже в базе Excel
        if os.path.exists(EXCEL_FILE_PATH):
            df = pd.read_excel(EXCEL_FILE_PATH, engine="openpyxl")
            existing_phone = df.get("Моб.номер", pd.Series(dtype=str)).astype(str).str.lstrip("'").values
            if not df.empty and phone_raw in existing_phone:
                await ask_question(message.chat.id, T_PHONE_EXISTS, create_nav_inline_kb("surname"), state, bot)
                return
        await state.update_data(phone_raw=phone_raw)
        await ask_for_country(message.chat.id, state, bot)
    
    @dp.callback_query_handler(lambda c: c.data.startswith("country_select_"), state=Registration.country)
    async def process_country_callback(call: types.CallbackQuery, state: FSMContext):
        country = call.data.replace("country_select_", "")
        await state.update_data(country=country)
        await ask_for_whatsapp(call.message.chat.id, state, bot)

    @dp.callback_query_handler(lambda c: c.data.startswith("reg_whatsapp_"), state=Registration.whatsapp)
    async def process_whatsapp_callback(call: types.CallbackQuery, state: FSMContext):
        answer = call.data.replace("reg_whatsapp_", "")
        data = await state.get_data()
        if answer == "yes":
            wp_number = country_info["code"] + data["phone_raw"]
        elif not message.text.isdigit() or len(message.text) != country_info["digits"]:
            # Удаляем неверный ввод пользователя и предыдущее сообщение бота
            await message.delete()
            await delete_last_bot_message(message.chat.id, state, bot)

            err_text = T_WHATSAPP_FORMAT_ERR.format(need=country_info["digits"])
            await ask_question(message.chat.id, err_text, create_nav_inline_kb("country"), state, bot)
            return
        else:
            wp_number = country_info["code"] + message.text
        # duplicate check
        if os.path.exists(EXCEL_FILE_PATH):
            df = pd.read_excel(EXCEL_FILE_PATH, engine="openpyxl")
            existing_wp = df.get("WhatsApp", pd.Series(dtype=str)).astype(str).str.lstrip("'").values
            if not df.empty and wp_number in existing_wp:
                # Удаляем неверный ввод пользователя и предыдущее сообщение бота
                await message.delete()
                await delete_last_bot_message(message.chat.id, state, bot)
                await ask_question(message.chat.id, T_WHATSAPP_EXISTS, create_nav_inline_kb("country"), state, bot)
                return
        # Save registration (унифицировано)
        code = generate_unique_code()
        mobile_phone = data["phone_raw"]
        await state.update_data(code=code, phone=mobile_phone, whatsapp=wp_number)
        full_data = await state.get_data()
        full_data["telegram_id"] = message.from_user.id if isinstance(message, types.Message) else call.from_user.id  # для обоих типов
        save_user_data(full_data)
        try:
            from ..handlers.common import _load_user_codes, _save_user_codes
            mapping = _load_user_codes()
            mapping[str(full_data["telegram_id"])] = code
            _save_user_codes(mapping)
        except Exception:
            pass

        # remove previous inline keyboards
        await delete_last_bot_message(message.chat.id, state, bot)
        # delete user whatsapp message
        await message.delete()
        await message.bot.send_photo(
            message.chat.id,
            photo=open("assets/success.jpg", "rb"),
            caption=T_REG_COMPLETE.format(
                name=data.get("name"),
                surname=data.get("surname"),
                phone_raw=data.get("phone_raw"),
                country=data.get("country"),
                phone=mobile_phone,
                whatsapp=wp_number,
                city=data.get("city", "-"),
                code=code,
            ),
            parse_mode="HTML", reply_markup=KB_REMOVE,
        )
        await state.finish()

    # --- Игнорируем лишние сообщения на шагах city и country
    @dp.message_handler(state=Registration.city, content_types=types.ContentTypes.ANY)
    async def _ignore_city(message: types.Message):
        try:
            await message.delete()
        except Exception:
            pass

    @dp.message_handler(state=Registration.country, content_types=types.ContentTypes.ANY)
    async def _ignore_country(message: types.Message):
        try:
            await message.delete()
        except Exception:
            pass

    # --- WHATSAPP handler
    @dp.message_handler(state=Registration.whatsapp)
    async def process_whatsapp(message: types.Message, state: FSMContext):
        data = await state.get_data()
        country_info = COUNTRIES[data["country"]]
        if message.text.lower() == "да":
            wp_number = country_info["code"] + data["phone_raw"]
        elif not message.text.isdigit() or len(message.text) != country_info["digits"]:
            # Удаляем неверный ввод пользователя и предыдущее сообщение бота
            await message.delete()
            await delete_last_bot_message(message.chat.id, state, bot)

            err_text = T_WHATSAPP_FORMAT_ERR.format(need=country_info["digits"])
            await ask_question(message.chat.id, err_text, create_nav_inline_kb("country"), state, bot)
            return
        else:
            wp_number = country_info["code"] + message.text
        # duplicate check
        if os.path.exists(EXCEL_FILE_PATH):
            df = pd.read_excel(EXCEL_FILE_PATH, engine="openpyxl")
            existing_wp = df.get("WhatsApp", pd.Series(dtype=str)).astype(str).str.lstrip("'").values
            if not df.empty and wp_number in existing_wp:
                # Удаляем неверный ввод пользователя и предыдущее сообщение бота
                await message.delete()
                await delete_last_bot_message(message.chat.id, state, bot)
                await ask_question(message.chat.id, T_WHATSAPP_EXISTS, create_nav_inline_kb("country"), state, bot)
                return
        # Save registration (унифицировано)
        code = generate_unique_code()
        mobile_phone = data["phone_raw"]
        await state.update_data(code=code, phone=mobile_phone, whatsapp=wp_number)
        full_data = await state.get_data()
        full_data["telegram_id"] = message.from_user.id if isinstance(message, types.Message) else call.from_user.id  # для обоих типов
        save_user_data(full_data)
        try:
            from ..handlers.common import _load_user_codes, _save_user_codes
            mapping = _load_user_codes()
            mapping[str(full_data["telegram_id"])] = code
            _save_user_codes(mapping)
        except Exception:
            pass

        # remove previous inline keyboards
        await delete_last_bot_message(message.chat.id, state, bot)
        # delete user whatsapp message
        await message.delete()
        await message.bot.send_photo(
            message.chat.id,
            photo=open("assets/success.jpg", "rb"),
            caption=T_REG_COMPLETE.format(
                name=data.get("name"),
                surname=data.get("surname"),
                phone_raw=data.get("phone_raw"),
                country=data.get("country"),
                phone=mobile_phone,
                whatsapp=wp_number,
                city=data.get("city", "-"),
                code=code,
            ),
            parse_mode="HTML", reply_markup=KB_REMOVE,
        )
        await state.finish()

    # --- Inline: cancel registration
    @dp.callback_query_handler(lambda c: c.data == "reg_cancel", state=Registration.all_states)
    async def cancel_callback(cb: types.CallbackQuery, state: FSMContext):
        await state.finish()
        await cb.answer("Отменено", show_alert=False)
        await cb.message.answer(T_REG_CANCELLED, parse_mode="HTML", reply_markup=KB_REMOVE)

    # --- Inline: back navigation
    @dp.callback_query_handler(lambda c: c.data.startswith("reg_back_to_"), state=Registration.all_states)
    async def back_callback(cb: types.CallbackQuery, state: FSMContext):
        target = cb.data.split("_")[-1]
        mapping = {
            "city": ask_for_city,
            "name": ask_for_name,
            "surname": ask_for_surname,
            "phone": ask_for_phone,
            "country": ask_for_country,
        }
        func = mapping.get(target)
        if func:
            await func(cb.from_user.id, state, cb.bot)
        await cb.answer()

    # --- Inline: back navigation
    @dp.callback_query_handler(lambda c: c.data.startswith("reg_back_to_"), state=Registration.all_states)
    async def back_callback(cb: types.CallbackQuery, state: FSMContext):
        target = cb.data.split("_")[-1]
        mapping = {
            "city": ask_for_city,
            "name": ask_for_name,
            "surname": ask_for_surname,
            "phone": ask_for_phone,
            "country": ask_for_country,
        }
        func = mapping.get(target)
        if func:
            await func(cb.from_user.id, state, cb.bot)
        await cb.answer()

    # --- Code Check Handlers ---
    
    @dp.callback_query_handler(text=["code_retry", "code_register"], state=Registration.check_code)
    async def code_retry_or_reg_callback(call: types.CallbackQuery, state: FSMContext):
        await call.message.delete()
        if call.data == "code_retry":
            msg = await call.message.answer("Пожалуйста, введите ваш 6-символьный код.", parse_mode="HTML")
            await state.update_data(last_bot_message_id=msg.message_id)
        else:
            await ask_for_city(call.message.chat.id, state, bot)

    @dp.message_handler(state=Registration.check_code)
    async def process_entered_code(message: types.Message, state: FSMContext):
        entered_code = message.text.strip()
        await message.delete()
        await delete_last_bot_message(message.chat.id, state, bot)

        if not os.path.exists(EXCEL_FILE_PATH):
            msg = await message.answer(T_CODE_NOT_FOUND, parse_mode="HTML", reply_markup=create_retry_register_inline_kb())
            await state.update_data(last_bot_message_id=msg.message_id)
            return

        try:
            df = pd.read_excel(EXCEL_FILE_PATH, engine="openpyxl")
            row = df[df["Уникальный код"].astype(str) == entered_code]
            if row.empty:
                msg = await message.answer(T_CODE_NOT_FOUND, parse_mode="HTML", reply_markup=create_retry_register_inline_kb())
                await state.update_data(last_bot_message_id=msg.message_id)
                return
        except Exception:
             msg = await message.answer(T_CODE_NOT_FOUND, parse_mode="HTML", reply_markup=create_retry_register_inline_kb())
             await state.update_data(last_bot_message_id=msg.message_id)
             return

        user_id = message.from_user.id
        save_user_code(user_id, "", entered_code)
        # Обновим user_codes.json, чтобы /info и /myproducts работали для этого пользователя
        try:
            from ..handlers.common import _load_user_codes, _save_user_codes
            codes = _load_user_codes()
            codes[str(user_id)] = entered_code
            _save_user_codes(codes)
        except Exception:
            pass

        photo_path = os.path.join("assets", "success.jpg")
        if os.path.exists(photo_path):
            with open(photo_path, "rb") as ph:
                await bot.send_photo(message.chat.id, ph, caption=T_LOGIN_SUCCESS, parse_mode="HTML", reply_markup=KB_REMOVE)
        else:
            await message.answer(T_LOGIN_SUCCESS, parse_mode="HTML", reply_markup=KB_REMOVE)

        await state.finish()

    # --- Inline: cancel registration
    @dp.callback_query_handler(lambda c: c.data == "reg_cancel", state=Registration.all_states)
    async def cancel_callback(cb: types.CallbackQuery, state: FSMContext):
        await state.finish()
        await cb.answer("Отменено", show_alert=False)
        await cb.message.answer(T_REG_CANCELLED, parse_mode="HTML", reply_markup=KB_REMOVE)

    # --- Inline: back navigation
    @dp.callback_query_handler(lambda c: c.data.startswith("reg_back_to_"), state=Registration.all_states)
    async def back_callback(cb: types.CallbackQuery, state: FSMContext):
        target = cb.data.split("_")[-1]
        mapping = {
            "city": ask_for_city,
            "name": ask_for_name,
            "surname": ask_for_surname,
            "phone": ask_for_phone,
            "country": ask_for_country,
        }
        func = mapping.get(target)
        if func:
            await func(cb.from_user.id, state, cb.bot)
        await cb.answer()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """Keep only letters, hyphen, space; collapse multiple spaces."""
    allowed = string.ascii_letters + string.ascii_uppercase + string.ascii_lowercase + "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя- "
    cleaned = "".join(ch for ch in text if ch in allowed)
    return " ".join(cleaned.split())

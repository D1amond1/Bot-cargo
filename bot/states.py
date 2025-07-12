"""Finite-state machine states for user registration flow."""
from aiogram.dispatcher.filters.state import State, StatesGroup

class Registration(StatesGroup):
    city = State()
    name = State()
    surname = State()
    phone = State()
    country = State()
    whatsapp = State()
    check_code = State()

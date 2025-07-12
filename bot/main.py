"""Entry point: sets up Bot/Dispatcher, registers handlers and starts polling."""
import logging
import os

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from .config import BOT_TOKEN
from .handlers.common import register_common_handlers
from .handlers.registration import register_registration_handlers


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    if BOT_TOKEN == "YOUR_TOKEN" or not BOT_TOKEN:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN env var or edit bot/config.py with your token.")

    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(bot, storage=MemoryStorage())

    # Ensure Excel directory exists
    os.makedirs("data", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Register all handlers
    register_common_handlers(dp, bot)
    register_registration_handlers(dp, bot)

    logger.info("Bot is starting…")
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()

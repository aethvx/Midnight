import logging

from aiogram import Bot, Dispatcher

from phone_bot.config import load_config
from phone_bot.database import Database
from phone_bot.handlers import build_router


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config = load_config()
    database = Database(config.database_path)
    await database.connect()

    bot = Bot(token=config.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router(config, database))

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        await database.close()
        await bot.session.close()

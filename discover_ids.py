import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from dotenv import load_dotenv


async def main() -> None:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or "replace_with" in token:
        raise ValueError("Сначала укажи BOT_TOKEN в файле .env")

    bot = Bot(token)
    dispatcher = Dispatcher()

    @dispatcher.message()
    async def show_ids(message: Message) -> None:
        print("\nПолучено сообщение:")
        print(f"GROUP_ID={message.chat.id}")
        print(f"TOPIC_ID={message.message_thread_id or 0}")
        print(f"REQUESTER_ID={message.from_user.id if message.from_user else 0}")
        print("Остановить поиск: Ctrl+C\n")

    try:
        print("Отправь любое сообщение от нужного человека в нужной теме.")
        print("Остановить поиск: Ctrl+C")
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient, events

from phone_bot.userbot import message_topic_id


async def main() -> None:
    load_dotenv()
    raw_api_id = os.getenv("API_ID", "").strip()
    api_hash = os.getenv("API_HASH", "").strip()
    if not raw_api_id or not api_hash or "replace_with" in api_hash:
        raise ValueError("Сначала укажи новые API_ID и API_HASH в файле .env")

    session_path = Path(os.getenv("SESSION_PATH", "data/user"))
    session_path.parent.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(session_path), int(raw_api_id), api_hash)

    @client.on(events.NewMessage())
    async def show_ids(event: events.NewMessage.Event) -> None:
        print("\nПолучено сообщение:")
        print(f"GROUP_ID={event.chat_id}")
        print(f"TOPIC_ID={message_topic_id(event.message) or 0}")
        print(f"REQUESTER_ID={event.sender_id}")
        print("Остановить поиск: Ctrl+C\n")

    await client.start()
    print("Отправь сообщение от нужного человека в нужной теме.")
    print("Остановить поиск: Ctrl+C")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())

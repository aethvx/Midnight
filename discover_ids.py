import asyncio
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv, set_key
from telethon import TelegramClient, functions, utils


def choose(items: list[Any], prompt: str) -> Any:
    while True:
        raw_choice = input(prompt).strip()
        try:
            return items[int(raw_choice) - 1]
        except (ValueError, IndexError):
            print("Введи номер строки из списка.")


async def main() -> None:
    load_dotenv()
    raw_api_id = os.getenv("API_ID", "").strip()
    api_hash = os.getenv("API_HASH", "").strip()
    if not raw_api_id or not api_hash or "replace_with" in api_hash:
        raise ValueError("Сначала укажи новые API_ID и API_HASH в файле .env")

    session_path = Path(os.getenv("SESSION_PATH", "data/user"))
    session_path.parent.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(session_path), int(raw_api_id), api_hash)
    await client.start()

    print("\nГруппы твоего аккаунта:")
    groups = [dialog async for dialog in client.iter_dialogs() if dialog.is_group]
    groups.sort(key=lambda dialog: dialog.name.casefold())
    for index, dialog in enumerate(groups, start=1):
        print(f"{index}. {dialog.name} [{dialog.id}]")
    selected_group = choose(groups, "\nНомер нужной группы: ")

    result = await client(
        functions.channels.GetForumTopicsRequest(
            channel=selected_group.entity,
            offset_date=None,
            offset_id=0,
            offset_topic=0,
            limit=100,
            q=None,
        )
    )
    topics = result.topics
    if not topics:
        raise RuntimeError("В выбранной группе не найдены темы")

    print(f"\nТемы группы «{selected_group.name}»:")
    for index, topic in enumerate(topics, start=1):
        state = "закрыта" if topic.closed else "открыта"
        print(f"{index}. {topic.title} [{topic.id}, {state}]")
    selected_topic = choose(topics, "\nНомер нужной темы: ")

    print("\nЧитаю последние сообщения темы — ничего отправляться не будет...")
    authors: dict[int, tuple[Any, str]] = {}
    async for message in client.iter_messages(
        selected_group.entity,
        limit=500,
        reply_to=selected_topic.id,
    ):
        if message.sender_id is None or message.sender_id in authors:
            continue
        sender = await message.get_sender()
        name = utils.get_display_name(sender) or "Без имени"
        username = getattr(sender, "username", None)
        label = f"{name} (@{username})" if username else name
        authors[message.sender_id] = (sender, label)

    if not authors:
        raise RuntimeError("В последних 500 сообщениях темы не найдены авторы")

    author_items = list(authors.items())
    print("\nАвторы последних сообщений:")
    for index, (sender_id, (_, label)) in enumerate(author_items, start=1):
        print(f"{index}. {label} [{sender_id}]")
    selected_author = choose(author_items, "\nНомер нужного человека: ")
    requester_id = selected_author[0]

    print("\nГотовые значения:")
    print(f"GROUP_ID={selected_group.id}")
    print(f"TOPIC_ID={selected_topic.id}")
    print(f"REQUESTER_ID={requester_id}")

    save = input("\nЗаписать их в .env автоматически? [Y/n]: ").strip().casefold()
    if save not in {"n", "no", "нет"}:
        set_key(".env", "GROUP_ID", str(selected_group.id), quote_mode="never")
        set_key(".env", "TOPIC_ID", str(selected_topic.id), quote_mode="never")
        set_key(".env", "REQUESTER_ID", str(requester_id), quote_mode="never")
        print("Значения сохранены в .env.")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

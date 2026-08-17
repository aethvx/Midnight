import logging

from telethon import TelegramClient, events

from phone_bot.config import load_config
from phone_bot.database import Database
from phone_bot.userbot import is_matching_request


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config = load_config()
    database = Database(config.database_path)
    database.initialize()
    config.session_path.parent.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(str(config.session_path), config.api_id, config.api_hash)

    @client.on(events.NewMessage())
    async def handle_request(event: events.NewMessage.Event) -> None:
        if not is_matching_request(event, config):
            return

        issued = database.issue_next(
            requester_id=event.sender_id,
            chat_id=event.chat_id,
            topic_id=config.topic_id,
        )
        text = issued.phone if issued else "Номеров нет"
        try:
            await client.send_message(event.chat_id, text, reply_to=event.message.id)
        except Exception:
            if issued is not None:
                database.return_to_front(issued)
            raise

    await client.start()
    me = await client.get_me()
    logging.info("Userbot started as %s (%s)", me.username or me.first_name, me.id)
    await client.run_until_disconnected()

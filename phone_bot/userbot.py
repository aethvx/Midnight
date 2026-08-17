from typing import Any

from phone_bot.config import Config


def message_topic_id(message: Any) -> int | None:
    reply_to = getattr(message, "reply_to", None)
    if reply_to is None:
        return None
    return reply_to.reply_to_top_id or reply_to.reply_to_msg_id


def is_matching_request(event: Any, config: Config) -> bool:
    text = getattr(event, "raw_text", None)
    if not isinstance(text, str) or text.strip().casefold() != "вотс":
        return False
    if event.chat_id != config.group_id:
        return False
    if event.sender_id != config.requester_id:
        return False
    return message_topic_id(event.message) == config.topic_id

from pathlib import Path
from types import SimpleNamespace

from phone_bot.config import Config
from phone_bot.userbot import is_matching_request, message_topic_id


def make_config() -> Config:
    return Config(
        api_id=123,
        api_hash="hash",
        group_id=-100500,
        topic_id=42,
        requester_id=777,
        database_path=Path("phones.db"),
        session_path=Path("user"),
    )


def make_event(
    text: str = "Вотс",
    chat_id: int = -100500,
    sender_id: int = 777,
    topic_id: int = 42,
    outgoing: bool = False,
):
    reply_to = SimpleNamespace(reply_to_top_id=topic_id, reply_to_msg_id=topic_id)
    message = SimpleNamespace(reply_to=reply_to)
    return SimpleNamespace(
        raw_text=text,
        chat_id=chat_id,
        sender_id=sender_id,
        message=message,
        out=outgoing,
    )


def test_topic_id_supports_top_level_and_nested_replies() -> None:
    top_level = SimpleNamespace(
        reply_to=SimpleNamespace(reply_to_top_id=None, reply_to_msg_id=42)
    )
    nested = SimpleNamespace(
        reply_to=SimpleNamespace(reply_to_top_id=42, reply_to_msg_id=99)
    )

    assert message_topic_id(top_level) == 42
    assert message_topic_id(nested) == 42


def test_only_exact_authorized_request_matches() -> None:
    config = make_config()

    assert is_matching_request(make_event(text="  вОтС  "), config)
    assert not is_matching_request(make_event(text="Вотс пожалуйста"), config)
    assert not is_matching_request(make_event(chat_id=-100999), config)
    assert not is_matching_request(make_event(sender_id=888), config)
    assert not is_matching_request(make_event(topic_id=43), config)


def test_own_outgoing_request_matches_when_own_id_is_authorized() -> None:
    config = make_config()

    assert is_matching_request(make_event(sender_id=777, outgoing=True), config)

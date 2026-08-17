from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    group_id: int
    topic_id: int
    requester_id: int
    admin_ids: frozenset[int]
    database_path: Path


def _required_int(name: str) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Не заполнена переменная {name} в файле .env")

    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"Переменная {name} должна быть целым числом") from error


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("Не заполнена переменная BOT_TOKEN в файле .env")

    requester_id = _required_int("REQUESTER_ID")
    raw_admin_ids = os.getenv("ADMIN_IDS", "").strip()
    try:
        admin_ids = (
            frozenset(
                int(value.strip())
                for value in raw_admin_ids.split(",")
                if value.strip()
            )
            if raw_admin_ids
            else frozenset({requester_id})
        )
    except ValueError as error:
        raise ValueError(
            "ADMIN_IDS должен содержать Telegram ID через запятую"
        ) from error

    return Config(
        bot_token=bot_token,
        group_id=_required_int("GROUP_ID"),
        topic_id=_required_int("TOPIC_ID"),
        requester_id=requester_id,
        admin_ids=admin_ids,
        database_path=Path(os.getenv("DATABASE_PATH", "data/phones.db")),
    )

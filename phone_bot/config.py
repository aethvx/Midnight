from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    group_id: int
    topic_id: int
    requester_id: int
    database_path: Path
    session_path: Path


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

    api_hash = os.getenv("API_HASH", "").strip()
    if not api_hash or "replace_with" in api_hash:
        raise ValueError("Не заполнена переменная API_HASH в файле .env")

    return Config(
        api_id=_required_int("API_ID"),
        api_hash=api_hash,
        group_id=_required_int("GROUP_ID"),
        topic_id=_required_int("TOPIC_ID"),
        requester_id=_required_int("REQUESTER_ID"),
        database_path=Path(os.getenv("DATABASE_PATH", "data/phones.db")),
        session_path=Path(os.getenv("SESSION_PATH", "data/user")),
    )

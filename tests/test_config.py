from pathlib import Path

import pytest

from phone_bot.config import load_config


def test_load_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("GROUP_ID", "-100123")
    monkeypatch.setenv("TOPIC_ID", "45")
    monkeypatch.setenv("REQUESTER_ID", "777")
    monkeypatch.setenv("ADMIN_IDS", "777, 888")
    monkeypatch.setenv("DATABASE_PATH", "custom.db")

    config = load_config()

    assert config.bot_token == "token"
    assert config.group_id == -100123
    assert config.topic_id == 45
    assert config.requester_id == 777
    assert config.admin_ids == frozenset({777, 888})
    assert config.database_path == Path("custom.db")


def test_requester_is_default_admin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("GROUP_ID", "-100123")
    monkeypatch.setenv("TOPIC_ID", "45")
    monkeypatch.setenv("REQUESTER_ID", "777")
    monkeypatch.delenv("ADMIN_IDS", raising=False)

    assert load_config().admin_ids == frozenset({777})

from pathlib import Path

import pytest

from phone_bot.config import PROJECT_DIR, load_config


def test_load_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("API_ID", "12345")
    monkeypatch.setenv("API_HASH", "secret_hash")
    monkeypatch.setenv("GROUP_ID", "-100123")
    monkeypatch.setenv("TOPIC_ID", "45")
    monkeypatch.setenv("REQUESTER_ID", "777")
    monkeypatch.setenv("DATABASE_PATH", "custom.db")
    monkeypatch.setenv("SESSION_PATH", "custom_session")

    config = load_config()

    assert config.api_id == 12345
    assert config.api_hash == "secret_hash"
    assert config.group_id == -100123
    assert config.topic_id == 45
    assert config.requester_id == 777
    assert config.database_path == PROJECT_DIR / "custom.db"
    assert config.session_path == PROJECT_DIR / "custom_session"


def test_api_hash_is_required(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("API_HASH", "replace_with_new_api_hash")

    with pytest.raises(ValueError, match="API_HASH"):
        load_config()

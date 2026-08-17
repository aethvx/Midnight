from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from phone_bot.database import Database, REGULAR, REPLACEMENT, is_valid_phone


@pytest.fixture
def database(tmp_path: Path) -> Database:
    db = Database(tmp_path / "test.db")
    db.initialize()
    return db


def test_phone_validation() -> None:
    assert is_valid_phone("+7 999 123-45-67")
    assert is_valid_phone("79991234567")
    assert not is_valid_phone("123")
    assert not is_valid_phone("+7 test 1234567")


def test_add_phones_reports_duplicates_and_invalid(database: Database) -> None:
    first = database.add_phones(
        ["+7 999 111-22-33", "79992223344", "bad", "79992223344"],
        REGULAR,
    )
    second = database.add_phones(["7 (999) 111-22-33"], REPLACEMENT)

    assert first.added == 2
    assert first.duplicates == 1
    assert first.invalid == ("bad",)
    assert second.added == 0
    assert second.duplicates == 1
    assert database.counts() == {REGULAR: 2, REPLACEMENT: 0}


def test_replacement_queue_has_priority(database: Database) -> None:
    database.add_phones(["79990000001"], REGULAR)
    database.add_phones(["79990000002"], REPLACEMENT)

    first = database.issue_next(1, -1001, 10)
    second = database.issue_next(1, -1001, 10)
    empty = database.issue_next(1, -1001, 10)

    assert first is not None and first.phone == "79990000002"
    assert second is not None and second.phone == "79990000001"
    assert empty is None
    assert database.total_issued() == 2


def test_failed_send_returns_number_to_front(database: Database) -> None:
    database.add_phones(["79990000001", "79990000002"], REGULAR)

    issued = database.issue_next(1, -1001, 10)
    assert issued is not None
    database.return_to_front(issued)

    next_phone = database.issue_next(1, -1001, 10)
    assert next_phone is not None and next_phone.phone == "79990000001"
    assert database.total_issued() == 1


def test_concurrent_requests_never_receive_same_number(database: Database) -> None:
    phones = [f"79990000{number:03d}" for number in range(20)]
    database.add_phones(phones, REGULAR)

    with ThreadPoolExecutor(max_workers=8) as executor:
        issued = list(
            executor.map(lambda _: database.issue_next(1, -1001, 10), range(25))
        )
    issued_phones = [item.phone for item in issued if item is not None]

    assert len(issued_phones) == 20
    assert len(set(issued_phones)) == 20
    assert database.counts() == {REGULAR: 0, REPLACEMENT: 0}


def test_move_and_remove_phone(database: Database) -> None:
    database.add_phones(["79990000001"], REGULAR)
    item = database.list_queue(REGULAR)[0]

    database.move_phone(item.id, REPLACEMENT)
    assert database.list_queue(REGULAR) == []
    assert database.list_queue(REPLACEMENT)[0].phone == item.phone

    database.remove_phone(item.id)
    assert database.list_queue(REPLACEMENT) == []

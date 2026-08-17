import asyncio
from pathlib import Path

import pytest
import pytest_asyncio

from phone_bot.database import Database, REGULAR, REPLACEMENT, is_valid_phone


@pytest_asyncio.fixture
async def database(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    await db.connect()
    yield db
    await db.close()


def test_phone_validation() -> None:
    assert is_valid_phone("+7 999 123-45-67")
    assert is_valid_phone("79991234567")
    assert not is_valid_phone("123")
    assert not is_valid_phone("+7 test 1234567")


@pytest.mark.asyncio
async def test_add_phones_reports_duplicates_and_invalid(database: Database) -> None:
    first = await database.add_phones(
        ["+7 999 111-22-33", "79992223344", "bad", "79992223344"],
        REGULAR,
    )
    second = await database.add_phones(["7 (999) 111-22-33"], REPLACEMENT)

    assert first.added == 2
    assert first.duplicates == 0
    assert first.invalid == ("bad",)
    assert second.added == 0
    assert second.duplicates == 1
    assert await database.counts() == {REGULAR: 2, REPLACEMENT: 0}


@pytest.mark.asyncio
async def test_replacement_queue_has_priority(database: Database) -> None:
    await database.add_phones(["79990000001"], REGULAR)
    await database.add_phones(["79990000002"], REPLACEMENT)

    first = await database.issue_next(1, -1001, 10)
    second = await database.issue_next(1, -1001, 10)
    empty = await database.issue_next(1, -1001, 10)

    assert first is not None and first.phone == "79990000002"
    assert second is not None and second.phone == "79990000001"
    assert empty is None
    assert await database.total_issued() == 2


@pytest.mark.asyncio
async def test_concurrent_requests_never_receive_same_number(
    database: Database,
) -> None:
    phones = [f"79990000{number:03d}" for number in range(20)]
    await database.add_phones(phones, REGULAR)

    issued = await asyncio.gather(
        *(database.issue_next(1, -1001, 10) for _ in range(25))
    )
    issued_phones = [item.phone for item in issued if item is not None]

    assert len(issued_phones) == 20
    assert len(set(issued_phones)) == 20
    assert await database.counts() == {REGULAR: 0, REPLACEMENT: 0}

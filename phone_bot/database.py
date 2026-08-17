from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import asyncio
import re

import aiosqlite


REGULAR = "regular"
REPLACEMENT = "replacement"
QUEUE_TYPES = {REGULAR, REPLACEMENT}


@dataclass(frozen=True)
class IssuedPhone:
    phone: str
    queue_type: str


@dataclass(frozen=True)
class AddResult:
    added: int
    duplicates: int
    invalid: tuple[str, ...]


def is_valid_phone(phone: str) -> bool:
    if not 7 <= sum(character.isdigit() for character in phone) <= 15:
        return False
    return re.fullmatch(r"\+?[\d\s()\-]+", phone) is not None


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._connection: aiosqlite.Connection | None = None
        self._transaction_lock = asyncio.Lock()

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA journal_mode = WAL")
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS phone_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                canonical_phone TEXT NOT NULL UNIQUE,
                queue_type TEXT NOT NULL CHECK(queue_type IN ('regular', 'replacement')),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS issuance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                queue_type TEXT NOT NULL CHECK(queue_type IN ('regular', 'replacement')),
                requester_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                issued_at TEXT NOT NULL
            );
            """
        )
        await self._connection.commit()

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("База данных не подключена")
        return self._connection

    async def add_phones(self, lines: list[str], queue_type: str) -> AddResult:
        if queue_type not in QUEUE_TYPES:
            raise ValueError("Неизвестный тип очереди")

        invalid: list[str] = []
        valid: list[str] = []
        seen: set[str] = set()
        for line in lines:
            phone = line.strip()
            if not phone:
                continue
            if not is_valid_phone(phone):
                invalid.append(phone)
                continue
            if phone not in seen:
                seen.add(phone)
                valid.append(phone)

        added = 0
        now = datetime.now(UTC).isoformat()
        async with self._transaction_lock:
            for phone in valid:
                cursor = await self.connection.execute(
                    """
                    INSERT OR IGNORE INTO phone_queue (
                        phone, canonical_phone, queue_type, created_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        phone,
                        "".join(
                            character for character in phone if character.isdigit()
                        ),
                        queue_type,
                        now,
                    ),
                )
                added += cursor.rowcount
            await self.connection.commit()

        return AddResult(
            added=added,
            duplicates=len(valid) - added,
            invalid=tuple(invalid),
        )

    async def issue_next(
        self,
        requester_id: int,
        chat_id: int,
        topic_id: int,
    ) -> IssuedPhone | None:
        async with self._transaction_lock:
            await self.connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = await self.connection.execute(
                    """
                    SELECT id, phone, queue_type
                    FROM phone_queue
                    ORDER BY CASE queue_type WHEN 'replacement' THEN 0 ELSE 1 END, id
                    LIMIT 1
                    """
                )
                row = await cursor.fetchone()
                if row is None:
                    await self.connection.commit()
                    return None

                await self.connection.execute(
                    "DELETE FROM phone_queue WHERE id = ?",
                    (row["id"],),
                )
                await self.connection.execute(
                    """
                    INSERT INTO issuance_log (
                        phone, queue_type, requester_id, chat_id, topic_id, issued_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["phone"],
                        row["queue_type"],
                        requester_id,
                        chat_id,
                        topic_id,
                        datetime.now(UTC).isoformat(),
                    ),
                )
                await self.connection.commit()
                return IssuedPhone(phone=row["phone"], queue_type=row["queue_type"])
            except Exception:
                await self.connection.rollback()
                raise

    async def counts(self) -> dict[str, int]:
        cursor = await self.connection.execute(
            """
            SELECT queue_type, COUNT(*) AS count
            FROM phone_queue
            GROUP BY queue_type
            """
        )
        rows = await cursor.fetchall()
        counts = {REGULAR: 0, REPLACEMENT: 0}
        counts.update({row["queue_type"]: row["count"] for row in rows})
        return counts

    async def total_issued(self) -> int:
        cursor = await self.connection.execute("SELECT COUNT(*) FROM issuance_log")
        row = await cursor.fetchone()
        return int(row[0])

    async def queue_preview(self, queue_type: str, limit: int = 20) -> list[str]:
        if queue_type not in QUEUE_TYPES:
            raise ValueError("Неизвестный тип очереди")
        cursor = await self.connection.execute(
            """
            SELECT phone FROM phone_queue
            WHERE queue_type = ?
            ORDER BY id
            LIMIT ?
            """,
            (queue_type, limit),
        )
        return [row["phone"] for row in await cursor.fetchall()]

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import re
import sqlite3


REGULAR = "regular"
REPLACEMENT = "replacement"
QUEUE_TYPES = {REGULAR, REPLACEMENT}


@dataclass(frozen=True)
class IssuedPhone:
    phone: str
    queue_type: str
    log_id: int


@dataclass(frozen=True)
class QueuePhone:
    id: int
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


def canonical_phone(phone: str) -> str:
    return "".join(character for character in phone if character.isdigit())


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS phone_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT NOT NULL,
                    canonical_phone TEXT NOT NULL UNIQUE,
                    queue_type TEXT NOT NULL
                        CHECK(queue_type IN ('regular', 'replacement')),
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS issuance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT NOT NULL,
                    queue_type TEXT NOT NULL
                        CHECK(queue_type IN ('regular', 'replacement')),
                    requester_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    topic_id INTEGER NOT NULL,
                    issued_at TEXT NOT NULL
                );
                """
            )

    def add_phones(self, lines: list[str], queue_type: str) -> AddResult:
        if queue_type not in QUEUE_TYPES:
            raise ValueError("Неизвестный тип очереди")

        invalid: list[str] = []
        valid: list[str] = []
        seen: set[str] = set()
        duplicates = 0
        for line in lines:
            phone = line.strip()
            if not phone:
                continue
            if not is_valid_phone(phone):
                invalid.append(phone)
                continue
            canonical = canonical_phone(phone)
            if canonical in seen:
                duplicates += 1
                continue
            seen.add(canonical)
            valid.append(phone)

        added = 0
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            for phone in valid:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO phone_queue (
                        phone, canonical_phone, queue_type, created_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (phone, canonical_phone(phone), queue_type, now),
                )
                added += cursor.rowcount

        return AddResult(
            added=added,
            duplicates=duplicates + len(valid) - added,
            invalid=tuple(invalid),
        )

    def issue_next(
        self,
        requester_id: int,
        chat_id: int,
        topic_id: int,
    ) -> IssuedPhone | None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT id, phone, queue_type
                FROM phone_queue
                ORDER BY CASE queue_type WHEN 'replacement' THEN 0 ELSE 1 END, id
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return None

            connection.execute("DELETE FROM phone_queue WHERE id = ?", (row["id"],))
            log_cursor = connection.execute(
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
            return IssuedPhone(
                phone=row["phone"],
                queue_type=row["queue_type"],
                log_id=log_cursor.lastrowid,
            )

    def return_to_front(self, issued: IssuedPhone) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM issuance_log WHERE id = ?", (issued.log_id,)
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO phone_queue (
                    id, phone, canonical_phone, queue_type, created_at
                ) VALUES (
                    COALESCE((SELECT MIN(id) - 1 FROM phone_queue), 1), ?, ?, ?, ?
                )
                """,
                (
                    issued.phone,
                    canonical_phone(issued.phone),
                    issued.queue_type,
                    datetime.now(UTC).isoformat(),
                ),
            )

    def counts(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT queue_type, COUNT(*) AS count
                FROM phone_queue
                GROUP BY queue_type
                """
            ).fetchall()
        counts = {REGULAR: 0, REPLACEMENT: 0}
        counts.update({row["queue_type"]: row["count"] for row in rows})
        return counts

    def total_issued(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM issuance_log").fetchone()
        return int(row[0])

    def list_queue(self, queue_type: str, limit: int = 500) -> list[QueuePhone]:
        if queue_type not in QUEUE_TYPES:
            raise ValueError("Неизвестный тип очереди")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, phone, queue_type
                FROM phone_queue
                WHERE queue_type = ?
                ORDER BY id
                LIMIT ?
                """,
                (queue_type, limit),
            ).fetchall()
        return [QueuePhone(row["id"], row["phone"], row["queue_type"]) for row in rows]

    def remove_phone(self, phone_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM phone_queue WHERE id = ?", (phone_id,))

    def move_phone(self, phone_id: int, queue_type: str) -> None:
        if queue_type not in QUEUE_TYPES:
            raise ValueError("Неизвестный тип очереди")
        with self._connect() as connection:
            connection.execute(
                "UPDATE phone_queue SET queue_type = ? WHERE id = ?",
                (queue_type, phone_id),
            )

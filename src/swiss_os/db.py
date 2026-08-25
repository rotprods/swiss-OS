from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()


def integrity_check(conn: sqlite3.Connection) -> str:
    return str(conn.execute("PRAGMA integrity_check").fetchone()[0])


def foreign_key_violations(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("PRAGMA foreign_key_check"))


def active_hotel_ids(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT hotel_id FROM canonical_hotels WHERE state = 'ACTIVE' ORDER BY hotel_id"
    ).fetchall()
    return {str(r[0]) for r in rows}


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise

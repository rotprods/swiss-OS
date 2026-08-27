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


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def sqlite_logical_differences(
    source_path: str | Path,
    restored_path: str | Path,
) -> list[str]:
    """Return logical differences between two SQLite databases.

    SQLite backup/restore operations are not required to reproduce the same file
    bytes: page layout, freelists and other physical representation details may
    differ while the databases are logically identical. A restore gate therefore
    compares integrity, FK state, schema objects and table contents in both
    directions instead of comparing only file hashes.

    An empty list means the databases are logically equivalent for operational
    restore purposes.
    """

    source = Path(source_path)
    restored = Path(restored_path)
    errors: list[str] = []

    if not source.is_file():
        return [f"source database does not exist: {source}"]
    if not restored.is_file():
        return [f"restored database does not exist: {restored}"]

    conn = sqlite3.connect(str(source))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("ATTACH DATABASE ? AS restored_db", (str(restored),))

        source_integrity = str(conn.execute("PRAGMA main.integrity_check").fetchone()[0])
        restored_integrity = str(
            conn.execute("PRAGMA restored_db.integrity_check").fetchone()[0]
        )
        if source_integrity.lower() != "ok":
            errors.append(f"source integrity_check={source_integrity}")
        if restored_integrity.lower() != "ok":
            errors.append(f"restored integrity_check={restored_integrity}")

        source_fk = list(conn.execute("PRAGMA main.foreign_key_check"))
        restored_fk = list(conn.execute("PRAGMA restored_db.foreign_key_check"))
        if source_fk:
            errors.append(f"source foreign_key_check returned {len(source_fk)} rows")
        if restored_fk:
            errors.append(f"restored foreign_key_check returned {len(restored_fk)} rows")

        schema_query = """
            SELECT type, name, tbl_name, COALESCE(sql, '')
            FROM {db}.sqlite_master
            WHERE name NOT LIKE 'sqlite_%'
              AND NOT (type = 'index' AND sql IS NULL)
            ORDER BY type, name, tbl_name, sql
        """
        source_schema = list(conn.execute(schema_query.format(db="main")))
        restored_schema = list(conn.execute(schema_query.format(db="restored_db")))
        if source_schema != restored_schema:
            errors.append("schema objects differ")

        source_tables = [
            str(row[0])
            for row in conn.execute(
                """
                SELECT name
                FROM main.sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            )
        ]
        restored_tables = [
            str(row[0])
            for row in conn.execute(
                """
                SELECT name
                FROM restored_db.sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            )
        ]
        if source_tables != restored_tables:
            errors.append("table sets differ")
            return errors

        for table in source_tables:
            quoted_table = _quote_identifier(table)
            columns = [
                str(row[1])
                for row in conn.execute(f"PRAGMA main.table_info({quoted_table})")
            ]
            if not columns:
                continue
            column_sql = ", ".join(_quote_identifier(column) for column in columns)

            source_count = int(
                conn.execute(f"SELECT COUNT(*) FROM main.{quoted_table}").fetchone()[0]
            )
            restored_count = int(
                conn.execute(
                    f"SELECT COUNT(*) FROM restored_db.{quoted_table}"
                ).fetchone()[0]
            )
            if source_count != restored_count:
                errors.append(
                    f"table {table} row count differs: {source_count} != {restored_count}"
                )
                continue

            source_minus_restore = conn.execute(
                f"""
                SELECT {column_sql} FROM main.{quoted_table}
                EXCEPT
                SELECT {column_sql} FROM restored_db.{quoted_table}
                LIMIT 1
                """
            ).fetchone()
            restore_minus_source = conn.execute(
                f"""
                SELECT {column_sql} FROM restored_db.{quoted_table}
                EXCEPT
                SELECT {column_sql} FROM main.{quoted_table}
                LIMIT 1
                """
            ).fetchone()
            if source_minus_restore is not None or restore_minus_source is not None:
                errors.append(f"table {table} content differs")

        return errors
    finally:
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise

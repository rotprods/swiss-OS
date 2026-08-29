from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
from typing import Iterable, Mapping, Sequence

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _quote(identifier: str) -> str:
    if not isinstance(identifier, str) or not _IDENTIFIER.fullmatch(identifier):
        raise ValueError(f"invalid SQLite identifier: {identifier!r}")
    return f'"{identifier}"'


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_value(value: object) -> object:
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    if value is None or isinstance(value, (str, int, float)):
        return value
    raise ValueError(f"unsupported SQLite repair value: {type(value).__name__}")


def _sqlite_value(value: object) -> object:
    if isinstance(value, Mapping) and set(value) == {"__bytes_hex__"}:
        raw = value["__bytes_hex__"]
        if not isinstance(raw, str):
            raise ValueError("__bytes_hex__ must be a string")
        return bytes.fromhex(raw)
    if value is None or isinstance(value, (str, int, float)):
        return value
    raise ValueError(f"unsupported repair JSON value: {value!r}")


def _canonical_rows_sha(rows: Iterable[Sequence[object]]) -> str:
    encoded = [
        json.dumps(
            [_json_value(v) for v in row],
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        for row in rows
    ]
    encoded.sort()
    return hashlib.sha256(("\n".join(encoded) + "\n").encode("utf-8")).hexdigest()


def _table_names(conn: sqlite3.Connection) -> tuple[str, ...]:
    return tuple(
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    )


def _columns(conn: sqlite3.Connection, table: str) -> tuple[str, ...]:
    quoted = _quote(table)
    cols = tuple(row[1] for row in conn.execute(f"PRAGMA table_info({quoted})"))
    if not cols:
        raise ValueError(f"table does not exist or has no columns: {table}")
    for col in cols:
        _quote(col)
    return cols


def _rows(
    conn: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
) -> list[tuple[object, ...]]:
    query = ", ".join(_quote(col) for col in columns)
    return [tuple(row) for row in conn.execute(f"SELECT {query} FROM {_quote(table)}")]


def _schema_signature(conn: sqlite3.Connection) -> str:
    rows = conn.execute(
        "SELECT type, name, tbl_name, COALESCE(sql, '') FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    return hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class RepairReceipt:
    repair_id: str
    state: str
    applied_removed_rows: int
    applied_added_rows: int
    integrity_check: str
    foreign_key_violations: int
    post_file_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "repair_id": self.repair_id,
            "repair_state": self.state,
            "applied_removed_rows": self.applied_removed_rows,
            "applied_added_rows": self.applied_added_rows,
            "integrity_check": self.integrity_check,
            "foreign_key_violations": self.foreign_key_violations,
            "post_file_sha256": self.post_file_sha256,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }


def build_repair_spec(
    source_db: str | Path,
    target_db: str | Path,
    *,
    repair_id: str,
) -> dict[str, object]:
    """Build a deterministic exact-row repair spec from two SQLite states."""

    if not isinstance(repair_id, str) or not repair_id.strip():
        raise ValueError("repair_id is required")
    source_path = Path(source_db)
    target_path = Path(target_db)
    with sqlite3.connect(source_path) as source, sqlite3.connect(target_path) as target:
        source.execute("PRAGMA foreign_keys = ON")
        target.execute("PRAGMA foreign_keys = ON")
        if _schema_signature(source) != _schema_signature(target):
            raise ValueError("source and target SQLite schemas differ")
        operations: list[dict[str, object]] = []
        expected_counts: dict[str, int] = {}
        expected_hashes: dict[str, str] = {}
        for table in _table_names(source):
            columns = _columns(source, table)
            source_rows = _rows(source, table, columns)
            target_rows = _rows(target, table, columns)
            source_counter = Counter(source_rows)
            target_counter = Counter(target_rows)
            removed: list[list[object]] = []
            added: list[list[object]] = []
            for row, count in sorted(
                (source_counter - target_counter).items(), key=lambda item: repr(item[0])
            ):
                removed.extend([[_json_value(v) for v in row] for _ in range(count)])
            for row, count in sorted(
                (target_counter - source_counter).items(), key=lambda item: repr(item[0])
            ):
                added.extend([[_json_value(v) for v in row] for _ in range(count)])
            if removed or added:
                operations.append(
                    {
                        "table": table,
                        "columns": list(columns),
                        "remove_rows": removed,
                        "add_rows": added,
                    }
                )
                expected_counts[table] = len(target_rows)
                expected_hashes[table] = _canonical_rows_sha(target_rows)
        return {
            "schema_version": "SQLITE_REPAIR_SPEC_V1",
            "repair_id": repair_id.strip(),
            "source_file_sha256": file_sha256(source_path),
            "source_schema_sha256": _schema_signature(source),
            "operations": operations,
            "expected_post_table_counts": expected_counts,
            "expected_post_table_rows_sha256": expected_hashes,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }


def _load_spec(
    spec: Mapping[str, object],
) -> tuple[
    str,
    str,
    str,
    tuple[Mapping[str, object], ...],
    Mapping[str, object],
    Mapping[str, object],
]:
    if spec.get("schema_version") != "SQLITE_REPAIR_SPEC_V1":
        raise ValueError("unsupported repair spec schema")
    repair_id = spec.get("repair_id")
    source_sha = spec.get("source_file_sha256")
    schema_sha = spec.get("source_schema_sha256")
    operations = spec.get("operations")
    counts = spec.get("expected_post_table_counts")
    hashes = spec.get("expected_post_table_rows_sha256")
    if not isinstance(repair_id, str) or not repair_id.strip():
        raise ValueError("repair_id is required")
    if not isinstance(source_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", source_sha):
        raise ValueError("source_file_sha256 is invalid")
    if not isinstance(schema_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", schema_sha):
        raise ValueError("source_schema_sha256 is invalid")
    if not isinstance(operations, list) or not all(
        isinstance(x, Mapping) for x in operations
    ):
        raise ValueError("operations must be an array of objects")
    if not isinstance(counts, Mapping) or not isinstance(hashes, Mapping):
        raise ValueError("postcondition maps are required")
    for field in ("authority_advanced", "outbound_opened"):
        if spec.get(field) is not False:
            raise ValueError(f"{field} must be false")
    if spec.get("h_id_allocations") != 0 or type(spec.get("h_id_allocations")) is not int:
        raise ValueError("h_id_allocations must be integer zero")
    if spec.get("send_allowed") != 0 or type(spec.get("send_allowed")) is not int:
        raise ValueError("send_allowed must be integer zero")
    return (
        repair_id.strip(),
        source_sha,
        schema_sha,
        tuple(operations),
        counts,
        hashes,
    )


def _row_exists(
    conn: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
    row: Sequence[object],
) -> int:
    if len(columns) != len(row):
        raise ValueError(f"row length mismatch for {table}")
    where = " AND ".join(f"{_quote(col)} IS ?" for col in columns)
    return int(
        conn.execute(
            f"SELECT COUNT(*) FROM {_quote(table)} WHERE {where}", tuple(row)
        ).fetchone()[0]
    )


def _postconditions_hold(
    conn: sqlite3.Connection,
    operations: Sequence[Mapping[str, object]],
    counts: Mapping[str, object],
    hashes: Mapping[str, object],
) -> bool:
    for op in operations:
        table = op.get("table")
        columns = op.get("columns")
        if not isinstance(table, str) or not isinstance(columns, list) or not all(
            isinstance(c, str) for c in columns
        ):
            raise ValueError("invalid operation table/columns")
        actual_columns = _columns(conn, table)
        if tuple(columns) != actual_columns:
            raise ValueError(f"column contract mismatch for {table}")
        expected_count = counts.get(table)
        expected_hash = hashes.get(table)
        if type(expected_count) is not int or not isinstance(expected_hash, str):
            raise ValueError(f"invalid postconditions for {table}")
        rows = _rows(conn, table, actual_columns)
        if len(rows) != expected_count or _canonical_rows_sha(rows) != expected_hash:
            return False
    return True


def apply_repair_spec(
    db_path: str | Path,
    spec: Mapping[str, object],
    *,
    backup_path: str | Path | None = None,
) -> RepairReceipt:
    """Apply an exact-row repair transaction or return an idempotent no-op."""

    path = Path(db_path)
    repair_id, source_sha, schema_sha, operations, counts, hashes = _load_spec(spec)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        if _schema_signature(conn) != schema_sha:
            raise ValueError("SQLite schema signature mismatch")
        if _postconditions_hold(conn, operations, counts, hashes):
            integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
            fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
            if integrity.lower() != "ok" or fk:
                raise ValueError("post-state exists but SQLite integrity/FK checks fail")
            return RepairReceipt(
                repair_id,
                "NOOP_ALREADY_APPLIED",
                0,
                0,
                integrity,
                fk,
                file_sha256(path),
            )

    if file_sha256(path) != source_sha:
        raise ValueError(
            "database is neither the exact source parent nor the verified post-state"
        )
    if backup_path is not None:
        backup = Path(backup_path)
        if backup.exists():
            raise ValueError("backup_path already exists")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)

    removed_count = 0
    added_count = 0
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            conn.execute("BEGIN IMMEDIATE")
            for op in operations:
                table = op.get("table")
                columns = op.get("columns")
                remove_rows = op.get("remove_rows")
                add_rows = op.get("add_rows")
                if (
                    not isinstance(table, str)
                    or not isinstance(columns, list)
                    or not all(isinstance(c, str) for c in columns)
                    or not isinstance(remove_rows, list)
                    or not isinstance(add_rows, list)
                ):
                    raise ValueError("invalid repair operation")
                actual_columns = _columns(conn, table)
                if tuple(columns) != actual_columns:
                    raise ValueError(f"column contract mismatch for {table}")
                for raw in remove_rows:
                    if not isinstance(raw, list):
                        raise ValueError("remove_rows must contain arrays")
                    row = tuple(_sqlite_value(v) for v in raw)
                    if _row_exists(conn, table, columns, row) != 1:
                        raise ValueError(
                            f"expected exact remove row not found exactly once in {table}"
                        )
                    where = " AND ".join(f"{_quote(col)} IS ?" for col in columns)
                    cursor = conn.execute(
                        f"DELETE FROM {_quote(table)} WHERE {where}", row
                    )
                    if cursor.rowcount != 1:
                        raise ValueError(f"unexpected delete cardinality in {table}")
                    removed_count += 1
                if add_rows:
                    col_sql = ", ".join(_quote(c) for c in columns)
                    marks = ", ".join("?" for _ in columns)
                    for raw in add_rows:
                        if not isinstance(raw, list):
                            raise ValueError("add_rows must contain arrays")
                        row = tuple(_sqlite_value(v) for v in raw)
                        if len(row) != len(columns):
                            raise ValueError(f"add row length mismatch for {table}")
                        conn.execute(
                            f"INSERT INTO {_quote(table)} ({col_sql}) VALUES ({marks})",
                            row,
                        )
                        added_count += 1
            if not _postconditions_hold(conn, operations, counts, hashes):
                raise ValueError("repair postconditions failed")
            integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
            fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
            if integrity.lower() != "ok" or fk:
                raise ValueError("repair integrity/FK checks failed")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return RepairReceipt(
        repair_id,
        "APPLIED_CANARY_NON_AUTHORITY",
        removed_count,
        added_count,
        integrity,
        fk,
        file_sha256(path),
    )

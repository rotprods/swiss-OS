from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sqlite3
from typing import Iterable, Mapping, Sequence

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _quote(value: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"invalid SQLite identifier: {value!r}")
    return f'"{value}"'


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_value(value: object) -> object:
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    if value is None or type(value) in {str, int}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite SQLite floats are unsupported")
        return value
    raise ValueError(f"unsupported SQLite repair value: {type(value).__name__}")


def _sqlite_value(value: object) -> object:
    if isinstance(value, Mapping) and set(value) == {"__bytes_hex__"}:
        raw = value["__bytes_hex__"]
        if not isinstance(raw, str) or len(raw) % 2:
            raise ValueError("__bytes_hex__ must be an even-length hex string")
        try:
            return bytes.fromhex(raw)
        except ValueError as exc:
            raise ValueError("__bytes_hex__ contains invalid hexadecimal") from exc
    if value is None or type(value) in {str, int}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite repair floats are unsupported")
        return value
    raise ValueError(f"unsupported repair JSON value: {value!r}")


def _rows_sha(rows: Iterable[Sequence[object]]) -> str:
    encoded = [
        json.dumps(
            [_json_value(value) for value in row],
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
        for row in rows
    ]
    encoded.sort()
    return hashlib.sha256(("\n".join(encoded) + "\n").encode("utf-8")).hexdigest()


def _tables(conn: sqlite3.Connection) -> tuple[str, ...]:
    return tuple(
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    )


def _columns(conn: sqlite3.Connection, table: str) -> tuple[str, ...]:
    columns = tuple(row[1] for row in conn.execute(f"PRAGMA table_info({_quote(table)})"))
    if not columns:
        raise ValueError(f"table does not exist or has no writable columns: {table}")
    for column in columns:
        _quote(column)
    return columns


def _rows(
    conn: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
) -> list[tuple[object, ...]]:
    projection = ", ".join(_quote(column) for column in columns)
    return [
        tuple(row)
        for row in conn.execute(f"SELECT {projection} FROM {_quote(table)}")
    ]


def _schema_sha(conn: sqlite3.Connection) -> str:
    objects = conn.execute(
        "SELECT type, name, tbl_name, COALESCE(sql, '') FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    payload = {
        "objects": objects,
        "user_version": int(conn.execute("PRAGMA user_version").fetchone()[0]),
        "application_id": int(conn.execute("PRAGMA application_id").fetchone()[0]),
        "encoding": str(conn.execute("PRAGMA encoding").fetchone()[0]),
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _post_fingerprint(
    schema_sha: str,
    counts: Mapping[str, object],
    hashes: Mapping[str, object],
) -> str:
    return hashlib.sha256(
        json.dumps(
            {"schema_sha256": schema_sha, "table_counts": counts, "table_hashes": hashes},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
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
    """Build an exact source-to-target repair spec with whole-DB post hashes."""

    if not isinstance(repair_id, str) or not repair_id.strip():
        raise ValueError("repair_id is required")
    source_path = Path(source_db)
    target_path = Path(target_db)
    with sqlite3.connect(source_path) as source, sqlite3.connect(target_path) as target:
        source.execute("PRAGMA foreign_keys = ON")
        target.execute("PRAGMA foreign_keys = ON")
        source_schema = _schema_sha(source)
        target_schema = _schema_sha(target)
        if source_schema != target_schema:
            raise ValueError("source and target SQLite schemas differ")
        if _tables(source) != _tables(target):
            raise ValueError("source and target SQLite table sets differ")

        operations: list[dict[str, object]] = []
        counts: dict[str, int] = {}
        hashes: dict[str, str] = {}
        for table in _tables(source):
            columns = _columns(source, table)
            source_rows = _rows(source, table, columns)
            target_rows = _rows(target, table, columns)
            counts[table] = len(target_rows)
            hashes[table] = _rows_sha(target_rows)

            removed_counter = Counter(source_rows) - Counter(target_rows)
            added_counter = Counter(target_rows) - Counter(source_rows)
            removed: list[list[object]] = []
            added: list[list[object]] = []
            for row, count in sorted(removed_counter.items(), key=lambda item: repr(item[0])):
                removed.extend([[_json_value(value) for value in row] for _ in range(count)])
            for row, count in sorted(added_counter.items(), key=lambda item: repr(item[0])):
                added.extend([[_json_value(value) for value in row] for _ in range(count)])
            if removed or added:
                operations.append(
                    {
                        "table": table,
                        "columns": list(columns),
                        "remove_rows": removed,
                        "add_rows": added,
                    }
                )

        return {
            "schema_version": "SQLITE_REPAIR_SPEC_V2",
            "repair_id": repair_id.strip(),
            "source_file_sha256": file_sha256(source_path),
            "source_schema_sha256": source_schema,
            "operations": operations,
            "expected_post_table_counts": counts,
            "expected_post_table_rows_sha256": hashes,
            "expected_post_fingerprint_sha256": _post_fingerprint(source_schema, counts, hashes),
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
    if spec.get("schema_version") != "SQLITE_REPAIR_SPEC_V2":
        raise ValueError("unsupported repair spec schema")
    repair_id = spec.get("repair_id")
    source_sha = spec.get("source_file_sha256")
    schema_sha = spec.get("source_schema_sha256")
    operations = spec.get("operations")
    counts = spec.get("expected_post_table_counts")
    hashes = spec.get("expected_post_table_rows_sha256")
    fingerprint = spec.get("expected_post_fingerprint_sha256")
    if not isinstance(repair_id, str) or not repair_id.strip():
        raise ValueError("repair_id is required")
    if not isinstance(source_sha, str) or not _SHA256.fullmatch(source_sha):
        raise ValueError("source_file_sha256 is invalid")
    if not isinstance(schema_sha, str) or not _SHA256.fullmatch(schema_sha):
        raise ValueError("source_schema_sha256 is invalid")
    if not isinstance(operations, list) or not all(
        isinstance(operation, Mapping) for operation in operations
    ):
        raise ValueError("operations must be an array of objects")
    if not isinstance(counts, Mapping) or not isinstance(hashes, Mapping):
        raise ValueError("postcondition maps are required")
    if not isinstance(fingerprint, str) or not _SHA256.fullmatch(fingerprint):
        raise ValueError("expected_post_fingerprint_sha256 is invalid")
    if fingerprint != _post_fingerprint(schema_sha, counts, hashes):
        raise ValueError("postcondition fingerprint mismatch")
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


def _row_count(
    conn: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
    row: Sequence[object],
) -> int:
    if len(columns) != len(row):
        raise ValueError(f"row length mismatch for {table}")
    where = " AND ".join(f"{_quote(column)} IS ?" for column in columns)
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
    live_tables = set(_tables(conn))
    if set(counts) != live_tables or set(hashes) != live_tables:
        raise ValueError("postcondition table set does not match live SQLite tables")

    operation_columns: dict[str, tuple[str, ...]] = {}
    for operation in operations:
        table = operation.get("table")
        columns = operation.get("columns")
        if not isinstance(table, str) or not isinstance(columns, list) or not all(
            isinstance(column, str) for column in columns
        ):
            raise ValueError("invalid operation table/columns")
        if table in operation_columns:
            raise ValueError(f"duplicate repair operation for table: {table}")
        operation_columns[table] = tuple(columns)

    extra_operation_tables = set(operation_columns) - live_tables
    if extra_operation_tables:
        raise ValueError(
            "repair operations reference tables absent from live SQLite: "
            f"{sorted(extra_operation_tables)}"
        )

    for table in sorted(live_tables):
        columns = _columns(conn, table)
        declared = operation_columns.get(table)
        if declared is not None and declared != columns:
            raise ValueError(f"column contract mismatch for {table}")
        expected_count = counts.get(table)
        expected_hash = hashes.get(table)
        if type(expected_count) is not int or not isinstance(expected_hash, str):
            raise ValueError(f"invalid postconditions for {table}")
        rows = _rows(conn, table, columns)
        if len(rows) != expected_count or _rows_sha(rows) != expected_hash:
            return False
    return True


def apply_repair_spec(
    db_path: str | Path,
    spec: Mapping[str, object],
    *,
    backup_path: str | Path | None = None,
) -> RepairReceipt:
    """Apply an exact repair transaction or return a whole-DB verified no-op."""

    path = Path(db_path)
    repair_id, source_sha, schema_sha, operations, counts, hashes = _load_spec(spec)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        if _schema_sha(conn) != schema_sha:
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
            conn.execute("PRAGMA defer_foreign_keys = ON")
            for operation in operations:
                table = operation.get("table")
                columns = operation.get("columns")
                remove_rows = operation.get("remove_rows")
                add_rows = operation.get("add_rows")
                if (
                    not isinstance(table, str)
                    or not isinstance(columns, list)
                    or not all(isinstance(column, str) for column in columns)
                    or not isinstance(remove_rows, list)
                    or not isinstance(add_rows, list)
                ):
                    raise ValueError("invalid repair operation")
                if tuple(columns) != _columns(conn, table):
                    raise ValueError(f"column contract mismatch for {table}")

                decoded_remove_rows: list[tuple[object, ...]] = []
                for encoded in remove_rows:
                    if not isinstance(encoded, list):
                        raise ValueError("remove_rows must contain arrays")
                    decoded_remove_rows.append(
                        tuple(_sqlite_value(value) for value in encoded)
                    )

                remove_counter = Counter(decoded_remove_rows)
                for row, remove_multiplicity in sorted(
                    remove_counter.items(), key=lambda item: repr(item[0])
                ):
                    actual_multiplicity = _row_count(conn, table, columns, row)
                    if actual_multiplicity < remove_multiplicity:
                        raise ValueError(
                            "expected remove-row multiplicity at least "
                            f"{remove_multiplicity}, found {actual_multiplicity} in {table}"
                        )
                    where = " AND ".join(
                        f"{_quote(column)} IS ?" for column in columns
                    )
                    cursor = conn.execute(
                        f"DELETE FROM {_quote(table)} WHERE {where}", row
                    )
                    if cursor.rowcount != actual_multiplicity:
                        raise ValueError(f"unexpected delete cardinality in {table}")
                    retained = actual_multiplicity - remove_multiplicity
                    if retained:
                        projection = ", ".join(_quote(column) for column in columns)
                        markers = ", ".join("?" for _ in columns)
                        conn.executemany(
                            f"INSERT INTO {_quote(table)} ({projection}) VALUES ({markers})",
                            [row] * retained,
                        )
                    removed_count += remove_multiplicity

                if add_rows:
                    projection = ", ".join(_quote(column) for column in columns)
                    markers = ", ".join("?" for _ in columns)
                    for encoded in add_rows:
                        if not isinstance(encoded, list):
                            raise ValueError("add_rows must contain arrays")
                        row = tuple(_sqlite_value(value) for value in encoded)
                        if len(row) != len(columns):
                            raise ValueError(f"add row length mismatch for {table}")
                        conn.execute(
                            f"INSERT INTO {_quote(table)} ({projection}) VALUES ({markers})",
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

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
from urllib.parse import quote

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SIDECAR_SUFFIXES = ("-wal", "-shm", "-journal")
_SPEC_KEYS = {
    "schema_version",
    "repair_id",
    "source_file_sha256",
    "source_schema_sha256",
    "operations",
    "expected_post_table_counts",
    "expected_post_table_rows_sha256",
    "expected_post_fingerprint_sha256",
    "authority_advanced",
    "h_id_allocations",
    "outbound_opened",
    "send_allowed",
    "spec_payload_sha256",
}


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


def _assert_quiescent(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"SQLite file does not exist: {path}")
    active = [
        str(Path(f"{path}{suffix}"))
        for suffix in _SIDECAR_SUFFIXES
        if Path(f"{path}{suffix}").exists()
        and Path(f"{path}{suffix}").stat().st_size > 0
    ]
    if active:
        raise ValueError(
            "SQLite artifact is not quiescent; checkpoint/export it before repair: "
            f"{active}"
        )


def _connect_read_only(path: Path) -> sqlite3.Connection:
    uri = f"file:{quote(str(path.resolve()), safe='/')}?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=30.0)


def _require_delete_journal(conn: sqlite3.Connection, *, label: str) -> None:
    mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).casefold()
    if mode != "delete":
        raise ValueError(
            f"{label} journal_mode must be DELETE for a quiescent repair artifact; found {mode}"
        )


def _validate_integrity(conn: sqlite3.Connection, *, label: str) -> None:
    integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
    if integrity.casefold() != "ok":
        raise ValueError(f"{label} integrity_check failed: {integrity}")
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        raise ValueError(f"{label} has {len(fk)} foreign-key violations")


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
            "AND (name NOT LIKE 'sqlite_%' OR name='sqlite_sequence') "
            "ORDER BY name"
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
        "WHERE name NOT LIKE 'sqlite_%' OR name='sqlite_sequence' "
        "ORDER BY type, name"
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
            {
                "schema_sha256": schema_sha,
                "table_counts": counts,
                "table_hashes": hashes,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _spec_payload_sha(spec_without_digest: Mapping[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            spec_without_digest,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class TableOperation:
    table: str
    columns: tuple[str, ...]
    remove_rows: tuple[tuple[object, ...], ...]
    add_rows: tuple[tuple[object, ...], ...]


@dataclass(frozen=True)
class ParsedRepairSpec:
    repair_id: str
    source_file_sha256: str
    source_schema_sha256: str
    operations: tuple[TableOperation, ...]
    expected_counts: Mapping[str, int]
    expected_hashes: Mapping[str, str]


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
    """Build an exact repair spec from two validated, quiescent SQLite files."""

    if not isinstance(repair_id, str) or not repair_id.strip():
        raise ValueError("repair_id is required")
    source_path = Path(source_db)
    target_path = Path(target_db)
    _assert_quiescent(source_path)
    _assert_quiescent(target_path)
    source_sha_before = file_sha256(source_path)
    target_sha_before = file_sha256(target_path)

    with _connect_read_only(source_path) as source, _connect_read_only(target_path) as target:
        source.execute("PRAGMA foreign_keys = ON")
        target.execute("PRAGMA foreign_keys = ON")
        _require_delete_journal(source, label="source")
        _require_delete_journal(target, label="target")
        _validate_integrity(source, label="source")
        _validate_integrity(target, label="target")
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

    _assert_quiescent(source_path)
    _assert_quiescent(target_path)
    if file_sha256(source_path) != source_sha_before:
        raise ValueError("source SQLite changed while building repair spec")
    if file_sha256(target_path) != target_sha_before:
        raise ValueError("target SQLite changed while building repair spec")

    spec: dict[str, object] = {
        "schema_version": "SQLITE_REPAIR_SPEC_V21",
        "repair_id": repair_id.strip(),
        "source_file_sha256": source_sha_before,
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
    spec["spec_payload_sha256"] = _spec_payload_sha(spec)
    return spec


def _load_spec(spec: Mapping[str, object]) -> ParsedRepairSpec:
    if set(spec) != _SPEC_KEYS:
        missing = sorted(_SPEC_KEYS - set(spec))
        extra = sorted(set(spec) - _SPEC_KEYS)
        raise ValueError(f"repair spec keys mismatch; missing={missing}, extra={extra}")
    if spec.get("schema_version") != "SQLITE_REPAIR_SPEC_V21":
        raise ValueError("unsupported repair spec schema")

    payload = dict(spec)
    digest = payload.pop("spec_payload_sha256")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise ValueError("spec_payload_sha256 is invalid")
    if digest != _spec_payload_sha(payload):
        raise ValueError("repair spec payload digest mismatch")

    repair_id = spec.get("repair_id")
    source_sha = spec.get("source_file_sha256")
    schema_sha = spec.get("source_schema_sha256")
    fingerprint = spec.get("expected_post_fingerprint_sha256")
    if not isinstance(repair_id, str) or not repair_id.strip():
        raise ValueError("repair_id is required")
    for label, value in (
        ("source_file_sha256", source_sha),
        ("source_schema_sha256", schema_sha),
        ("expected_post_fingerprint_sha256", fingerprint),
    ):
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise ValueError(f"{label} is invalid")

    for field in ("authority_advanced", "outbound_opened"):
        if spec.get(field) is not False:
            raise ValueError(f"{field} must be false")
    if spec.get("h_id_allocations") != 0 or type(spec.get("h_id_allocations")) is not int:
        raise ValueError("h_id_allocations must be integer zero")
    if spec.get("send_allowed") != 0 or type(spec.get("send_allowed")) is not int:
        raise ValueError("send_allowed must be integer zero")

    raw_counts = spec.get("expected_post_table_counts")
    raw_hashes = spec.get("expected_post_table_rows_sha256")
    if not isinstance(raw_counts, Mapping) or not isinstance(raw_hashes, Mapping):
        raise ValueError("postcondition maps are required")
    if set(raw_counts) != set(raw_hashes) or not raw_counts:
        raise ValueError("postcondition table maps must be non-empty and have identical keys")

    counts: dict[str, int] = {}
    hashes: dict[str, str] = {}
    for table, count in raw_counts.items():
        _quote(table)
        if type(count) is not int or count < 0:
            raise ValueError(f"invalid expected row count for {table}")
        row_hash = raw_hashes.get(table)
        if not isinstance(row_hash, str) or not _SHA256.fullmatch(row_hash):
            raise ValueError(f"invalid expected row hash for {table}")
        counts[table] = count
        hashes[table] = row_hash
    if fingerprint != _post_fingerprint(schema_sha, counts, hashes):
        raise ValueError("postcondition fingerprint mismatch")

    raw_operations = spec.get("operations")
    if not isinstance(raw_operations, list) or not all(
        isinstance(operation, Mapping) for operation in raw_operations
    ):
        raise ValueError("operations must be an array of objects")

    operations: list[TableOperation] = []
    seen_tables: set[str] = set()
    for raw_operation in raw_operations:
        if set(raw_operation) != {"table", "columns", "remove_rows", "add_rows"}:
            raise ValueError("repair operation keys are invalid")
        table = raw_operation.get("table")
        columns = raw_operation.get("columns")
        remove_rows = raw_operation.get("remove_rows")
        add_rows = raw_operation.get("add_rows")
        _quote(table)
        if table not in counts:
            raise ValueError(f"repair operation table absent from postconditions: {table}")
        if table in seen_tables:
            raise ValueError(f"duplicate repair operation for table: {table}")
        seen_tables.add(table)
        if (
            not isinstance(columns, list)
            or not columns
            or not all(isinstance(column, str) for column in columns)
            or len(set(columns)) != len(columns)
        ):
            raise ValueError(f"invalid operation columns for {table}")
        for column in columns:
            _quote(column)
        if not isinstance(remove_rows, list) or not isinstance(add_rows, list):
            raise ValueError(f"operation rows must be arrays for {table}")
        if not remove_rows and not add_rows:
            raise ValueError(f"empty repair operation for {table}")

        def decode_rows(raw_rows: list[object], label: str) -> tuple[tuple[object, ...], ...]:
            decoded: list[tuple[object, ...]] = []
            for raw_row in raw_rows:
                if not isinstance(raw_row, list) or len(raw_row) != len(columns):
                    raise ValueError(f"{label} row length mismatch for {table}")
                decoded.append(tuple(_sqlite_value(value) for value in raw_row))
            return tuple(decoded)

        operations.append(
            TableOperation(
                table=table,
                columns=tuple(columns),
                remove_rows=decode_rows(remove_rows, "remove"),
                add_rows=decode_rows(add_rows, "add"),
            )
        )

    return ParsedRepairSpec(
        repair_id=repair_id.strip(),
        source_file_sha256=source_sha,
        source_schema_sha256=schema_sha,
        operations=tuple(operations),
        expected_counts=counts,
        expected_hashes=hashes,
    )


def _row_count(
    conn: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
    row: Sequence[object],
) -> int:
    where = " AND ".join(f"{_quote(column)} IS ?" for column in columns)
    return int(
        conn.execute(
            f"SELECT COUNT(*) FROM {_quote(table)} WHERE {where}", tuple(row)
        ).fetchone()[0]
    )


def _postconditions_hold(conn: sqlite3.Connection, spec: ParsedRepairSpec) -> bool:
    live_tables = set(_tables(conn))
    if set(spec.expected_counts) != live_tables or set(spec.expected_hashes) != live_tables:
        raise ValueError("postcondition table set does not match live SQLite tables")
    if _schema_sha(conn) != spec.source_schema_sha256:
        raise ValueError("SQLite schema signature mismatch")

    operation_columns = {operation.table: operation.columns for operation in spec.operations}
    for table in sorted(live_tables):
        columns = _columns(conn, table)
        declared = operation_columns.get(table)
        if declared is not None and declared != columns:
            raise ValueError(f"column contract mismatch for {table}")
        rows = _rows(conn, table, columns)
        if (
            len(rows) != spec.expected_counts[table]
            or _rows_sha(rows) != spec.expected_hashes[table]
        ):
            return False
    return True


def _attest(conn: sqlite3.Connection, spec: ParsedRepairSpec) -> tuple[str, int]:
    if not _postconditions_hold(conn, spec):
        raise ValueError("repair postconditions failed")
    integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
    fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    if integrity.casefold() != "ok" or fk:
        raise ValueError("repair integrity/FK checks failed")
    return integrity, fk


def apply_repair_spec(
    db_path: str | Path,
    spec_payload: Mapping[str, object],
    *,
    backup_path: str | Path | None = None,
) -> RepairReceipt:
    """Apply an exact repair under lock or return a whole-DB verified no-op."""

    path = Path(db_path)
    _assert_quiescent(path)
    spec = _load_spec(spec_payload)
    backup = Path(backup_path) if backup_path is not None else None
    if backup is not None and backup.exists():
        raise ValueError("backup_path already exists")

    conn = sqlite3.connect(path, timeout=30.0, isolation_level=None)
    applied_removed = 0
    applied_added = 0
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA synchronous = FULL")
        _require_delete_journal(conn, label="repair database")
        conn.execute("BEGIN IMMEDIATE")

        if _schema_sha(conn) != spec.source_schema_sha256:
            raise ValueError("SQLite schema signature mismatch")

        if _postconditions_hold(conn, spec):
            integrity, fk = _attest(conn, spec)
            post_sha = file_sha256(path)
            conn.rollback()
            return RepairReceipt(
                repair_id=spec.repair_id,
                state="NOOP_ALREADY_APPLIED",
                applied_removed_rows=0,
                applied_added_rows=0,
                integrity_check=integrity,
                foreign_key_violations=fk,
                post_file_sha256=post_sha,
            )

        if file_sha256(path) != spec.source_file_sha256:
            raise ValueError(
                "database is neither the exact source parent nor the verified post-state"
            )
        _validate_integrity(conn, label="source")

        if backup is not None:
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
            if file_sha256(backup) != spec.source_file_sha256:
                raise ValueError("source backup SHA-256 mismatch")

        conn.execute("PRAGMA defer_foreign_keys = ON")
        operations = sorted(
            spec.operations,
            key=lambda operation: (operation.table == "sqlite_sequence", operation.table),
        )
        for operation in operations:
            if operation.columns != _columns(conn, operation.table):
                raise ValueError(f"column contract mismatch for {operation.table}")

            remove_counter = Counter(operation.remove_rows)
            for row, remove_multiplicity in sorted(
                remove_counter.items(), key=lambda item: repr(item[0])
            ):
                actual_multiplicity = _row_count(
                    conn,
                    operation.table,
                    operation.columns,
                    row,
                )
                if actual_multiplicity < remove_multiplicity:
                    raise ValueError(
                        "expected remove-row multiplicity at least "
                        f"{remove_multiplicity}, found {actual_multiplicity} "
                        f"in {operation.table}"
                    )
                where = " AND ".join(
                    f"{_quote(column)} IS ?" for column in operation.columns
                )
                cursor = conn.execute(
                    f"DELETE FROM {_quote(operation.table)} WHERE {where}", row
                )
                if cursor.rowcount != actual_multiplicity:
                    raise ValueError(
                        f"unexpected delete cardinality in {operation.table}"
                    )
                retained = actual_multiplicity - remove_multiplicity
                if retained:
                    projection = ", ".join(
                        _quote(column) for column in operation.columns
                    )
                    markers = ", ".join("?" for _ in operation.columns)
                    conn.executemany(
                        f"INSERT INTO {_quote(operation.table)} "
                        f"({projection}) VALUES ({markers})",
                        [row] * retained,
                    )
                applied_removed += remove_multiplicity

            if operation.add_rows:
                projection = ", ".join(
                    _quote(column) for column in operation.columns
                )
                markers = ", ".join("?" for _ in operation.columns)
                for row in operation.add_rows:
                    conn.execute(
                        f"INSERT INTO {_quote(operation.table)} "
                        f"({projection}) VALUES ({markers})",
                        row,
                    )
                    applied_added += 1

        _attest(conn, spec)
        conn.commit()

        # Reacquire the writer lock and attest the committed state. If another
        # writer raced after commit, authority remains blocked instead of relying
        # on the pre-commit observation.
        conn.execute("BEGIN IMMEDIATE")
        integrity, fk = _attest(conn, spec)
        post_sha = file_sha256(path)
        conn.rollback()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()

    _assert_quiescent(path)
    return RepairReceipt(
        repair_id=spec.repair_id,
        state="APPLIED_CANARY_NON_AUTHORITY",
        applied_removed_rows=applied_removed,
        applied_added_rows=applied_added,
        integrity_check=integrity,
        foreign_key_violations=fk,
        post_file_sha256=post_sha,
    )

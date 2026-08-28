from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
from typing import Iterable, Mapping

from .alias_semantics import identity_key

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class AliasRepairInstruction:
    alias_hotel_id: str
    canonical_hotel_id: str
    expected_alias_name: str
    expected_alias_city: str
    expected_target_name: str
    expected_target_city: str
    restore_state: str = "CANONICAL_CURRENT_RECONCILED"

    @classmethod
    def from_mapping(cls, row: Mapping[str, object]) -> "AliasRepairInstruction":
        required = (
            "alias_hotel_id",
            "canonical_hotel_id",
            "expected_alias_name",
            "expected_alias_city",
            "expected_target_name",
            "expected_target_city",
        )
        values: dict[str, str] = {}
        for key in required:
            value = row.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key} must be a non-empty string")
            values[key] = value.strip()
        restore = row.get("restore_state", "CANONICAL_CURRENT_RECONCILED")
        if not isinstance(restore, str) or not restore.strip():
            raise ValueError("restore_state must be a non-empty string")
        return cls(**values, restore_state=restore.strip())


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _hotel(conn: sqlite3.Connection, hotel_id: str) -> tuple[str, str, str]:
    row = conn.execute(
        "SELECT canonical_name, COALESCE(city,''), state FROM hotels WHERE hotel_id=?",
        (hotel_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"hotel missing: {hotel_id}")
    return str(row[0]), str(row[1]), str(row[2])


def _verify_instruction(conn: sqlite3.Connection, item: AliasRepairInstruction) -> str:
    alias_name, alias_city, alias_state = _hotel(conn, item.alias_hotel_id)
    target_name, target_city, _ = _hotel(conn, item.canonical_hotel_id)

    if identity_key(alias_name, alias_city) != identity_key(item.expected_alias_name, item.expected_alias_city):
        raise ValueError(f"alias identity drift: {item.alias_hotel_id}")
    if identity_key(target_name, target_city) != identity_key(item.expected_target_name, item.expected_target_city):
        raise ValueError(f"target identity drift: {item.canonical_hotel_id}")
    if identity_key(alias_name, alias_city) == identity_key(target_name, target_city):
        raise ValueError(f"repair plan would remove a semantically valid alias: {item.alias_hotel_id}")

    edge = conn.execute(
        "SELECT canonical_hotel_id FROM hotel_aliases WHERE alias_hotel_id=?",
        (item.alias_hotel_id,),
    ).fetchone()
    expected_superseded = f"SUPERSEDED_DUPLICATE→{item.canonical_hotel_id}"

    if edge is None:
        if alias_state != item.restore_state:
            raise ValueError(f"alias edge absent but state not repaired: {item.alias_hotel_id}")
        return "ALREADY_REPAIRED"

    if str(edge[0]) != item.canonical_hotel_id:
        raise ValueError(f"alias target drift: {item.alias_hotel_id}")
    if alias_state != expected_superseded:
        raise ValueError(f"unexpected superseded state for {item.alias_hotel_id}: {alias_state!r}")
    return "NEEDS_REPAIR"


def apply_alias_repair(
    source_db: str | Path,
    output_db: str | Path,
    instructions: Iterable[AliasRepairInstruction],
    *,
    expected_parent_sha256: str,
) -> dict[str, object]:
    source = Path(source_db)
    output = Path(output_db)
    if source.resolve() == output.resolve():
        raise ValueError("in-place repair is forbidden")
    if not source.exists():
        raise FileNotFoundError(source)
    if not isinstance(expected_parent_sha256, str) or not _SHA256_RE.fullmatch(expected_parent_sha256):
        raise ValueError("expected_parent_sha256 must be lowercase SHA-256 hex")
    actual_parent_sha = sha256_file(source)
    if actual_parent_sha != expected_parent_sha256:
        raise ValueError("parent SHA-256 mismatch")

    items = tuple(instructions)
    if not items:
        raise ValueError("repair instructions must not be empty")
    alias_ids = [x.alias_hotel_id for x in items]
    if len(set(alias_ids)) != len(alias_ids):
        raise ValueError("duplicate alias_hotel_id in repair plan")

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    temp_output = output.with_name(output.name + ".tmp")
    if temp_output.exists():
        temp_output.unlink()
    shutil.copy2(source, temp_output)

    try:
        with sqlite3.connect(temp_output) as conn:
            if str(conn.execute("PRAGMA integrity_check").fetchone()[0]).lower() != "ok":
                raise ValueError("source copy failed integrity_check")
            if conn.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("source copy has FK violations")

            statuses = {item.alias_hotel_id: _verify_instruction(conn, item) for item in items}
            conn.execute("BEGIN IMMEDIATE")
            mutations = 0
            for item in items:
                if statuses[item.alias_hotel_id] == "ALREADY_REPAIRED":
                    continue
                cur = conn.execute(
                    "UPDATE hotels SET state=? WHERE hotel_id=? AND state=?",
                    (
                        item.restore_state,
                        item.alias_hotel_id,
                        f"SUPERSEDED_DUPLICATE→{item.canonical_hotel_id}",
                    ),
                )
                if cur.rowcount != 1:
                    raise ValueError(f"state repair cardinality failed: {item.alias_hotel_id}")
                cur = conn.execute(
                    "DELETE FROM hotel_aliases WHERE alias_hotel_id=? AND canonical_hotel_id=?",
                    (item.alias_hotel_id, item.canonical_hotel_id),
                )
                if cur.rowcount != 1:
                    raise ValueError(f"alias delete cardinality failed: {item.alias_hotel_id}")
                mutations += 2
            conn.commit()

            for item in items:
                if _verify_instruction(conn, item) != "ALREADY_REPAIRED":
                    raise ValueError(f"post-repair verification failed: {item.alias_hotel_id}")

            integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
            fk_violations = len(conn.execute("PRAGMA foreign_key_check").fetchall())
            physical_rows = int(conn.execute("SELECT COUNT(*) FROM hotels").fetchone()[0])
            alias_rows = int(conn.execute("SELECT COUNT(*) FROM hotel_aliases").fetchone()[0])
            superseded_rows = int(
                conn.execute("SELECT COUNT(*) FROM hotels WHERE state LIKE 'SUPERSEDED_DUPLICATE%'").fetchone()[0]
            )
        temp_output.replace(output)
    except Exception:
        temp_output.unlink(missing_ok=True)
        raise

    return {
        "schema_version": "ASR_REPAIR_REPLAY_V1",
        "parent_sha256": actual_parent_sha,
        "output_sha256": sha256_file(output),
        "instructions": [asdict(item) for item in items],
        "mutations": mutations,
        "integrity_check": integrity,
        "foreign_key_violations": fk_violations,
        "physical_rows": physical_rows,
        "alias_rows": alias_rows,
        "superseded_rows": superseded_rows,
        "candidate_active_canonical": None,
        "active_denominator_state": "RECONCILE_REQUIRED_CROSS_PLANE",
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }


def _load_plan(path: str | Path) -> tuple[str, tuple[AliasRepairInstruction, ...]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("repair plan must be a JSON object")
    parent_sha = raw.get("expected_parent_sha256")
    if not isinstance(parent_sha, str) or not _SHA256_RE.fullmatch(parent_sha):
        raise ValueError("expected_parent_sha256 must be lowercase SHA-256 hex")
    rows = raw.get("instructions")
    if not isinstance(rows, list) or not rows:
        raise ValueError("instructions must be a non-empty JSON array")
    if not all(isinstance(row, Mapping) for row in rows):
        raise ValueError("instructions must contain only JSON objects")
    return parent_sha, tuple(AliasRepairInstruction.from_mapping(row) for row in rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.alias_repair")
    parser.add_argument("source_db")
    parser.add_argument("repair_plan")
    parser.add_argument("--out", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args(argv)

    parent_sha, items = _load_plan(args.repair_plan)
    result = apply_alias_repair(args.source_db, args.out, items, expected_parent_sha256=parent_sha)
    Path(args.manifest).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

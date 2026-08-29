from __future__ import annotations

import copy
from pathlib import Path
import shutil
import sqlite3

import pytest

from swiss_os.sqlite_repair import apply_repair_spec, build_repair_spec


def _make_db(path: Path, *, repaired: bool = False) -> None:
    con = sqlite3.connect(path)
    con.executescript(
        """
        PRAGMA foreign_keys=ON;
        PRAGMA user_version=7;
        CREATE TABLE hotels (
          hotel_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          state TEXT NOT NULL
        );
        CREATE TABLE hotel_aliases (
          alias_hotel_id TEXT PRIMARY KEY REFERENCES hotels(hotel_id),
          canonical_hotel_id TEXT NOT NULL REFERENCES hotels(hotel_id)
        );
        CREATE TABLE audit_log (
          event_id TEXT PRIMARY KEY,
          note TEXT NOT NULL
        );
        CREATE TABLE duplicate_notes (
          note TEXT NOT NULL
        );
        """
    )
    con.executemany(
        "INSERT INTO hotels VALUES (?, ?, ?)",
        [
            ("H-0001", "Alpha", "ACTIVE" if repaired else "SUPERSEDED_DUPLICATE"),
            ("H-0002", "Beta", "ACTIVE"),
        ],
    )
    if not repaired:
        con.execute("INSERT INTO hotel_aliases VALUES ('H-0001', 'H-0002')")
    con.execute("INSERT INTO audit_log VALUES ('E-1', 'unchanged')")
    duplicate_count = 1 if repaired else 3
    con.executemany(
        "INSERT INTO duplicate_notes VALUES (?)",
        [("same",)] * duplicate_count,
    )
    con.commit()
    con.close()


def _logical_state(path: Path) -> dict[str, list[tuple[object, ...]]]:
    con = sqlite3.connect(path)
    tables = [
        row[0]
        for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    result = {
        table: sorted(con.execute(f'SELECT * FROM "{table}"').fetchall(), key=repr)
        for table in tables
    }
    con.close()
    return result


def _paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "source.sqlite"
    target = tmp_path / "target.sqlite"
    work = tmp_path / "work.sqlite"
    _make_db(source)
    _make_db(target, repaired=True)
    shutil.copy2(source, work)
    return source, target, work


def test_build_apply_and_replay_exact_repair(tmp_path: Path) -> None:
    source, target, work = _paths(tmp_path)
    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")

    assert set(spec["expected_post_table_counts"]) == {
        "audit_log",
        "duplicate_notes",
        "hotel_aliases",
        "hotels",
    }
    receipt = apply_repair_spec(
        work,
        spec,
        backup_path=tmp_path / "backup.sqlite",
    )
    assert receipt.state == "APPLIED_CANARY_NON_AUTHORITY"
    assert receipt.applied_removed_rows == 4
    assert _logical_state(work) == _logical_state(target)
    assert _logical_state(tmp_path / "backup.sqlite") == _logical_state(source)
    assert receipt.as_dict()["authority_advanced"] is False
    assert receipt.as_dict()["h_id_allocations"] == 0
    assert receipt.as_dict()["send_allowed"] == 0

    replay = apply_repair_spec(work, spec)
    assert replay.state == "NOOP_ALREADY_APPLIED"
    assert replay.applied_removed_rows == 0
    assert replay.applied_added_rows == 0


def test_multiset_remove_preserves_target_duplicate_multiplicity(tmp_path: Path) -> None:
    source, target, work = _paths(tmp_path)
    spec = build_repair_spec(source, target, repair_id="DUPLICATE-REPAIR")
    apply_repair_spec(work, spec)

    con = sqlite3.connect(work)
    count = con.execute(
        "SELECT COUNT(*) FROM duplicate_notes WHERE note='same'"
    ).fetchone()[0]
    con.close()
    assert count == 1


def test_unaffected_table_drift_is_not_accepted_as_replay(tmp_path: Path) -> None:
    source, target, work = _paths(tmp_path)
    spec = build_repair_spec(source, target, repair_id="GLOBAL-FINGERPRINT")
    apply_repair_spec(work, spec)

    con = sqlite3.connect(work)
    con.execute("UPDATE audit_log SET note='tampered' WHERE event_id='E-1'")
    con.commit()
    con.close()

    with pytest.raises(ValueError, match="neither the exact source parent"):
        apply_repair_spec(work, spec)


def test_wrong_parent_fails_closed(tmp_path: Path) -> None:
    source, target, _ = _paths(tmp_path)
    wrong = tmp_path / "wrong.sqlite"
    shutil.copy2(source, wrong)
    con = sqlite3.connect(wrong)
    con.execute("UPDATE audit_log SET note='wrong-parent' WHERE event_id='E-1'")
    con.commit()
    con.close()

    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    with pytest.raises(ValueError, match="neither the exact source parent"):
        apply_repair_spec(wrong, spec)


def test_tampered_postcondition_fingerprint_fails_before_mutation(tmp_path: Path) -> None:
    source, target, work = _paths(tmp_path)
    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    broken = copy.deepcopy(spec)
    broken["expected_post_table_counts"]["hotels"] = 99
    before = _logical_state(work)

    with pytest.raises(ValueError, match="postcondition fingerprint mismatch"):
        apply_repair_spec(work, broken)
    assert _logical_state(work) == before


def test_missing_postcondition_table_fails_closed(tmp_path: Path) -> None:
    source, target, work = _paths(tmp_path)
    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    broken = copy.deepcopy(spec)
    broken["expected_post_table_counts"].pop("audit_log")

    with pytest.raises(ValueError, match="postcondition fingerprint mismatch"):
        apply_repair_spec(work, broken)


def test_extra_operation_table_is_rejected_even_on_post_state(tmp_path: Path) -> None:
    source, target, _ = _paths(tmp_path)
    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    spec["operations"].append(
        {
            "table": "ghost_table",
            "columns": ["id"],
            "remove_rows": [],
            "add_rows": [],
        }
    )

    with pytest.raises(ValueError, match="absent from live SQLite"):
        apply_repair_spec(target, spec)


def test_invalid_identifier_is_rejected(tmp_path: Path) -> None:
    source, target, work = _paths(tmp_path)
    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    spec["operations"][0]["table"] = "hotels; DROP TABLE hotels"

    with pytest.raises(ValueError, match="invalid SQLite identifier"):
        apply_repair_spec(work, spec)


def test_preauthorization_fields_are_rejected(tmp_path: Path) -> None:
    source, target, work = _paths(tmp_path)
    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    spec["authority_advanced"] = True

    with pytest.raises(ValueError, match="authority_advanced must be false"):
        apply_repair_spec(work, spec)


def test_existing_backup_path_fails_before_mutation(tmp_path: Path) -> None:
    source, target, work = _paths(tmp_path)
    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    backup = tmp_path / "backup.sqlite"
    backup.write_bytes(b"do not overwrite")
    before = _logical_state(work)

    with pytest.raises(ValueError, match="backup_path already exists"):
        apply_repair_spec(work, spec, backup_path=backup)
    assert backup.read_bytes() == b"do not overwrite"
    assert _logical_state(work) == before


def test_schema_drift_is_rejected(tmp_path: Path) -> None:
    source, target, work = _paths(tmp_path)
    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    con = sqlite3.connect(work)
    con.execute("CREATE TABLE extra_table (id TEXT PRIMARY KEY)")
    con.commit()
    con.close()

    with pytest.raises(ValueError, match="schema signature mismatch"):
        apply_repair_spec(work, spec)

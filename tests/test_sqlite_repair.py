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
        CREATE TABLE hotels (
          hotel_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          state TEXT NOT NULL
        );
        CREATE TABLE hotel_aliases (
          alias_hotel_id TEXT PRIMARY KEY REFERENCES hotels(hotel_id),
          canonical_hotel_id TEXT NOT NULL REFERENCES hotels(hotel_id)
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
    con.commit()
    con.close()


def _logical_rows(path: Path):
    con = sqlite3.connect(path)
    result = {
        table: con.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
        for table in ("hotels", "hotel_aliases")
    }
    con.close()
    return result


def test_build_apply_and_replay_exact_repair(tmp_path):
    source = tmp_path / "source.sqlite"
    target = tmp_path / "target.sqlite"
    work = tmp_path / "work.sqlite"
    _make_db(source)
    _make_db(target, repaired=True)
    shutil.copy2(source, work)

    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    receipt = apply_repair_spec(work, spec, backup_path=tmp_path / "backup.sqlite")
    assert receipt.state == "APPLIED_CANARY_NON_AUTHORITY"
    assert _logical_rows(work) == _logical_rows(target)
    assert receipt.as_dict()["authority_advanced"] is False
    assert receipt.as_dict()["send_allowed"] == 0

    replay = apply_repair_spec(work, spec)
    assert replay.state == "NOOP_ALREADY_APPLIED"
    assert replay.applied_removed_rows == 0
    assert replay.applied_added_rows == 0


def test_wrong_parent_fails_closed(tmp_path):
    source = tmp_path / "source.sqlite"
    target = tmp_path / "target.sqlite"
    wrong = tmp_path / "wrong.sqlite"
    _make_db(source)
    _make_db(target, repaired=True)
    _make_db(wrong)
    con = sqlite3.connect(wrong)
    con.execute("UPDATE hotels SET name='Tampered' WHERE hotel_id='H-0002'")
    con.commit()
    con.close()

    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    with pytest.raises(ValueError, match="neither the exact source parent"):
        apply_repair_spec(wrong, spec)


def test_tampered_postcondition_rolls_back(tmp_path):
    source = tmp_path / "source.sqlite"
    target = tmp_path / "target.sqlite"
    work = tmp_path / "work.sqlite"
    _make_db(source)
    _make_db(target, repaired=True)
    shutil.copy2(source, work)

    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    broken = copy.deepcopy(spec)
    broken["expected_post_table_counts"]["hotels"] = 99
    before = _logical_rows(work)
    with pytest.raises(ValueError, match="postconditions"):
        apply_repair_spec(work, broken)
    assert _logical_rows(work) == before


def test_invalid_identifier_is_rejected(tmp_path):
    source = tmp_path / "source.sqlite"
    target = tmp_path / "target.sqlite"
    work = tmp_path / "work.sqlite"
    _make_db(source)
    _make_db(target, repaired=True)
    shutil.copy2(source, work)

    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    spec["operations"][0]["table"] = "hotels; DROP TABLE hotels"
    with pytest.raises(ValueError, match="invalid SQLite identifier"):
        apply_repair_spec(work, spec)


def test_preauthorization_fields_are_rejected(tmp_path):
    source = tmp_path / "source.sqlite"
    target = tmp_path / "target.sqlite"
    work = tmp_path / "work.sqlite"
    _make_db(source)
    _make_db(target, repaired=True)
    shutil.copy2(source, work)

    spec = build_repair_spec(source, target, repair_id="TEST-REPAIR")
    spec["authority_advanced"] = True
    with pytest.raises(ValueError, match="authority_advanced must be false"):
        apply_repair_spec(work, spec)

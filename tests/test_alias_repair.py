from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from swiss_os.alias_repair import AliasRepairInstruction, apply_alias_repair


def _db(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys=ON;
            CREATE TABLE hotels (
              hotel_id TEXT PRIMARY KEY,
              canonical_name TEXT NOT NULL,
              city TEXT,
              state TEXT NOT NULL
            );
            CREATE TABLE hotel_aliases (
              alias_hotel_id TEXT PRIMARY KEY,
              canonical_hotel_id TEXT NOT NULL,
              reason_code TEXT NOT NULL,
              evidence_ref TEXT,
              run_id TEXT NOT NULL,
              created_at TEXT NOT NULL,
              FOREIGN KEY(alias_hotel_id) REFERENCES hotels(hotel_id),
              FOREIGN KEY(canonical_hotel_id) REFERENCES hotels(hotel_id)
            );
            """
        )
        conn.executemany(
            "INSERT INTO hotels VALUES (?,?,?,?)",
            [
                ("H-0001", "Alpha Hotel", "Bern", "SUPERSEDED_DUPLICATE→H-0002"),
                ("H-0002", "Beta Hotel", "Zürich", "CANONICAL_CURRENT_RECONCILED"),
            ],
        )
        conn.execute(
            "INSERT INTO hotel_aliases VALUES (?,?,?,?,?,?)",
            ("H-0001", "H-0002", "BAD_LINEAGE", "ER:1", "RUN-1", "2026-08-28"),
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _instruction(**overrides: str) -> AliasRepairInstruction:
    values = dict(
        alias_hotel_id="H-0001",
        canonical_hotel_id="H-0002",
        expected_alias_name="Alpha Hotel",
        expected_alias_city="Bern",
        expected_target_name="Beta Hotel",
        expected_target_city="Zürich",
    )
    values.update(overrides)
    return AliasRepairInstruction(**values)


class AliasRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_repair_is_copy_on_write_and_fail_closed(self) -> None:
        source = self.root / "parent.sqlite"
        parent_sha = _db(source)
        out = self.root / "repaired.sqlite"

        result = apply_alias_repair(source, out, [_instruction()], expected_parent_sha256=parent_sha)

        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), parent_sha)
        self.assertEqual(result["mutations"], 2)
        self.assertEqual(result["alias_rows"], 0)
        self.assertEqual(result["superseded_rows"], 0)
        self.assertIsNone(result["candidate_active_canonical"])
        self.assertEqual(result["active_denominator_state"], "RECONCILE_REQUIRED_CROSS_PLANE")
        self.assertEqual(str(result["integrity_check"]).lower(), "ok")
        self.assertEqual(result["foreign_key_violations"], 0)
        self.assertIs(result["authority_advanced"], False)
        self.assertEqual(result["h_id_allocations"], 0)
        self.assertIs(result["outbound_opened"], False)
        self.assertEqual(result["send_allowed"], 0)

        with sqlite3.connect(out) as conn:
            self.assertEqual(
                conn.execute("SELECT state FROM hotels WHERE hotel_id='H-0001'").fetchone()[0],
                "CANONICAL_CURRENT_RECONCILED",
            )
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM hotel_aliases").fetchone()[0], 0)

    def test_parent_sha_mismatch_rejects_without_output(self) -> None:
        source = self.root / "parent.sqlite"
        _db(source)
        out = self.root / "repaired.sqlite"
        with self.assertRaisesRegex(ValueError, "parent SHA-256 mismatch"):
            apply_alias_repair(source, out, [_instruction()], expected_parent_sha256="0" * 64)
        self.assertFalse(out.exists())

    def test_identity_drift_fails_closed(self) -> None:
        source = self.root / "parent.sqlite"
        parent_sha = _db(source)
        for field, value, match in (
            ("expected_alias_name", "Different", "alias identity drift"),
            ("expected_alias_city", "Basel", "alias identity drift"),
            ("expected_target_name", "Different", "target identity drift"),
            ("expected_target_city", "Basel", "target identity drift"),
            ("canonical_hotel_id", "H-9999", "hotel missing"),
        ):
            out = self.root / f"{field}.sqlite"
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, match):
                apply_alias_repair(
                    source,
                    out,
                    [_instruction(**{field: value})],
                    expected_parent_sha256=parent_sha,
                )
            self.assertFalse(out.exists())
            self.assertFalse((self.root / f"{field}.sqlite.tmp").exists())

    def test_wrong_persisted_target_fails_closed(self) -> None:
        source = self.root / "parent.sqlite"
        _db(source)
        with sqlite3.connect(source) as conn:
            conn.execute("UPDATE hotel_aliases SET canonical_hotel_id='H-0001' WHERE alias_hotel_id='H-0001'")
        parent_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        out = self.root / "repaired.sqlite"
        with self.assertRaisesRegex(ValueError, "alias target drift"):
            apply_alias_repair(source, out, [_instruction()], expected_parent_sha256=parent_sha)

    def test_idempotent_replay_from_already_repaired_parent(self) -> None:
        source = self.root / "parent.sqlite"
        parent_sha = _db(source)
        first = self.root / "first.sqlite"
        apply_alias_repair(source, first, [_instruction()], expected_parent_sha256=parent_sha)

        second = self.root / "second.sqlite"
        result = apply_alias_repair(
            first,
            second,
            [_instruction()],
            expected_parent_sha256=hashlib.sha256(first.read_bytes()).hexdigest(),
        )
        self.assertEqual(result["mutations"], 0)
        self.assertEqual(result["alias_rows"], 0)
        self.assertEqual(result["superseded_rows"], 0)

    def test_in_place_repair_is_forbidden(self) -> None:
        source = self.root / "parent.sqlite"
        parent_sha = _db(source)
        with self.assertRaisesRegex(ValueError, "in-place repair is forbidden"):
            apply_alias_repair(source, source, [_instruction()], expected_parent_sha256=parent_sha)

    def test_duplicate_alias_instruction_is_rejected(self) -> None:
        source = self.root / "parent.sqlite"
        parent_sha = _db(source)
        out = self.root / "repaired.sqlite"
        with self.assertRaisesRegex(ValueError, "duplicate alias_hotel_id"):
            apply_alias_repair(source, out, [_instruction(), _instruction()], expected_parent_sha256=parent_sha)

    def test_invalid_sha_format_rejected(self) -> None:
        source = self.root / "parent.sqlite"
        _db(source)
        out = self.root / "repaired.sqlite"
        with self.assertRaisesRegex(ValueError, "lowercase SHA-256 hex"):
            apply_alias_repair(source, out, [_instruction()], expected_parent_sha256="G" * 64)
        self.assertFalse(out.exists())
        self.assertFalse((self.root / "repaired.sqlite.tmp").exists())

    def test_failed_identity_preflight_leaves_no_output_or_temp(self) -> None:
        source = self.root / "parent.sqlite"
        parent_sha = _db(source)
        out = self.root / "repaired.sqlite"
        with self.assertRaisesRegex(ValueError, "alias identity drift"):
            apply_alias_repair(
                source,
                out,
                [_instruction(expected_alias_name="Wrong")],
                expected_parent_sha256=parent_sha,
            )
        self.assertFalse(out.exists())
        self.assertFalse((self.root / "repaired.sqlite.tmp").exists())


if __name__ == "__main__":
    unittest.main()

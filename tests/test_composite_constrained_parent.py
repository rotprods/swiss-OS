from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from swiss_os.composite_constrained_parent import validate_composite_parent, verify_materialized_sqlite


def _sqlite(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys=ON;
            CREATE TABLE hotels (hotel_id TEXT PRIMARY KEY, state TEXT NOT NULL);
            INSERT INTO hotels VALUES ('H-0001', 'CANONICAL_CURRENT_RECONCILED');
            """
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(output_sha: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "CCP-1.0",
        "project": "SWITZERLAND_JOB_OS",
        "base_sha256": "0" * 64,
        "base_size_bytes": 1024,
        "base_replicas": [
            {"provider": "GOOGLE_DRIVE", "file_id": "base-primary", "size_bytes": 1024},
            {"provider": "GOOGLE_DRIVE", "file_id": "base-copy", "size_bytes": 1024},
        ],
        "repair_protocol": "ARR-1.0",
        "repair_plan_path": "docs/state/repair.json",
        "repair_plan_blob_sha": "1" * 40,
        "repair_engine_blob_sha": "2" * 40,
        "repair_engine_commit_sha": "3" * 40,
        "expected_materialized_sha256": output_sha,
        "materialization_proof": {
            "output_sha256": output_sha,
            "integrity_check": "ok",
            "foreign_key_violations": 0,
            "physical_rows": 1,
            "alias_rows": 0,
            "superseded_rows": 0,
            "idempotency_replay": "PASS",
        },
        "active_denominator": None,
        "active_denominator_state": "RECONCILE_REQUIRED_CROSS_PLANE",
        "authority_advanced": False,
        "canonical_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    payload.update(overrides)
    return payload


class CompositeConstrainedParentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "materialized.sqlite"
        self.output_sha = _sqlite(self.db)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_valid_manifest_is_durable_but_not_authority(self) -> None:
        result = validate_composite_parent(_manifest(self.output_sha))
        self.assertTrue(result["valid"])
        self.assertEqual(result["representation_state"], "DURABLE_MATERIALIZABLE_CONSTRAINED_PARENT")
        self.assertEqual(result["base_replica_count"], 2)
        self.assertIs(result["authority_eligible"], False)
        self.assertIsNone(result["active_denominator"])
        self.assertEqual(result["active_denominator_state"], "RECONCILE_REQUIRED_CROSS_PLANE")
        self.assertIs(result["authority_advanced"], False)
        self.assertEqual(result["canonical_id_allocations"], 0)
        self.assertIs(result["outbound_opened"], False)
        self.assertEqual(result["send_allowed"], 0)

    def test_materialized_sqlite_must_match_precommitted_sha(self) -> None:
        result = verify_materialized_sqlite(self.db, _manifest(self.output_sha))
        self.assertEqual(result["materialization_state"], "EXACT")
        self.assertEqual(result["output_sha256"], self.output_sha)
        self.assertEqual(str(result["integrity_check"]).lower(), "ok")
        self.assertEqual(result["foreign_key_violations"], 0)
        self.assertIs(result["authority_eligible"], False)

        wrong = _manifest("f" * 64)
        with self.assertRaisesRegex(ValueError, "materialized SQLite SHA-256 mismatch"):
            verify_materialized_sqlite(self.db, wrong)

    def test_preauthorized_denominator_authority_or_outbound_rejected(self) -> None:
        for key, value, match in (
            ("active_denominator", 1, "must not pre-authorize"),
            ("authority_advanced", True, "cannot advance authority"),
            ("canonical_id_allocations", 1, "cannot allocate canonical IDs"),
            ("canonical_id_allocations", False, "cannot allocate canonical IDs"),
            ("outbound_opened", True, "cannot open outbound"),
            ("send_allowed", 1, "must be integer 0"),
            ("send_allowed", False, "must be integer 0"),
        ):
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, match):
                validate_composite_parent(_manifest(self.output_sha, **{key: value}))

    def test_replica_semantics_fail_closed(self) -> None:
        cases = [
            ([{"provider": "LOCAL", "file_id": "x", "size_bytes": 1024}], "unsupported durable provider"),
            ([{"provider": "GOOGLE_DRIVE", "file_id": "x", "size_bytes": 1}], "size differs"),
            (
                [
                    {"provider": "GOOGLE_DRIVE", "file_id": "x", "size_bytes": 1024},
                    {"provider": "GOOGLE_DRIVE", "file_id": "x", "size_bytes": 1024},
                ],
                "duplicate base replica",
            ),
        ]
        for replicas, match in cases:
            with self.subTest(match=match), self.assertRaisesRegex(ValueError, match):
                validate_composite_parent(_manifest(self.output_sha, base_replicas=replicas))

    def test_materialization_proof_is_exact_and_strict(self) -> None:
        base = _manifest(self.output_sha)
        for patch, match in (
            ({"output_sha256": "f" * 64}, "proof SHA"),
            ({"integrity_check": "not ok"}, "integrity_check"),
            ({"foreign_key_violations": 1}, "foreign key violations"),
            ({"foreign_key_violations": False}, "strict non-negative integer"),
            ({"physical_rows": False}, "strict positive integer"),
            ({"idempotency_replay": "FAIL"}, "idempotency_replay"),
        ):
            payload = dict(base)
            proof = dict(base["materialization_proof"])
            proof.update(patch)
            payload["materialization_proof"] = proof
            with self.subTest(patch=patch), self.assertRaisesRegex(ValueError, match):
                validate_composite_parent(payload)

    def test_base_and_output_digest_cannot_be_identical(self) -> None:
        payload = _manifest(self.output_sha, base_sha256=self.output_sha)
        with self.assertRaisesRegex(ValueError, "must differ"):
            validate_composite_parent(payload)


if __name__ == "__main__":
    unittest.main()

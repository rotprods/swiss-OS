from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from swiss_os.v2_migration import (  # noqa: E402
    MigrationInventory,
    MigrationShadowError,
    compile_migration_shadow,
)

FIXTURE = ROOT / "tests/fixtures/v2_migration_inventory.json"
COMPILER_SHA = "1" * 40
GENERATED_AT = "2026-08-30T20:30:00Z"
SALT = "unit-test-pseudonym-salt-v2"


def payload() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def compile_fixture(raw: dict[str, object] | None = None):
    inventory = MigrationInventory.from_mapping(raw or payload())
    return compile_migration_shadow(
        inventory,
        compiler_sha=COMPILER_SHA,
        branch="unit-test",
        generated_at=GENERATED_AT,
        pseudonym_salt=SALT,
    )


class MigrationInventoryTests(unittest.TestCase):
    def test_fixture_is_exact_and_compiles(self) -> None:
        result = compile_fixture()
        attestation = result.public_attestation
        self.assertEqual(attestation["state"], "SHADOW_PARITY_VERIFIED")
        self.assertEqual(attestation["parity"]["physical_count"], 4)
        self.assertEqual(attestation["parity"]["active_count"], 3)
        self.assertEqual(attestation["parity"]["alias_count"], 1)
        self.assertEqual(attestation["parity"]["entity_binding_count"], 4)
        self.assertFalse(attestation["authority_advanced"])
        self.assertEqual(attestation["h_id_allocations"], 0)
        self.assertFalse(attestation["outbound_opened"])
        self.assertEqual(attestation["send_allowed"], 0)
        self.assertEqual(len(result.private_id_map), 4)
        self.assertEqual(len(set(result.private_id_map.values())), 4)
        self.assertEqual(len(result.private_graph["hyperedges"]), 4)
        self.assertEqual(
            len([line for line in result.event_ledger_jsonl.splitlines() if line]),
            7,
        )

    def test_public_attestation_contains_no_raw_h_ids(self) -> None:
        result = compile_fixture()
        rendered = json.dumps(result.public_attestation, sort_keys=True)
        self.assertNotRegex(rendered, r"H-\d{4}")
        self.assertIn("physical_ids_sha256", rendered)
        self.assertIn("private_id_map_sha256", rendered)

    def test_compile_is_deterministic_for_same_inputs(self) -> None:
        first = compile_fixture()
        second = compile_fixture()
        self.assertEqual(first.public_attestation, second.public_attestation)
        self.assertEqual(first.private_graph, second.private_graph)
        self.assertEqual(first.private_id_map, second.private_id_map)
        self.assertEqual(first.event_ledger_jsonl, second.event_ledger_jsonl)
        self.assertEqual(first.contextpack, second.contextpack)

    def test_mismatched_active_pk_set_rejected(self) -> None:
        raw = payload()
        raw["planes"]["intelligence"]["active_ids"] = [
            "H-0001",
            "H-0002",
            "H-0003",
        ]
        with self.assertRaisesRegex(MigrationShadowError, "active PK set differs"):
            MigrationInventory.from_mapping(raw)

    def test_equal_counts_but_different_physical_pk_set_rejected(self) -> None:
        raw = payload()
        raw["planes"]["hotels_master"]["physical_ids"] = [
            "H-0001",
            "H-0002",
            "H-0003",
            "H-0005",
        ]
        with self.assertRaisesRegex(MigrationShadowError, "physical PK sets differ"):
            MigrationInventory.from_mapping(raw)

    def test_alias_edge_mismatch_rejected(self) -> None:
        raw = payload()
        raw["planes"]["operational_graph"]["alias_edges"] = []
        with self.assertRaisesRegex(MigrationShadowError, "alias edge set differs"):
            MigrationInventory.from_mapping(raw)

    def test_alias_id_cannot_remain_active(self) -> None:
        raw = payload()
        for plane in raw["planes"].values():
            plane["active_ids"] = ["H-0001", "H-0002", "H-0003", "H-0004"]
        raw["expected_active_count"] = 4
        with self.assertRaisesRegex(MigrationShadowError, "alias IDs remain"):
            MigrationInventory.from_mapping(raw)

    def test_integrity_and_foreign_keys_fail_closed(self) -> None:
        for key, value, message in (
            ("integrity_check", "corrupt", "integrity_check"),
            ("foreign_key_violations", 1, "foreign-key"),
        ):
            raw = payload()
            raw["planes"]["constrained_db"][key] = value
            with self.subTest(key=key):
                with self.assertRaisesRegex(MigrationShadowError, message):
                    MigrationInventory.from_mapping(raw)

    def test_mutable_sources_and_write_claims_rejected(self) -> None:
        raw = payload()
        raw["sources_immutable"] = False
        with self.assertRaisesRegex(MigrationShadowError, "immutable copied sources"):
            MigrationInventory.from_mapping(raw)
        raw = payload()
        raw["active_write_claims"] = [
            {"claim_id": "CLAIM:1", "scope": "authority", "mode": "WRITE"}
        ]
        with self.assertRaisesRegex(MigrationShadowError, "write claims"):
            MigrationInventory.from_mapping(raw)

    def test_any_preauthorization_is_rejected(self) -> None:
        cases = (
            ("authority_advance_allowed", True, "authority advancement"),
            ("canonical_id_allocation_allowed", True, "H-ID allocation"),
            ("outbound_allowed", True, "outbound"),
            ("outbound", "OPEN", "outbound"),
            ("send_allowed", 1, "outbound"),
        )
        for key, value, message in cases:
            raw = payload()
            raw[key] = value
            with self.subTest(key=key):
                with self.assertRaisesRegex(MigrationShadowError, message):
                    MigrationInventory.from_mapping(raw)

    def test_unsorted_and_duplicate_ids_rejected(self) -> None:
        raw = payload()
        raw["planes"]["constrained_db"]["physical_ids"] = [
            "H-0002",
            "H-0001",
            "H-0003",
            "H-0004",
        ]
        with self.assertRaisesRegex(MigrationShadowError, "sorted"):
            MigrationInventory.from_mapping(raw)
        raw = payload()
        raw["planes"]["constrained_db"]["physical_ids"] = [
            "H-0001",
            "H-0001",
            "H-0003",
            "H-0004",
        ]
        with self.assertRaisesRegex(MigrationShadowError, "duplicate"):
            MigrationInventory.from_mapping(raw)

    def test_short_or_placeholder_salt_rejected(self) -> None:
        inventory = MigrationInventory.from_mapping(payload())
        for salt in ("short", "placeholder"):
            with self.subTest(salt=salt):
                with self.assertRaises(MigrationShadowError):
                    compile_migration_shadow(
                        inventory,
                        compiler_sha=COMPILER_SHA,
                        branch="unit-test",
                        generated_at=GENERATED_AT,
                        pseudonym_salt=salt,
                    )

    def test_historical_unknown_is_preserved_not_invented(self) -> None:
        result = compile_fixture()
        historical = [
            node
            for node in result.private_graph["nodes"]
            if node["type"] == "HISTORICAL_UNKNOWN"
        ]
        self.assertEqual(len(historical), 1)
        self.assertEqual(
            historical[0]["attributes"]["reason"],
            "pre-V2 event causation is incomplete",
        )


class MigrationCompilerIntegrationTests(unittest.TestCase):
    def test_cli_emits_private_public_and_rollback_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "out"
            env = dict(os.environ)
            env["SWISS_OS_V2_PSEUDONYM_SALT"] = SALT
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/compile_graph_v2_migration_shadow.py"),
                    "--inventory",
                    str(FIXTURE),
                    "--out",
                    str(out),
                    "--compiler-sha",
                    COMPILER_SHA,
                    "--branch",
                    "unit-test",
                    "--generated-at",
                    GENERATED_AT,
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=60,
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )
            expected = {
                "public_attestation.json",
                "private_shadow_graph.json",
                "private_id_map.json",
                "contextpack.json",
                "rollback_manifest.json",
                "migration_plan.json",
                "migration_event_ledger.jsonl",
                "manifest.json",
            }
            self.assertEqual({path.name for path in out.iterdir()}, expected)
            manifest = json.loads(
                (out / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["state"], "SHADOW_PARITY_VERIFIED")
            self.assertFalse(manifest["authority_advanced"])
            self.assertEqual(manifest["h_id_allocations"], 0)
            self.assertFalse(manifest["outbound_opened"])
            self.assertEqual(manifest["send_allowed"], 0)
            self.assertFalse(
                manifest["files"]["private_id_map.json"]["public_safe"]
            )
            self.assertFalse(
                manifest["files"]["private_shadow_graph.json"]["public_safe"]
            )
            self.assertTrue(
                manifest["files"]["public_attestation.json"]["public_safe"]
            )

    def test_cli_requires_secret_salt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ)
            env.pop("SWISS_OS_V2_PSEUDONYM_SALT", None)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/compile_graph_v2_migration_shadow.py"),
                    "--inventory",
                    str(FIXTURE),
                    "--out",
                    str(Path(temp) / "out"),
                    "--compiler-sha",
                    COMPILER_SHA,
                    "--branch",
                    "unit-test",
                    "--generated-at",
                    GENERATED_AT,
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=60,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("pseudonym salt", completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()

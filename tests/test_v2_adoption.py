from __future__ import annotations

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

from swiss_os.v2_adoption import (  # noqa: E402
    AdoptionCandidate,
    AdoptionGateError,
    build_activation_receipt,
    evaluate_adoption,
)

FIXTURE = ROOT / "tests/fixtures/v2_adoption_candidate.json"


def payload() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def evaluation(raw: dict[str, object] | None = None):
    return evaluate_adoption(AdoptionCandidate.from_mapping(raw or payload()))


class AdoptionCandidateTests(unittest.TestCase):
    def test_complete_candidate_is_eligible_but_not_activated(self) -> None:
        result = evaluation()
        rendered = result.to_dict()
        self.assertEqual(rendered["state"], "ADOPTION_ELIGIBLE")
        self.assertTrue(rendered["v2_coordination_authority_allowed"])
        self.assertFalse(rendered["v2_coordination_authority_activated"])
        self.assertFalse(rendered["domain_authority_mutated"])
        self.assertEqual(rendered["h_id_allocations"], 0)
        self.assertFalse(rendered["outbound_opened"])
        self.assertEqual(rendered["send_allowed"], 0)
        self.assertEqual(
            {item["checkpoint_id"] for item in rendered["candidate"]["checkpoint_evidence"]},
            {f"CP{index}" for index in range(7, 14)},
        )

    def test_checkpoint_set_must_be_exact_and_unique(self) -> None:
        raw = payload()
        raw["cp_evidence"] = raw["cp_evidence"][:-1]
        with self.assertRaisesRegex(AdoptionGateError, "checkpoint evidence set mismatch"):
            AdoptionCandidate.from_mapping(raw)
        raw = payload()
        raw["cp_evidence"].append(dict(raw["cp_evidence"][0]))
        with self.assertRaisesRegex(AdoptionGateError, "duplicate checkpoint"):
            AdoptionCandidate.from_mapping(raw)

    def test_checkpoint_state_ancestry_and_locks_fail_closed(self) -> None:
        mutations = (
            ("state", "PROPOSED", "does not satisfy"),
            ("ancestor_verified", False, "ancestry is unverified"),
            ("authority_advanced", True, "mutated domain authority"),
            ("h_id_allocations", 1, "mutated domain authority"),
            ("outbound_opened", True, "outbound lock"),
            ("send_allowed", 1, "outbound lock"),
        )
        for key, value, message in mutations:
            raw = payload()
            raw["cp_evidence"][0][key] = value
            with self.subTest(key=key):
                with self.assertRaisesRegex(AdoptionGateError, message):
                    AdoptionCandidate.from_mapping(raw)

    def test_workflow_set_must_be_exact_successful_and_current(self) -> None:
        raw = payload()
        raw["workflow_evidence"] = raw["workflow_evidence"][:-1]
        with self.assertRaisesRegex(AdoptionGateError, "workflow evidence set mismatch"):
            AdoptionCandidate.from_mapping(raw)
        raw = payload()
        raw["workflow_evidence"][0]["state"] = "FAILURE"
        with self.assertRaisesRegex(AdoptionGateError, "did not succeed"):
            AdoptionCandidate.from_mapping(raw)
        raw = payload()
        raw["workflow_evidence"][0]["commit_sha"] = "f" * 40
        with self.assertRaisesRegex(AdoptionGateError, "not executed on current main"):
            AdoptionCandidate.from_mapping(raw)

    def test_persistence_set_must_be_exact_and_verified(self) -> None:
        raw = payload()
        raw["persistence_receipts"] = raw["persistence_receipts"][:-1]
        with self.assertRaisesRegex(AdoptionGateError, "persistence surface mismatch"):
            AdoptionCandidate.from_mapping(raw)
        raw = payload()
        raw["persistence_receipts"][0]["state"] = "PENDING"
        with self.assertRaisesRegex(AdoptionGateError, "is not verified"):
            AdoptionCandidate.from_mapping(raw)

    def test_conflicting_claim_or_pr_blocks_adoption(self) -> None:
        raw = payload()
        raw["active_conflicting_write_claims"] = [
            {"claim_id": "CLAIM:WRITE", "scope": "AGENTS.md"}
        ]
        with self.assertRaisesRegex(AdoptionGateError, "write claims"):
            AdoptionCandidate.from_mapping(raw)
        raw = payload()
        raw["open_conflicting_prs"] = [
            {"pr": 1, "paths": ["AGENTS.md"]}
        ]
        with self.assertRaisesRegex(AdoptionGateError, "conflicting PRs"):
            AdoptionCandidate.from_mapping(raw)

    def test_modes_rollback_and_domain_authority_are_mandatory(self) -> None:
        cases = (
            ("feature_mode", "OPTIONAL", "feature_mode"),
            ("compatibility_mode", "REPLACE_DOMAIN_DB", "compatibility"),
            ("adoption_scope", "ALL_AUTHORITY", "scope"),
            ("domain_authority_preserved", False, "preservation"),
            ("rollback_verified", False, "rollback"),
        )
        for key, value, message in cases:
            raw = payload()
            raw[key] = value
            with self.subTest(key=key):
                with self.assertRaisesRegex(AdoptionGateError, message):
                    AdoptionCandidate.from_mapping(raw)

    def test_any_domain_or_outbound_preauthorization_rejected(self) -> None:
        cases = (
            ("authority_advance_allowed", True),
            ("canonical_id_allocation_allowed", True),
            ("outbound_allowed", True),
            ("outbound", "OPEN"),
            ("send_allowed", 1),
        )
        for key, value in cases:
            raw = payload()
            raw[key] = value
            with self.subTest(key=key):
                with self.assertRaises(AdoptionGateError):
                    AdoptionCandidate.from_mapping(raw)

    def test_candidate_digest_is_deterministic(self) -> None:
        first = evaluation()
        second = evaluation()
        self.assertEqual(first.candidate_digest, second.candidate_digest)
        self.assertEqual(first.to_dict(), second.to_dict())


class ActivationReceiptTests(unittest.TestCase):
    def test_receipt_activates_coordination_only(self) -> None:
        result = evaluation()
        receipt = build_activation_receipt(
            result,
            activation_sha="e" * 40,
            activated_at="2026-08-30T23:00:00Z",
            agents_sha256="1" * 64,
            wop_sha256="2" * 64,
            state_sha256="3" * 64,
            next_sha256="4" * 64,
            adoption_event_hash="5" * 64,
            contextpack_digest="6" * 64,
            recovery_bundle_sha256="7" * 64,
            compatibility_wave_evidence_ref="fixture:compatibility-wave",
        )
        self.assertEqual(receipt["state"], "ADOPTED_COORDINATION_ONLY")
        self.assertTrue(receipt["v2_coordination_authority_activated"])
        self.assertTrue(receipt["domain_authority_preserved"])
        self.assertFalse(receipt["domain_authority_mutated"])
        self.assertEqual(receipt["h_id_allocations"], 0)
        self.assertFalse(receipt["outbound_opened"])
        self.assertEqual(receipt["send_allowed"], 0)
        self.assertEqual(len(receipt["receipt_digest"]), 64)

    def test_receipt_rejects_invalid_evidence_hash(self) -> None:
        with self.assertRaises(AdoptionGateError):
            build_activation_receipt(
                evaluation(),
                activation_sha="e" * 40,
                activated_at="2026-08-30T23:00:00Z",
                agents_sha256="bad",
                wop_sha256="2" * 64,
                state_sha256="3" * 64,
                next_sha256="4" * 64,
                adoption_event_hash="5" * 64,
                contextpack_digest="6" * 64,
                recovery_bundle_sha256="7" * 64,
                compatibility_wave_evidence_ref="fixture:compatibility-wave",
            )


class AdoptionCLIIntegrationTests(unittest.TestCase):
    def test_cli_emits_eligible_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "evaluation.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/evaluate_graph_v2_adoption.py"),
                    "--candidate",
                    str(FIXTURE),
                    "--out",
                    str(output),
                ],
                cwd=ROOT,
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
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["state"], "ADOPTION_ELIGIBLE")
            self.assertFalse(result["v2_coordination_authority_activated"])
            self.assertFalse(result["domain_authority_mutated"])
            self.assertEqual(result["h_id_allocations"], 0)
            self.assertFalse(result["outbound_opened"])
            self.assertEqual(result["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/state/v2/HISTORICAL_DEBT_2026-09-01.json"
AUDIT = ROOT / "docs/audits/HISTORICAL_REGRESSION_2026-09-01.md"


class HistoricalRegressionContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.audit = AUDIT.read_text(encoding="utf-8")
        cls.items = cls.payload["escaped_failures"]

    def test_unique_failure_ids(self) -> None:
        ids = [item["id"] for item in self.items]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 20)

    def test_resolved_failures_have_invariant_and_regression_protection(self) -> None:
        for item in self.items:
            if item["state"] == "RESOLVED":
                self.assertTrue(item.get("invariant"), item["id"])
                self.assertTrue(item.get("test_or_guard"), item["id"])

    def test_open_debt_has_owner_next_and_resolution_trigger(self) -> None:
        for item in self.items:
            if item["state"].startswith("OPEN"):
                self.assertTrue(item.get("owner"), item["id"])
                self.assertTrue(item.get("next"), item["id"])
                self.assertTrue(item.get("resolution_trigger"), item["id"])
                self.assertTrue(item.get("test_or_guard"), item["id"])

    def test_external_degraded_failures_are_not_marked_resolved(self) -> None:
        degraded = {item["id"] for item in self.items if item["state"] == "DEGRADED_EXTERNAL"}
        self.assertEqual(degraded, {"HDR-012", "HDR-022"})

    def test_audit_never_advances_authority_or_outbound(self) -> None:
        hard = self.payload["hard_invariants"]
        self.assertIs(hard["authority_advanced_by_this_audit"], False)
        self.assertEqual(hard["canonical_id_allocations"], 0)
        self.assertEqual(hard["canonical_id_reservations"], 0)
        self.assertIs(hard["outbound_opened"], False)
        self.assertEqual(hard["send_allowed"], 0)
        self.assertEqual(self.payload["outbound"], "CLOSED")
        self.assertIs(self.payload["crm_universe_complete"], False)

    def test_key_historical_failure_families_are_present(self) -> None:
        families = {item["family"] for item in self.items}
        required = {
            "SEMANTIC_ALIAS_CORRUPTION",
            "PAGE_POSITION_AS_SOURCE_IDENTITY",
            "STALE_BRANCH_AFTER_GREEN_CI",
            "TEST_FILE_NOT_EXECUTED",
            "SELF_REFERENTIAL_HASH_DOMAIN",
            "ROUTE_SECURITY_REJECTION_KILLS_SHARD",
            "LEXICAL_NUMERIC_SHARD_ORDER",
            "TRANSIENT_GITHUB_ARTIFACT_TRANSPORT",
            "ENTITY_GRANULARITY_COLLAPSE",
            "CRM_TERMINAL_PARITY_INCOMPLETE",
        }
        self.assertTrue(required.issubset(families))

    def test_audit_marks_history_non_authoritative_and_requires_live_recheck(self) -> None:
        self.assertIn("NON-AUTHORITATIVE", self.audit)
        self.assertIn("VERIFY LIVE TRUTH BEFORE EXECUTION", self.audit)
        self.assertIn("Historical truth is superseded, never rewritten", self.audit)


if __name__ == "__main__":
    unittest.main()

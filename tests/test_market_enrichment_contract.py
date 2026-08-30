import json
import unittest
from pathlib import Path


class MarketEnrichmentContractTests(unittest.TestCase):
    def test_run_request_is_exact_and_fail_closed(self):
        req = json.loads(Path("docs/state/market/MARKET_ENRICHMENT_RUN_REQUEST_2061_2026-08-30.json").read_text(encoding="utf-8"))
        self.assertEqual(req["source_snapshot_id"], "HS-MEMBER-DE-33206402141")
        self.assertEqual(req["source_artifact_id"], 9700376482)
        self.assertEqual(req["expected_records"], 2061)
        self.assertEqual(req["records_sha256"], "62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2")
        self.assertEqual(req["shard_count"], 42)
        self.assertEqual(req["max_parallel"], 6)
        self.assertEqual(req["outputs"]["candidate_truth_join"], "PRIVATE_PLANE_REQUIRED")
        self.assertFalse(req["safety"]["authority_advance_allowed"])
        self.assertFalse(req["safety"]["canonical_id_allocation_allowed"])
        self.assertEqual(req["safety"]["canonical_id_reservations"], 0)
        self.assertFalse(req["safety"]["crm_universe_complete"])
        self.assertEqual(req["safety"]["outbound"], "CLOSED")
        self.assertEqual(req["safety"]["send_allowed"], 0)
        self.assertEqual(req["safety"]["irreversible_external_actions"], 0)

    def test_workflow_is_bounded_and_does_not_send(self):
        workflow = Path(".github/workflows/market-enrichment-2061.yml").read_text(encoding="utf-8")
        self.assertIn("max-parallel: 6", workflow)
        self.assertIn("actions/artifacts/9700376482/zip", workflow)
        self.assertIn("--expected-records 2061", workflow)
        self.assertIn("--shard-count 42", workflow)
        self.assertIn("market-enrichment-2061.json", workflow)
        self.assertNotIn("smtp", workflow.lower())
        self.assertNotIn("sendgrid", workflow.lower())
        self.assertNotIn("mailgun", workflow.lower())


if __name__ == "__main__":
    unittest.main()

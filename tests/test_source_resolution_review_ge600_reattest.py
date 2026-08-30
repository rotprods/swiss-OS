import json
import unittest
from pathlib import Path

REATTEST = Path("docs/state/SOURCE_RESOLUTION_REVIEW_GE600_REATTEST_33206402141.json")
UNRESOLVED = Path("docs/state/SOURCE_RESOLUTION_REVIEW_UNRESOLVED_1403_33206402141.json")
EVIDENCE = Path("docs/state/SRET_HIGH_RISK20_PROVIDER_IDENTITY_33206402141.json")


class TestSourceResolutionReviewGe600Reattest(unittest.TestCase):
    def test_current_queue_reuses_exact_persisted_evidence_set_safely(self):
        r = json.loads(REATTEST.read_text(encoding="utf-8"))
        u = json.loads(UNRESOLVED.read_text(encoding="utf-8"))
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        current_keys = [item["source_record_key"] for item in u["review_priority"]["priority_ge600_items"]]
        evidence_keys = [item["source_record_key"] for item in e["items"]]
        self.assertEqual(r["identity_set"]["source_record_keys"], current_keys)
        self.assertEqual(set(current_keys), set(evidence_keys))
        self.assertEqual(len(current_keys), 20)
        self.assertEqual(r["reattestation"]["distinctness_corroborated"], 20)
        self.assertEqual(r["reattestation"]["typed_terminal_actions"], 0)
        self.assertEqual(r["reattestation"]["mapping_delta"], 0)
        self.assertEqual(r["current_mapping_frontier"]["terminal_source_mappings"], 658)
        self.assertEqual(r["current_mapping_frontier"]["reconcile_required"], 1403)
        self.assertIs(r["safety"]["authority_advanced"], False)
        self.assertEqual(r["safety"]["canonical_id_reservations"], 0)
        self.assertEqual(r["safety"]["h_id_allocations"], 0)
        self.assertEqual(r["safety"]["outbound"], "CLOSED")
        self.assertEqual(r["safety"]["send_allowed"], 0)
        self.assertIs(r["safety"]["terminal_mapping_allowed_from_distinctness"], False)


if __name__ == "__main__":
    unittest.main()

import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LINEAGE = ROOT / "docs" / "state" / "CRM_EXACT_CURRENT_CANDIDATE_LINEAGE_33339392661.json"
NEXT = ROOT / "docs" / "state" / "NEXT.json"


class CurrentCandidateLineageTest(unittest.TestCase):
    def test_lineage_is_total_reproducible_and_preauthority(self):
        payload = json.loads(LINEAGE.read_text(encoding="utf-8"))
        frontier = payload["frontier"]
        self.assertEqual(frontier["exact_unchanged_transfers"], 1436)
        self.assertEqual(frontier["changed_identity_transfers"], 2)
        self.assertEqual(frontier["candidate_lineage_accounted"], 1438)
        self.assertEqual(frontier["terminal_source_mappings"], 658)
        self.assertEqual(frontier["reconcile_required"], 1403)
        self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", payload["mapping_sha256"]))
        self.assertEqual(payload["exact_unchanged_mapping_materialization"]["mapping_sha256"], payload["mapping_sha256"])
        self.assertFalse(payload["qa"]["authority_advanced"])
        self.assertEqual(payload["qa"]["h_id_allocations"], 0)
        self.assertEqual(payload["qa"]["canonical_id_reservations"], 0)
        self.assertEqual(payload["qa"]["outbound"], "CLOSED")
        self.assertEqual(payload["qa"]["send_allowed"], 0)
        self.assertFalse(payload["qa"]["fuzzy_autobind"])

    def test_next_points_to_current_resolution_without_authority(self):
        payload = json.loads(NEXT.read_text(encoding="utf-8"))
        self.assertEqual(payload["next_route"], "CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION")
        self.assertEqual(payload["source_frontier"]["reconcile_required"], 1403)
        self.assertTrue(payload["source_frontier"]["coverage_complete"])
        self.assertFalse(payload["authority_advance_allowed"])
        self.assertFalse(payload["canonical_id_allocation_allowed"])
        self.assertFalse(payload["outbound_allowed"])
        self.assertEqual(payload["safety"]["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()

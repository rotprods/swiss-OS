import json
import unittest
from pathlib import Path

MANIFEST = Path("docs/state/CRM_MASS_ANTI_JOIN_1403_MANIFEST_33206402141.json")
STAGE = Path("docs/state/CRM_UNRESOLVED_STAGE_0001_33206402141.json")


class TestCrmMassAntiJoin1403(unittest.TestCase):
    def test_manifest_and_stage_invariants(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        s = json.loads(STAGE.read_text(encoding="utf-8"))
        a = m["anti_join"]
        self.assertEqual(m["candidate"]["records"], 1438)
        self.assertEqual(m["terminal_exceptions"]["count"], 35)
        self.assertEqual(a["unresolved_records"], 1403)
        self.assertEqual(a["unresolved_source_record_keys_sha256"], "910cfd92974025a836430612387d380be0f15d173d41f20fda6fea2bcca48581")
        self.assertIs(a["matches_full_658_unresolved_digest"], True)
        self.assertEqual(len(a["batches"]), 22)
        self.assertEqual(sum(b["records"] for b in a["batches"]), 1403)
        self.assertEqual(a["batches"][0]["records"], 64)
        self.assertEqual(a["batches"][-1]["records"], 59)
        self.assertEqual(s["records"], 64)
        self.assertEqual(s["source_record_keys_sha256"], a["batches"][0]["source_record_keys_sha256"])
        self.assertEqual(s["source_record_keys"], sorted(s["source_record_keys"]))
        self.assertIs(s["work_contract"]["allowed_terminal_decision"], False)
        self.assertIs(m["safety"]["terminal_mapping_allowed"], False)
        self.assertIs(m["safety"]["authority_advanced"], False)
        self.assertEqual(m["safety"]["canonical_id_reservations"], 0)
        self.assertEqual(m["safety"]["outbound"], "CLOSED")
        self.assertEqual(m["safety"]["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()

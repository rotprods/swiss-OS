import hashlib
import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/RAGR_CURRENT_EVIDENCE_B01_2026-08-30.json"
STATE = ROOT / "STATE.md"
NEXT = ROOT / "docs/state/NEXT.json"
WORKSET = "docs/state/RAGR34_POST_REVIEW_DISPOSITION_WORKSET_2026-08-30.json"


def _sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Ragr34B01Tests(unittest.TestCase):
    def test_exact_batch_evidence_and_fail_closed_safety(self):
        art = json.loads(ART.read_text(encoding="utf-8"))
        expected = ["H-0003","H-0016","H-0100","H-0144","H-0161","H-0192","H-0218","H-0291","H-0337","H-0352"]
        allowed = {
            "IN_SCOPE_NO_SOURCE_MATCH", "OUT_OF_SNAPSHOT_SCOPE", "SUPERSEDED/RENAMED WITH EVIDENCE",
            "COMPONENT/GROUP GRANULARITY", "DATA DEFECT", "UNRESOLVED",
        }
        self.assertEqual(art["parent_git_sha"], "e3c597b4007527e1cdb6b8895eddbb1100956200")
        self.assertEqual(art["claim"]["claim_id"], "CLAIM-CRM-SRR-SPECIAL-006")
        self.assertEqual(art["claim"]["fencing_token"], 6)
        self.assertEqual(art["batch"]["batch_id"], "RAGR34-B01")
        self.assertEqual(art["batch"]["hotel_ids"], expected)
        self.assertEqual(art["batch"]["queue_sha256"], "cf47dc91057df8653cd75729cb39320605e193e476c6828f24956b69e2848b9c")
        decisions = art["decisions"]
        self.assertEqual([d["hotel_id"] for d in decisions], expected)
        self.assertEqual(_sha(decisions), art["decisions_sha256"])
        self.assertTrue(all(d["classification"] in allowed for d in decisions))
        self.assertEqual(dict(Counter(d["classification"] for d in decisions)), {k:v for k,v in art["classification_counts"].items() if v})
        self.assertTrue(all(any(e["type"] == "CANONICAL_AUTHORITY_READBACK" and e.get("ref", "").startswith("Drive HOTELS_MASTER/HOTELS_V2!") for e in d["evidence"]) for d in decisions))
        self.assertTrue(all(any(e["type"].startswith("CURRENT_") and e.get("url", "").startswith("https://") for e in d["evidence"]) for d in decisions))
        self.assertTrue(all(d["authority_action"] == "REVIEW_ONLY_NO_MUTATION" for d in decisions))
        self.assertTrue(all(d["terminal_source_mapping_created"] is False and d["canonical_deactivation"] is False for d in decisions))
        self.assertEqual(art["review_frontier"], {"ragr_classified_before":0,"ragr_classified_after":10,"ragr_remaining_after":24,"ragr_total":34})
        self.assertEqual(art["mapping_effect"], {"reverse_authority_gaps_before":34,"reverse_authority_gaps_after":34,"terminal_mappings_before":658,"terminal_mappings_after":658})
        self.assertFalse(art["safety"]["authority_advanced"])
        self.assertEqual(art["safety"]["canonical_deactivations"], 0)
        self.assertEqual(art["safety"]["canonical_id_reservations"], 0)
        self.assertEqual(art["safety"]["h_id_allocations"], 0)
        self.assertEqual(art["safety"]["terminal_mapping_delta"], 0)
        self.assertEqual(art["safety"]["h_0691"], "UNALLOCATED")
        self.assertEqual(art["safety"]["outbound"], "CLOSED")
        self.assertEqual(art["safety"]["send_allowed"], 0)
        self.assertEqual(art["next"]["batch_id"], "RAGR34-B02")

    def test_persisted_next_advances_monotonically(self):
        text = STATE.read_text(encoding="utf-8")
        match = re.search(r"RAGR evidence-classified\s+(\d+) / 34", text)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(int(match.group(1)), 10)
        self.assertIn("H-0691 UNALLOCATED", text)
        self.assertIn("OUTBOUND                        CLOSED", text)
        nxt = json.loads(NEXT.read_text(encoding="utf-8"))
        ragr = nxt["review_frontier"]["ragr"]
        self.assertGreaterEqual(ragr["reviewed"], 10)
        self.assertLessEqual(ragr["remaining"], 24)
        self.assertEqual(ragr["reviewed"] + ragr["remaining"], 34)
        if ragr["reviewed"] < 34:
            self.assertRegex(nxt["next_route"], r"^EXECUTE_RAGR34_B0[2-4]_EVIDENCE_CLASSIFICATION$")
        else:
            self.assertEqual(ragr["reviewed"], 34)
            self.assertNotRegex(nxt["next_route"], r"^EXECUTE_RAGR34_B0[1-4]_EVIDENCE_CLASSIFICATION$")
            self.assertIn(WORKSET, nxt.get("artifacts", []))
        self.assertFalse(nxt["authority_advance_allowed"])
        self.assertFalse(nxt["outbound_allowed"])


if __name__ == "__main__":
    unittest.main()

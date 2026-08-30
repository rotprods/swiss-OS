import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_LOWER49_P1_B01_2026-08-30.json"
STATE = ROOT / "STATE.md"


def _sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Lower49B01Tests(unittest.TestCase):
    def test_exact_batch_and_fail_closed_safety(self):
        art = json.loads(ART.read_text(encoding="utf-8"))
        expected = [
            "MD-00447e4a1c8634a7711d", "MD-009d9c619a7da469e4cd", "MD-0ccac9a0d3b6144a3783",
            "MD-0f8ed600f086c0fdaa04", "MD-111c7f5cd4b1f3060482", "MD-21303c8f807f932b1609",
            "MD-29671ff37e9eb4c0f842", "MD-2f5b900fce66b8f76eef", "MD-33afe41aa0273852418b",
            "MD-3d8dd299140519ac9269",
        ]
        self.assertEqual(art["parent_git_sha"], "aa7b9964acefc5f86548cf618c3d91e3c68edaf7")
        self.assertEqual(art["claim"]["claim_id"], "CLAIM-CRM-SRR-SPECIAL-006")
        self.assertEqual(art["claim"]["fencing_token"], 6)
        self.assertEqual(art["authority"]["materialized_sha256"], "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6")
        self.assertEqual(art["batch"]["batch_id"], "L49-P1-B01")
        self.assertEqual(art["batch"]["source_record_keys"], expected)
        self.assertEqual(art["batch"]["workset_sha256"], "8817941127ede8f9329d81b4831b1fd6643e9ab4c19438c3fa612b78e1169050")
        decisions = art["decisions"]
        self.assertEqual([d["source_record_key"] for d in decisions], expected)
        self.assertEqual(_sha(decisions), art["decisions_sha256"])
        self.assertTrue(all(d["action"] == "NEW_CANONICAL" for d in decisions))
        self.assertTrue(all(d["mapping_state"] == "RECONCILE_REQUIRED" for d in decisions))
        self.assertTrue(all(d["canonical_h_id_reserved"] is False and d["h_id_allocated"] is False for d in decisions))
        self.assertTrue(all(any(e["type"] == "CURRENT_SOURCE_WEB" and e.get("url", "").startswith("https://") for e in d["evidence"]) for d in decisions))
        self.assertTrue(all(any(e["type"] == "CANONICAL_COMPARATOR_READBACK" and e.get("hotel_id") in d["suggested_hotel_ids"] for e in d["evidence"]) for d in decisions))
        self.assertTrue(all(set(d["suggested_hotel_ids"]) == {e["hotel_id"] for e in d["evidence"] if e["type"] == "CANONICAL_COMPARATOR_READBACK"} for d in decisions))
        self.assertTrue(all(any(e["type"] == "HISTORICAL_CURRENT_DISTINCTNESS_EVIDENCE_ONLY" and e["authority"] == "EVIDENCE_ONLY_NO_CURRENT_WRITE_AUTHORITY" for e in d["evidence"]) for d in decisions))
        self.assertEqual(art["review_frontier"]["lower49_typed_srr_after"], 10)
        self.assertEqual(art["review_frontier"]["lower49_remaining_after"], 37)
        self.assertEqual(art["cumulative_preauthority_frontier"]["total_new_canonical_preauth"], 77)
        self.assertEqual(art["mapping_effect"], {"reconcile_required_after": 1403, "reconcile_required_before": 1403, "terminal_mappings_after": 658, "terminal_mappings_before": 658})
        self.assertEqual(art["safety"]["h_0691"], "UNALLOCATED")
        self.assertEqual(art["safety"]["outbound"], "CLOSED")
        self.assertEqual(art["safety"]["send_allowed"], 0)
        self.assertFalse(art["safety"]["authority_advanced"])
        self.assertEqual(art["safety"]["canonical_id_reservations"], 0)
        self.assertEqual(art["safety"]["h_id_allocations"], 0)
        self.assertEqual(art["safety"]["irreversible_external_actions"], 0)

    def test_state_has_not_regressed_below_b01_frontier(self):
        text = STATE.read_text(encoding="utf-8")
        typed = re.search(r"lower49 typed SRR materialized\s+(\d+) / 47", text)
        cumulative = re.search(r"cumulative NEW_CANONICAL preauthority\s+(\d+)", text)
        self.assertIsNotNone(typed)
        self.assertIsNotNone(cumulative)
        self.assertGreaterEqual(int(typed.group(1)), 10)
        self.assertGreaterEqual(int(cumulative.group(1)), 77)
        self.assertIn("H-0691 UNALLOCATED", text)
        self.assertIn("OUTBOUND                        CLOSED", text)


if __name__ == "__main__":
    unittest.main()

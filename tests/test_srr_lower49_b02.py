import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_LOWER49_P1_B02_2026-08-30.json"
STATE = ROOT / "STATE.md"


def _sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Lower49B02Tests(unittest.TestCase):
    def test_exact_batch_and_fail_closed_safety(self):
        art = json.loads(ART.read_text(encoding="utf-8"))
        expected = [
            "MD-21cacf00a1166143f8ec", "MD-52ceb75baa65fb5de17c", "MD-582a13bd0acdcb72163c",
            "MD-59baf980dc6eace0c82d", "MD-5b615884374622a092d0", "MD-62c2d857f1a02b87e6a7",
            "MD-6541e4f795368814de02", "MD-68a026173cd82d358ecd", "MD-68dfe05e742b42831a4e",
            "MD-6caa40a9d84392fffeac",
        ]
        self.assertEqual(art["parent_git_sha"], "95a4d4acb317e996bebeeb27d5933432c9ad9599")
        self.assertEqual(art["claim"]["claim_id"], "CLAIM-CRM-SRR-SPECIAL-006")
        self.assertEqual(art["claim"]["fencing_token"], 6)
        self.assertEqual(art["authority"]["materialized_sha256"], "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6")
        self.assertEqual(art["batch"]["batch_id"], "L49-P1-B02")
        self.assertEqual(art["batch"]["source_record_keys"], expected)
        self.assertEqual(art["batch"]["workset_sha256"], "8817941127ede8f9329d81b4831b1fd6643e9ab4c19438c3fa612b78e1169050")
        self.assertEqual(art["batch"]["historical_packet_semantic_sha256"], "aecca409c25415232ec55f4780b1664b8cbb0ef30f0099bf6a81a085a07adc66")
        decisions = art["decisions"]
        self.assertEqual([d["source_record_key"] for d in decisions], expected)
        self.assertEqual(_sha(decisions), art["decisions_sha256"])
        self.assertTrue(all(d["action"] == "NEW_CANONICAL" for d in decisions))
        self.assertTrue(all(d["mapping_state"] == "RECONCILE_REQUIRED" for d in decisions))
        self.assertTrue(all(d["canonical_h_id_reserved"] is False and d["h_id_allocated"] is False for d in decisions))
        current_types = {"CURRENT_FIRST_PARTY_SOURCE", "CURRENT_PUBLIC_SOURCE"}
        self.assertTrue(all(any(e["type"] in current_types and e.get("url", "").startswith("https://") for e in d["evidence"]) for d in decisions))
        self.assertTrue(all(any(e["type"] == "CANONICAL_COMPARATOR_READBACK" and e.get("hotel_id") in d["suggested_hotel_ids"] for e in d["evidence"]) for d in decisions))
        self.assertTrue(all(set(d["suggested_hotel_ids"]) == {e["hotel_id"] for e in d["evidence"] if e["type"] == "CANONICAL_COMPARATOR_READBACK"} for d in decisions))
        self.assertTrue(all(any(e["type"] == "HISTORICAL_CURRENT_DISTINCTNESS_EVIDENCE_ONLY" and e["authority"] == "EVIDENCE_ONLY_NO_CURRENT_WRITE_AUTHORITY" for e in d["evidence"]) for d in decisions))
        self.assertEqual(art["review_frontier"]["lower49_typed_srr_before"], 10)
        self.assertEqual(art["review_frontier"]["lower49_typed_srr_after"], 20)
        self.assertEqual(art["review_frontier"]["lower49_remaining_after"], 27)
        self.assertEqual(art["cumulative_preauthority_frontier"]["total_new_canonical_preauth"], 87)
        self.assertEqual(art["mapping_effect"], {"terminal_mappings_before": 658, "terminal_mappings_after": 658, "reconcile_required_before": 1403, "reconcile_required_after": 1403})
        self.assertEqual(art["safety"]["h_0691"], "UNALLOCATED")
        self.assertEqual(art["safety"]["outbound"], "CLOSED")
        self.assertEqual(art["safety"]["send_allowed"], 0)
        self.assertFalse(art["safety"]["authority_advanced"])
        self.assertEqual(art["safety"]["canonical_id_reservations"], 0)
        self.assertEqual(art["safety"]["h_id_allocations"], 0)
        self.assertEqual(art["safety"]["irreversible_external_actions"], 0)
        self.assertEqual(art["next"]["batch_id"], "L49-P1-B03")

    def test_state_has_not_regressed_below_b02_frontier(self):
        text = STATE.read_text(encoding="utf-8")
        typed = re.search(r"lower49 typed SRR materialized\s+(\d+) / 47", text)
        cumulative = re.search(r"cumulative NEW_CANONICAL preauthority\s+(\d+)", text)
        self.assertIsNotNone(typed)
        self.assertIsNotNone(cumulative)
        self.assertGreaterEqual(int(typed.group(1)), 20)
        self.assertGreaterEqual(int(cumulative.group(1)), 87)
        self.assertIn("H-0691 UNALLOCATED", text)
        self.assertIn("OUTBOUND                        CLOSED", text)


if __name__ == "__main__":
    unittest.main()

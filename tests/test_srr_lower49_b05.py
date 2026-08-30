import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/SRR_CURRENT_IDENTITY_EVIDENCE_LOWER49_P1_B05_2026-08-30.json"
STATE = ROOT / "STATE.md"
NEXT = ROOT / "docs/state/NEXT.json"


def _sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Lower49B05Tests(unittest.TestCase):
    def test_exact_batch_and_fail_closed_safety(self):
        art = json.loads(ART.read_text(encoding="utf-8"))
        expected = [
            "MD-83df33376ee7247fb705", "MD-88fe266f7ae8e242f8e6", "MD-db1a681a0f3f4ad062ec",
            "MD-e3e74eb562bcfd8195b8", "MD-e6d5cdefc711089ae896", "MD-ec2a23d089f88b523a99",
            "MD-ee7e8cc521c970228078",
        ]
        self.assertEqual(art["parent_git_sha"], "72b7fed673f53eaf31df797051b7fe09f7cd1a7c")
        self.assertEqual(art["claim"]["claim_id"], "CLAIM-CRM-SRR-SPECIAL-006")
        self.assertEqual(art["claim"]["fencing_token"], 6)
        self.assertEqual(art["authority"]["materialized_sha256"], "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6")
        self.assertEqual(art["batch"]["batch_id"], "L49-P1-B05")
        self.assertEqual(art["batch"]["source_record_keys"], expected)
        self.assertEqual(art["batch"]["workset_sha256"], "8817941127ede8f9329d81b4831b1fd6643e9ab4c19438c3fa612b78e1169050")
        self.assertEqual(art["batch"]["historical_packet_semantic_sha256"], "7d5303337a452f0ed97eafb58d1b53732de1fcca2f9adc5a902a116035e77e1f")
        self.assertEqual(art["batch"]["reviewed_source_record_keys_sha256"], "e06a2aa0874961262003b35e4e1419710b5ee3a2d6468f9cb5707f08379affb0")
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
        self.assertEqual(art["review_frontier"], {"lower49_typed_srr_before": 40, "lower49_typed_srr_after": 47, "lower49_remaining_after": 0})
        self.assertEqual(art["cumulative_preauthority_frontier"]["total_new_canonical_preauth"], 114)
        self.assertEqual(art["mapping_effect"], {"terminal_mappings_before": 658, "terminal_mappings_after": 658, "reconcile_required_before": 1403, "reconcile_required_after": 1403})
        self.assertEqual(art["safety"]["h_0691"], "UNALLOCATED")
        self.assertEqual(art["safety"]["outbound"], "CLOSED")
        self.assertEqual(art["safety"]["send_allowed"], 0)
        self.assertFalse(art["safety"]["authority_advanced"])
        self.assertEqual(art["safety"]["canonical_id_reservations"], 0)
        self.assertEqual(art["safety"]["h_id_allocations"], 0)
        self.assertEqual(art["safety"]["irreversible_external_actions"], 0)
        self.assertEqual(art["next"]["route"], "REBUILD_TYPED_UNTYPED_CONSERVATION_AND_COMPILE_REMAINING_RECONCILE_REQUIRED_WORKSET")

    def test_state_and_canonical_next_never_regress_before_or_after_ragr(self):
        text = STATE.read_text(encoding="utf-8")
        nxt = json.loads(NEXT.read_text(encoding="utf-8"))
        typed = re.search(r"lower49 typed SRR materialized\s+(\d+) / 47", text)
        cumulative = re.search(r"cumulative NEW_CANONICAL preauthority\s+(\d+)", text)
        self.assertIsNotNone(typed)
        self.assertIsNotNone(cumulative)
        self.assertEqual(int(typed.group(1)), 47)
        self.assertGreaterEqual(int(cumulative.group(1)), 114)
        self.assertIn("H-0691 UNALLOCATED", text)
        self.assertIn("OUTBOUND                        CLOSED", text)

        # This historical test protects monotonicity, not a forever-fixed NEXT.
        # Before 34/34, NEXT must stay on the deterministic RAGR B01-B04 chain.
        # Once 34/34 is reached, any later safe route is valid as long as it never
        # regresses to a completed RAGR batch and all hard safety locks remain closed.
        route = nxt["next_route"]
        ragr = nxt["review_frontier"]["ragr"]
        self.assertEqual(ragr["total"], 34)
        self.assertGreaterEqual(ragr["reviewed"], 0)
        self.assertLessEqual(ragr["remaining"], 34)
        self.assertEqual(ragr["reviewed"] + ragr["remaining"], 34)
        if ragr["reviewed"] < 34:
            self.assertRegex(route, r"^EXECUTE_RAGR34_B0[1-4]_EVIDENCE_CLASSIFICATION$")
        else:
            self.assertEqual(ragr["reviewed"], 34)
            self.assertFalse(re.match(r"^EXECUTE_RAGR34_B0[1-4]_EVIDENCE_CLASSIFICATION$", route))
            self.assertTrue(isinstance(route, str) and route.strip())
        self.assertFalse(nxt["authority_advance_allowed"])
        self.assertFalse(nxt["canonical_id_allocation_allowed"])
        self.assertFalse(nxt["outbound_allowed"])


if __name__ == "__main__":
    unittest.main()

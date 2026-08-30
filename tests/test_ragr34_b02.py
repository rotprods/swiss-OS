import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/state/RAGR_CURRENT_EVIDENCE_B02_2026-08-30.json"
NEXT = ROOT / "docs/state/NEXT.json"
WORKSET = "docs/state/RAGR34_POST_REVIEW_DISPOSITION_WORKSET_2026-08-30.json"


def _sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class RAGR34B02Tests(unittest.TestCase):
    def test_exact_batch_classification_and_safety(self):
        art = json.loads(ART.read_text(encoding="utf-8"))
        expected = ["H-0464","H-0501","H-0521","H-0524","H-0623","H-0657","H-0659","H-0660","H-0661","H-0662"]
        self.assertEqual(art["parent_git_sha"], "30e15e4adaca971fe75b474f1bdf386359367aa5")
        self.assertEqual(art["queue"]["hotel_ids"], expected)
        self.assertEqual(art["queue"]["review_queue_sha256"], "cf47dc91057df8653cd75729cb39320605e193e476c6828f24956b69e2848b9c")
        self.assertEqual(art["claim"]["claim_id"], "CLAIM-CRM-SRR-SPECIAL-006")
        self.assertEqual(art["claim"]["fencing_token"], 6)
        decisions = art["decisions"]
        self.assertEqual([d["hotel_id"] for d in decisions], expected)
        self.assertEqual(_sha(decisions), art["decisions_sha256"])
        self.assertEqual(art["decisions_sha256"], "e8f040b2542213e9b8643b80028320cb7d5e094c44bd77e8c7cc98eb1f755178")
        self.assertEqual(sum(d["classification"] == "IN_SCOPE_NO_SOURCE_MATCH" for d in decisions), 9)
        self.assertEqual(sum(d["classification"] == "DATA DEFECT" for d in decisions), 1)
        self.assertEqual(next(d for d in decisions if d["hotel_id"] == "H-0657")["classification"], "DATA DEFECT")
        self.assertEqual(next(d for d in decisions if d["hotel_id"] == "H-0521")["classification"], "IN_SCOPE_NO_SOURCE_MATCH")
        self.assertTrue(all(d["authority_action"] == "NONE_REVIEW_ONLY" for d in decisions))
        self.assertTrue(all(d["authority_mutation_allowed"] is False for d in decisions))
        self.assertTrue(all(d["terminal_source_mapping"] == "NONE" and d["source_mapping_created"] is False for d in decisions))
        self.assertTrue(all(any(e["type"] == "CANONICAL_ROW_READBACK" for e in d["evidence"]) for d in decisions))
        self.assertTrue(all(any(e["type"].startswith("CURRENT_") for e in d["evidence"]) for d in decisions))
        self.assertEqual(art["counts"]["reviewed_before"], 10)
        self.assertEqual(art["counts"]["reviewed_after"], 20)
        self.assertEqual(art["counts"]["remaining_after"], 14)
        self.assertEqual(art["counts"]["terminal_source_mappings_created"], 0)
        self.assertEqual(art["counts"]["canonical_deactivations"], 0)
        self.assertEqual(art["counts"]["authority_mutations"], 0)
        safety = art["safety"]
        self.assertTrue(safety["review_only"])
        self.assertFalse(safety["authority_advanced"])
        self.assertFalse(safety["authority_mutation_allowed"])
        self.assertEqual(safety["terminal_source_mappings_created"], 0)
        self.assertEqual(safety["canonical_deactivations"], 0)
        self.assertEqual(safety["canonical_id_reservations"], 0)
        self.assertEqual(safety["h_id_allocations"], 0)
        self.assertEqual(safety["h_0691"], "UNALLOCATED")
        self.assertFalse(safety["crm_universe_complete"])
        self.assertEqual(safety["outbound"], "CLOSED")
        self.assertEqual(safety["send_allowed"], 0)
        self.assertEqual(safety["irreversible_external_actions"], 0)

    def test_canonical_next_advances_monotonically(self):
        nxt = json.loads(NEXT.read_text(encoding="utf-8"))
        ragr = nxt["review_frontier"]["ragr"]
        self.assertGreaterEqual(ragr["reviewed"], 20)
        self.assertLessEqual(ragr["remaining"], 14)
        self.assertEqual(ragr["reviewed"] + ragr["remaining"], 34)
        if ragr["reviewed"] < 34:
            self.assertRegex(nxt["next_route"], r"^EXECUTE_RAGR34_B0[3-4]_EVIDENCE_CLASSIFICATION$")
        else:
            self.assertEqual(ragr["reviewed"], 34)
            self.assertNotRegex(nxt["next_route"], r"^EXECUTE_RAGR34_B0[1-4]_EVIDENCE_CLASSIFICATION$")
            self.assertIn(WORKSET, nxt.get("artifacts", []))
        self.assertGreaterEqual(ragr["classification_counts"]["IN_SCOPE_NO_SOURCE_MATCH"], 13)
        self.assertGreaterEqual(ragr["classification_counts"]["DATA DEFECT"], 3)
        self.assertFalse(nxt["authority_advance_allowed"])
        self.assertFalse(nxt["canonical_id_allocation_allowed"])
        self.assertFalse(nxt["outbound_allowed"])


if __name__ == "__main__":
    unittest.main()

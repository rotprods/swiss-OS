import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSET = ROOT / "docs/operations/CRM_IDENTITY_WORKSET_LOWER49_ORDINARY_47_2026-08-30.json"


def _sha_json(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _sha_key_lines(keys):
    """Historical lower49 packet contract: ordered source keys joined by LF, no trailing LF."""
    return hashlib.sha256("\n".join(keys).encode("utf-8")).hexdigest()


class Lower49OrdinaryWorksetTests(unittest.TestCase):
    def test_exact_deterministic_and_fail_closed(self):
        workset = json.loads(WORKSET.read_text(encoding="utf-8"))
        core = dict(workset)
        claimed = core.pop("workset_sha256")
        self.assertEqual(_sha_json(core), claimed)
        self.assertEqual(claimed, "8817941127ede8f9329d81b4831b1fd6643e9ab4c19438c3fa612b78e1169050")
        self.assertEqual(workset["parent_git_sha"], "317d5892b5c80f0066a16339ed2a1f10dcdae1ef")
        self.assertEqual(workset["authority_revision"], "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6")
        self.assertEqual(workset["active_claim"]["claim_id"], "CLAIM-CRM-SRR-SPECIAL-006")
        self.assertEqual(workset["active_claim"]["fencing_token"], 6)
        self.assertEqual(workset["historical_evidence_plane"]["fencing_token"], 5)
        self.assertEqual(workset["historical_evidence_plane"]["use"], "EVIDENCE_ONLY_NO_CURRENT_WRITE_AUTHORITY")

        all_keys = []
        for batch in workset["batches"]:
            packet = json.loads((ROOT / batch["input_packet"]).read_text(encoding="utf-8"))
            self.assertEqual(packet["packet_sha256"], batch["input_packet_semantic_sha256"])
            reviews = packet["reviews"]
            self.assertEqual(len(reviews), batch["records"])
            keys = [item["source_record_key"] for item in reviews]
            self.assertEqual(_sha_key_lines(keys), batch["reviewed_source_record_keys_sha256"])
            self.assertEqual(_sha_key_lines(keys), packet["reviewed_source_record_keys_sha256"])
            self.assertTrue(all(item["review_outcome"] == "CURRENT_PUBLIC_DISTINCTNESS_SUPPORTED" for item in reviews))
            self.assertTrue(all(item["terminal_source_mapping"] == "NONE" for item in reviews))
            self.assertTrue(all(item["authority_effect"] == "NONE" for item in reviews))
            self.assertTrue(all(item["new_identity_status"] == "UNALLOCATED_PREAUTH_CANDIDATE" for item in reviews))
            all_keys.extend(keys)

        self.assertEqual([batch["records"] for batch in workset["batches"]], [10, 10, 10, 10, 7])
        self.assertEqual(len(all_keys), 47)
        self.assertEqual(len(set(all_keys)), 47)
        self.assertTrue(set(workset["selection_contract"]["special_source_record_keys"]).isdisjoint(all_keys))
        self.assertEqual(workset["selection_contract"]["ordinary_records"], 47)
        self.assertIn("DISTINCTNESS_REVIEW_IS_NOT_TYPED_SRR", workset["selection_contract"]["execution_semantics"])
        self.assertEqual(workset["safety"], {
            "authority_advanced": False,
            "canonical_id_reservations": 0,
            "h_0691": "UNALLOCATED",
            "h_id_allocations": 0,
            "irreversible_external_actions": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "terminal_mapping_delta": 0,
        })


if __name__ == "__main__":
    unittest.main()

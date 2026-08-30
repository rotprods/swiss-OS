import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSET = ROOT / "docs/state/RAGR34_POST_REVIEW_DISPOSITION_WORKSET_2026-08-30.json"
QUEUE = ROOT / "docs/state/RAGR_REVIEW_QUEUE_34_33206402141.json"
BATCHES = [
    ROOT / "docs/state/RAGR_CURRENT_EVIDENCE_B01_2026-08-30.json",
    ROOT / "docs/state/RAGR_CURRENT_EVIDENCE_B02_2026-08-30.json",
    ROOT / "docs/state/RAGR_CURRENT_EVIDENCE_B03_2026-08-30.json",
    ROOT / "docs/state/RAGR_CURRENT_EVIDENCE_B04_2026-08-30.json",
]


def _sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class RAGR34PostReviewDispositionTests(unittest.TestCase):
    def test_exact_34_row_concatenation_and_lineage(self):
        workset = json.loads(WORKSET.read_text(encoding="utf-8"))
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        batches = [json.loads(path.read_text(encoding="utf-8")) for path in BATCHES]

        expected_ids = queue["ragr"]["gap_hotel_ids"]
        rows = workset["rows"]
        self.assertEqual(len(rows), 34)
        self.assertEqual([row["ordinal"] for row in rows], list(range(1, 35)))
        self.assertEqual([row["hotel_id"] for row in rows], expected_ids)
        self.assertEqual(workset["inputs"]["review_queue_sha256"], queue["ragr"]["review_queue_sha256"])
        self.assertEqual(workset["inputs"]["queue_hotel_ids_sha256"], _sha(expected_ids))
        self.assertEqual(workset["construction"]["rows_sha256"], _sha(rows))

        source_decisions = []
        for batch in batches:
            source_decisions.extend(batch["decisions"])
        self.assertEqual([decision["hotel_id"] for decision in source_decisions], expected_ids)

        for row, decision in zip(rows, source_decisions):
            self.assertEqual(row["hotel_id"], decision["hotel_id"])
            self.assertEqual(row["canonical_name"], decision["canonical_name"])
            self.assertEqual(row["classification"], decision["classification"])
            self.assertEqual(row["reason_code"], decision["reason_code"])
            if "followup" in decision:
                self.assertEqual(row["source_followup"], decision["followup"])
                self.assertEqual(row["normalized_followup"], decision["followup"])
            else:
                self.assertIsNone(row["source_followup"])
                self.assertTrue(row["normalized_followup"])
            self.assertFalse(row["terminal_source_mapping_created"])
            self.assertEqual(row["authority_effect"], "NONE_REVIEW_ONLY")

    def test_counts_lanes_and_fail_closed_boundary(self):
        workset = json.loads(WORKSET.read_text(encoding="utf-8"))
        rows = workset["rows"]
        counts = Counter(row["classification"] for row in rows)
        lanes = Counter(row["disposition_lane"] for row in rows)
        self.assertEqual(counts, Counter({
            "IN_SCOPE_NO_SOURCE_MATCH": 24,
            "SUPERSEDED/RENAMED WITH EVIDENCE": 5,
            "DATA DEFECT": 3,
            "COMPONENT/GROUP GRANULARITY": 2,
        }))
        self.assertEqual(workset["classification_counts"]["OUT_OF_SNAPSHOT_SCOPE"], 0)
        self.assertEqual(workset["classification_counts"]["UNRESOLVED"], 0)
        self.assertEqual(lanes["SOURCE_IDENTITY_MEMBERSHIP_SEARCH"], 24)
        self.assertEqual(lanes["AUTHORITY_RENAME_AND_SOURCE_IDENTITY_REVIEW"], 5)
        self.assertEqual(lanes["AUTHORITY_STATUS_ENTITY_TYPE_REVIEW"], 3)
        self.assertEqual(lanes["AUTHORITY_GRANULARITY_COMPONENT_REVIEW"], 2)

        safety = workset["safety"]
        self.assertFalse(safety["authority_advanced"])
        self.assertFalse(safety["authority_mutation_allowed"])
        self.assertEqual(safety["terminal_source_mappings_created"], 0)
        self.assertEqual(safety["canonical_status_changes"], 0)
        self.assertEqual(safety["canonical_deactivations"], 0)
        self.assertEqual(safety["canonical_id_reservations"], 0)
        self.assertEqual(safety["h_id_allocations"], 0)
        self.assertEqual(safety["h_0691"], "UNALLOCATED")
        self.assertFalse(safety["crm_universe_complete"])
        self.assertEqual(safety["raw_reverse_authority_gaps"], 34)
        self.assertEqual(safety["outbound"], "CLOSED")
        self.assertEqual(safety["send_allowed"], 0)
        self.assertEqual(safety["irreversible_external_actions"], 0)

        special10 = [row["hotel_id"] for row in rows if row["classification"] != "IN_SCOPE_NO_SOURCE_MATCH"]
        self.assertEqual(workset["next"]["hotel_ids"], special10)
        self.assertEqual(workset["next"]["route"], "EXECUTE_RAGR34_SPECIAL10_AUTHORITY_RECONCILIATION_PREFLIGHT")
        self.assertEqual(workset["next"]["authority_effect"], "NONE_PREFLIGHT_ONLY")


if __name__ == "__main__":
    unittest.main()

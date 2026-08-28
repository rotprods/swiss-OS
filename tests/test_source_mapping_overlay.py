from __future__ import annotations

import unittest

from swiss_os.source_mapping_overlay import build_match_existing_overlay, validate_overlay, SourceMappingOverlayError


REVIEWS = {
    "schema_version": "SOURCE-RESOLUTION-EXPLICIT-REVIEWS-1.0",
    "source_snapshot_id": "SNAP",
    "review_state": "READY_FOR_SRR_APPLICATION",
    "reviews_count": 2,
    "reviews": [
        {"source_record_key":"MD-2","action":"MATCH_EXISTING","canonical_hotel_id":"H-0002","current_evidence_verified":True,"authority_action":"NONE_PREAUTH_REVIEW","evidence_ref":"E2","reason_code":"R2"},
        {"source_record_key":"MD-1","action":"MATCH_EXISTING","canonical_hotel_id":"H-0001","current_evidence_verified":True,"authority_action":"NONE_PREAUTH_REVIEW","evidence_ref":"E1","reason_code":"R1"},
    ],
}


class SourceMappingOverlayTests(unittest.TestCase):
    def build(self):
        return build_match_existing_overlay(REVIEWS, snapshot_id="SNAP", base_candidate_sha256="a"*64, base_source_records=10, base_terminal_mappings=3, base_reconcile_required=7)

    def test_builds_deterministic_safe_overlay(self):
        payload = self.build()
        self.assertEqual(payload["effective_terminal_mappings"], 5)
        self.assertEqual(payload["effective_reconcile_required"], 5)
        self.assertEqual([d["source_record_key"] for d in payload["terminal_deltas"]], ["MD-1", "MD-2"])
        self.assertEqual(validate_overlay(payload), ())
        self.assertFalse(payload["authority_advanced"])
        self.assertEqual(payload["h_id_allocations"], 0)
        self.assertEqual(payload["outbound"], "CLOSED")
        self.assertEqual(payload["send_allowed"], 0)

    def test_rejects_unverified_review(self):
        raw = {**REVIEWS, "reviews": [dict(REVIEWS["reviews"][0], current_evidence_verified=False)], "reviews_count": 1}
        with self.assertRaises(SourceMappingOverlayError):
            build_match_existing_overlay(raw, snapshot_id="SNAP", base_candidate_sha256="a"*64, base_source_records=10, base_terminal_mappings=3, base_reconcile_required=7)

    def test_rejects_allocate_or_non_match_action(self):
        raw = {**REVIEWS, "reviews": [dict(REVIEWS["reviews"][0], action="CREATE_NEW")], "reviews_count": 1}
        with self.assertRaises(SourceMappingOverlayError):
            build_match_existing_overlay(raw, snapshot_id="SNAP", base_candidate_sha256="a"*64, base_source_records=10, base_terminal_mappings=3, base_reconcile_required=7)

    def test_validation_rejects_safety_regression(self):
        payload = self.build()
        payload["h_id_allocations"] = 1
        self.assertIn("H_ID_ALLOCATIONS_FORBIDDEN", validate_overlay(payload))

    def test_rejects_duplicate_source_key(self):
        raw = {**REVIEWS, "reviews": [REVIEWS["reviews"][0], REVIEWS["reviews"][0]], "reviews_count": 2}
        with self.assertRaises(SourceMappingOverlayError):
            build_match_existing_overlay(raw, snapshot_id="SNAP", base_candidate_sha256="a"*64, base_source_records=10, base_terminal_mappings=3, base_reconcile_required=7)


if __name__ == "__main__":
    unittest.main()

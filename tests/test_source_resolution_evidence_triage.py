from __future__ import annotations

import copy
import unittest

from swiss_os.source_resolution_evidence_triage import (
    AMBIGUOUS_REVIEW,
    EVIDENCE_PENDING,
    MATCH_EXISTING_REVIEW,
    NOVELTY_REVIEW,
    SourceResolutionEvidenceTriageError,
    build_evidence_triage,
    validate_evidence_triage,
)


class SourceResolutionEvidenceTriageTests(unittest.TestCase):
    def _mapping(self):
        return {
            "snapshot_id": "HS-TEST",
            "source_manifest_sha256": "f" * 64,
            "candidate_sha256": "a" * 64,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "mappings": [
                {
                    "source_record_key": "hs:0",
                    "name": "Carried Hotel",
                    "city": "Bern",
                    "detail_url": "https://source.example/carried",
                    "mapping_state": "ACTIVE_CANONICAL",
                    "canonical_hotel_id": "H-0001",
                    "current_evidence_verified": True,
                },
                {
                    "source_record_key": "hs:1",
                    "name": "Exact Hotel",
                    "city": "Zurich",
                    "detail_url": "https://source.example/exact",
                    "mapping_state": "RECONCILE_REQUIRED",
                    "canonical_hotel_id": "",
                    "current_evidence_verified": True,
                },
                {
                    "source_record_key": "hs:2",
                    "name": "Common Name",
                    "city": "Chur",
                    "detail_url": "https://source.example/common",
                    "mapping_state": "RECONCILE_REQUIRED",
                    "canonical_hotel_id": "",
                    "current_evidence_verified": True,
                },
                {
                    "source_record_key": "hs:3",
                    "name": "Brand New Lodge",
                    "city": "Luzern",
                    "detail_url": "https://source.example/new",
                    "mapping_state": "RECONCILE_REQUIRED",
                    "canonical_hotel_id": "",
                    "current_evidence_verified": True,
                },
                {
                    "source_record_key": "hs:4",
                    "name": "Evidence Pending",
                    "city": "Basel",
                    "detail_url": "https://source.example/pending",
                    "mapping_state": "RECONCILE_REQUIRED",
                    "canonical_hotel_id": "",
                    "current_evidence_verified": False,
                },
            ],
        }

    def _catalog(self):
        return {
            "hotels": [
                {"hotel_id": "H-0001", "name": "Carried Hotel", "city": "Bern", "detail_url": "https://canonical.example/carried", "is_active": True},
                {"hotel_id": "H-0002", "name": "Exact Hotel", "city": "Zurich", "detail_url": "https://canonical.example/exact", "is_active": True},
                {"hotel_id": "H-0003", "name": "Common Name", "city": "Luzern", "detail_url": "https://canonical.example/common", "is_active": True},
                {"hotel_id": "H-0004", "name": "Exact Lodge Zurich", "city": "Zurich", "detail_url": "https://canonical.example/other", "is_active": True},
            ]
        }

    def test_partition_is_review_only_and_never_allocates(self):
        result = build_evidence_triage(self._mapping(), self._catalog())
        self.assertEqual(result["carried_terminal_mappings"], 1)
        self.assertEqual(result["triage_records"], 4)
        self.assertFalse(result["terminal_mapping_allowed"])
        self.assertFalse(result["canonical_id_reservation_allowed"])
        self.assertFalse(result["authority_advanced"])
        self.assertEqual(result["h_id_allocations"], 0)
        self.assertEqual(result["outbound"], "CLOSED")
        self.assertEqual(result["send_allowed"], 0)
        self.assertEqual(validate_evidence_triage(result), ())

    def test_exact_name_city_is_match_review_not_terminal_mapping(self):
        result = build_evidence_triage(self._mapping(), self._catalog())
        item = next(x for x in result["items"] if x["source_record_key"] == "hs:1")
        self.assertEqual(item["triage_state"], MATCH_EXISTING_REVIEW)
        self.assertEqual(item["exact_signal_hotel_ids"], ["H-0002"])
        self.assertFalse(item["terminal_mapping_allowed"])
        self.assertEqual(item["authority_action"], "NONE")
        self.assertNotIn("canonical_hotel_id", item)

    def test_exact_global_name_locality_conflict_is_ambiguous(self):
        result = build_evidence_triage(self._mapping(), self._catalog())
        item = next(x for x in result["items"] if x["source_record_key"] == "hs:2")
        self.assertEqual(item["triage_state"], AMBIGUOUS_REVIEW)
        self.assertEqual(item["exact_signal_hotel_ids"], ["H-0003"])
        self.assertIn("LOCALITY_CONFLICT", item["reason_code"])

    def test_current_verified_no_exact_signal_is_novelty_review_not_new_canonical(self):
        result = build_evidence_triage(self._mapping(), self._catalog())
        item = next(x for x in result["items"] if x["source_record_key"] == "hs:3")
        self.assertEqual(item["triage_state"], NOVELTY_REVIEW)
        self.assertIn("DISTINCTNESS_UNPROVEN", item["reason_code"])
        self.assertFalse(item["canonical_id_reservation_allowed"])
        self.assertEqual(item["authority_action"], "NONE")

    def test_missing_current_evidence_stays_pending(self):
        result = build_evidence_triage(self._mapping(), self._catalog())
        item = next(x for x in result["items"] if x["source_record_key"] == "hs:4")
        self.assertEqual(item["triage_state"], EVIDENCE_PENDING)

    def test_similarity_is_suggestion_only(self):
        mapping = self._mapping()
        source = next(x for x in mapping["mappings"] if x["source_record_key"] == "hs:3")
        source["name"] = "Exact Lodge"
        source["city"] = "Zurich"
        result = build_evidence_triage(mapping, self._catalog())
        item = next(x for x in result["items"] if x["source_record_key"] == "hs:3")
        self.assertEqual(item["triage_state"], NOVELTY_REVIEW)
        self.assertTrue(item["candidate_suggestions"])
        self.assertTrue(all(x["evidence_role"] == "REVIEW_SPACE_REDUCTION_ONLY" for x in item["candidate_suggestions"]))
        self.assertFalse(item["terminal_mapping_allowed"])

    def test_tampering_with_authority_semantics_fails_validation(self):
        result = build_evidence_triage(self._mapping(), self._catalog())
        tampered = copy.deepcopy(result)
        tampered["items"][0]["canonical_hotel_id"] = "H-9999"
        violations = validate_evidence_triage(tampered)
        self.assertIn("ITEM_CANONICAL_TARGET_FORBIDDEN", violations)
        self.assertIn("ITEMS_SHA_MISMATCH", violations)
        self.assertIn("TRIAGE_SHA_MISMATCH", violations)

    def test_duplicate_source_key_fails_closed(self):
        mapping = self._mapping()
        mapping["mappings"].append(copy.deepcopy(mapping["mappings"][1]))
        with self.assertRaisesRegex(SourceResolutionEvidenceTriageError, "duplicate source_record_key"):
            build_evidence_triage(mapping, self._catalog())

    def test_non_boolean_catalog_activity_fails_closed(self):
        catalog = self._catalog()
        catalog["hotels"][0]["is_active"] = "true"
        with self.assertRaisesRegex(SourceResolutionEvidenceTriageError, "is_active must be boolean"):
            build_evidence_triage(self._mapping(), catalog)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import unittest

from swiss_os.source_mapping import build_source_mapping_candidate
from swiss_os.source_resolution import (
    SourceResolutionError,
    build_resolution_review,
    validate_resolution_review,
)


class SourceResolutionTests(unittest.TestCase):
    def _smc(self):
        cmi = {
            "decisions": [
                {
                    "source_record_key": "hs:1",
                    "raw_name": "Existing Hotel",
                    "raw_city": "Bern",
                    "detail_url": "https://www.hotelleriesuisse.ch/de/x/hotel-existing-hotel",
                    "decision": "MATCHED_EXISTING",
                    "matched_hotel_id": "H-0001",
                },
                {
                    "source_record_key": "hs:2",
                    "raw_name": "Variant Hôtel",
                    "raw_city": "Zürich",
                    "detail_url": "https://www.hotelleriesuisse.ch/de/x/hotel-variant-hotel?tracking=x",
                    "decision": "VERIFY_NEW_ENTITY",
                },
                {
                    "source_record_key": "hs:3",
                    "raw_name": "Brand New Lodge",
                    "raw_city": "Luzern",
                    "detail_url": "https://www.hotelleriesuisse.ch/de/x/hotel-brand-new-lodge",
                    "decision": "VERIFY_NEW_ENTITY",
                },
                {
                    "source_record_key": "hs:4",
                    "raw_name": "Weak Evidence",
                    "raw_city": "Basel",
                    "detail_url": "https://www.hotelleriesuisse.ch/de/x/hotel-weak-evidence",
                    "decision": "VERIFY_NEW_ENTITY",
                },
            ]
        }
        verified = [
            {
                "source_record_key": "hs:2",
                "verification_state": "CURRENT_DETAIL_VERIFIED",
                "response_sha256": "a" * 64,
            },
            {
                "source_record_key": "hs:3",
                "verification_state": "CURRENT_DETAIL_VERIFIED",
                "response_sha256": "b" * 64,
            },
        ]
        requeue = [
            {
                "source_record_key": "hs:4",
                "verification_state": "FETCH_FAILED",
                "response_sha256": "",
            }
        ]
        return build_source_mapping_candidate(
            cmi,
            verified,
            requeue,
            snapshot_id="HS-TEST",
            source_manifest_sha256="f" * 64,
        )

    def _catalog(self):
        return [
            {
                "hotel_id": "H-0001",
                "name": "Existing Hotel",
                "city": "Bern",
                "detail_url": "https://www.hotelleriesuisse.ch/de/x/hotel-existing-hotel",
                "is_active": True,
            },
            {
                "hotel_id": "H-0002",
                "name": "Variant Hotel",
                "city": "Zurich",
                "detail_url": "https://www.hotelleriesuisse.ch/de/x/hotel-variant-hotel",
                "is_active": True,
            },
        ]

    def test_auto_proposal_carries_existing_matches_and_resolves_unique_detail(self):
        result = build_resolution_review(self._smc(), self._catalog())
        by_key = {item["source_record_key"]: item for item in result["mappings"]}
        self.assertEqual(by_key["hs:1"]["mapping_state"], "ACTIVE_CANONICAL")
        self.assertEqual(by_key["hs:1"]["resolution_action"], "CARRY_TERMINAL")
        self.assertEqual(by_key["hs:2"]["mapping_state"], "ACTIVE_CANONICAL")
        self.assertEqual(by_key["hs:2"]["canonical_hotel_id"], "H-0002")
        self.assertEqual(by_key["hs:2"]["resolution_reason_code"], "UNIQUE_EXACT_DETAIL_URL_MATCH")

    def test_auto_proposal_new_canonical_never_allocates_id(self):
        result = build_resolution_review(self._smc(), self._catalog())
        by_key = {item["source_record_key"]: item for item in result["mappings"]}
        new_item = by_key["hs:3"]
        self.assertEqual(new_item["resolution_action"], "NEW_CANONICAL")
        self.assertEqual(new_item["mapping_state"], "RECONCILE_REQUIRED")
        self.assertEqual(new_item["canonical_hotel_id"], "")
        self.assertEqual(new_item["authority_action"], "ALLOCATE_NEW_CANONICAL_ON_AUTHORITY_COMMIT")
        self.assertEqual(result["h_id_allocations"], 0)
        self.assertFalse(result["authority_advanced"])

    def test_weak_evidence_remains_unresolved(self):
        result = build_resolution_review(self._smc(), self._catalog())
        by_key = {item["source_record_key"]: item for item in result["mappings"]}
        self.assertEqual(by_key["hs:4"]["resolution_action"], "UNRESOLVED")
        self.assertEqual(by_key["hs:4"]["mapping_state"], "RECONCILE_REQUIRED")
        self.assertEqual(result["unresolved_review"], 1)
        self.assertFalse(result["authority_batch_ready"])

    def test_explicit_alias_requires_active_target_and_current_evidence(self):
        reviews = [
            {
                "source_record_key": "hs:2",
                "action": "ALIAS_EXISTING",
                "canonical_hotel_id": "H-0002",
                "reason_code": "EXPLICIT_VARIANT_ALIAS",
                "evidence_ref": "review:e1",
            }
        ]
        result = build_resolution_review(self._smc(), self._catalog(), reviews)
        item = next(x for x in result["mappings"] if x["source_record_key"] == "hs:2")
        self.assertEqual(item["mapping_state"], "ALIAS_TO_CANONICAL")
        self.assertEqual(item["canonical_hotel_id"], "H-0002")
        self.assertEqual(item["resolution_origin"], "EXPLICIT_REVIEW")

    def test_explicit_exclusion_is_terminal_candidate_but_not_authority(self):
        reviews = [
            {
                "source_record_key": "hs:4",
                "action": "EXCLUDE",
                "reason_code": "NOT_TARGET_ACCOMMODATION_SCOPE",
                "evidence_ref": "source-scope:card-4",
            }
        ]
        result = build_resolution_review(self._smc(), self._catalog(), reviews)
        item = next(x for x in result["mappings"] if x["source_record_key"] == "hs:4")
        self.assertEqual(item["mapping_state"], "EXCLUDED_WITH_REASON")
        self.assertEqual(item["canonical_hotel_id"], "")
        self.assertFalse(result["crm_universe_complete"])
        self.assertEqual(result["outbound"], "CLOSED")
        self.assertEqual(result["send_allowed"], 0)

    def test_review_cannot_rewrite_terminal_smc_match(self):
        reviews = [
            {
                "source_record_key": "hs:1",
                "action": "EXCLUDE",
                "reason_code": "BAD_OVERRIDE",
                "evidence_ref": "review:x",
            }
        ]
        with self.assertRaisesRegex(SourceResolutionError, "only target RECONCILE_REQUIRED"):
            build_resolution_review(self._smc(), self._catalog(), reviews)

    def test_unknown_review_key_fails_closed(self):
        reviews = [
            {
                "source_record_key": "hs:999",
                "action": "UNRESOLVED",
                "reason_code": "UNKNOWN",
                "evidence_ref": "review:x",
            }
        ]
        with self.assertRaisesRegex(SourceResolutionError, "unknown source keys"):
            build_resolution_review(self._smc(), self._catalog(), reviews)

    def test_match_target_must_exist_and_be_active(self):
        reviews = [
            {
                "source_record_key": "hs:2",
                "action": "MATCH_EXISTING",
                "canonical_hotel_id": "H-9999",
                "reason_code": "MANUAL_MATCH",
                "evidence_ref": "review:x",
            }
        ]
        with self.assertRaisesRegex(SourceResolutionError, "must exist and be active"):
            build_resolution_review(self._smc(), self._catalog(), reviews)

    def test_new_canonical_requires_current_exact_evidence(self):
        reviews = [
            {
                "source_record_key": "hs:4",
                "action": "NEW_CANONICAL",
                "reason_code": "NEW_PROPERTY",
                "evidence_ref": "review:x",
            }
        ]
        with self.assertRaisesRegex(SourceResolutionError, "current exact evidence required"):
            build_resolution_review(self._smc(), self._catalog(), reviews)

    def test_ambiguous_catalog_match_fails_to_unresolved_not_first_match(self):
        catalog = self._catalog() + [
            {
                "hotel_id": "H-0003",
                "name": "Other Name",
                "city": "Zürich",
                "detail_url": "https://www.hotelleriesuisse.ch/de/x/hotel-variant-hotel",
                "is_active": True,
            }
        ]
        result = build_resolution_review(self._smc(), catalog)
        item = next(x for x in result["mappings"] if x["source_record_key"] == "hs:2")
        self.assertEqual(item["resolution_action"], "UNRESOLVED")
        self.assertEqual(item["resolution_reason_code"], "AMBIGUOUS_EXACT_DETAIL_URL_MATCH")
        self.assertEqual(item["canonical_hotel_id"], "")

    def test_catalog_boolean_is_strict(self):
        catalog = self._catalog()
        catalog[0]["is_active"] = "true"
        with self.assertRaisesRegex(SourceResolutionError, "is_active must be boolean"):
            build_resolution_review(self._smc(), catalog)

    def test_smc_pre_authority_booleans_are_strict(self):
        smc = self._smc()
        smc["authority_advanced"] = 0
        with self.assertRaisesRegex(SourceResolutionError, "authority_advanced must be exactly False"):
            build_resolution_review(smc, self._catalog())

    def test_output_validator_detects_tampering(self):
        result = build_resolution_review(self._smc(), self._catalog())
        self.assertEqual(validate_resolution_review(result), ())
        tampered = copy.deepcopy(result)
        tampered["mappings"][0]["name"] = "tampered"
        violations = validate_resolution_review(tampered)
        self.assertIn("MAPPINGS_SHA_MISMATCH", violations)
        self.assertIn("REVIEW_SHA_MISMATCH", violations)

    def test_complete_explicit_reviews_distinguishes_review_from_authority_completion(self):
        reviews = [
            {
                "source_record_key": "hs:2",
                "action": "MATCH_EXISTING",
                "canonical_hotel_id": "H-0002",
                "reason_code": "EXACT_DETAIL_MATCH",
                "evidence_ref": "review:2",
            },
            {
                "source_record_key": "hs:3",
                "action": "NEW_CANONICAL",
                "reason_code": "CURRENT_NEW_PROPERTY",
                "evidence_ref": "review:3",
            },
            {
                "source_record_key": "hs:4",
                "action": "EXCLUDE",
                "reason_code": "OUT_OF_SCOPE",
                "evidence_ref": "review:4",
            },
        ]
        result = build_resolution_review(self._smc(), self._catalog(), reviews)
        self.assertTrue(result["explicit_review_complete"])
        self.assertTrue(result["review_decision_complete"])
        self.assertTrue(result["authority_batch_ready"])
        self.assertEqual(result["new_canonical_candidates"], 1)
        self.assertEqual(result["reconcile_required_after_review"], 1)
        self.assertFalse(result["crm_universe_complete"])
        self.assertFalse(result["authority_advanced"])
        self.assertEqual(result["h_id_allocations"], 0)


if __name__ == "__main__":
    unittest.main()

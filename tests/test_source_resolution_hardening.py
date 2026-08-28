from __future__ import annotations

import copy
import unittest

from swiss_os.source_mapping import build_source_mapping_candidate
from swiss_os.source_resolution import (
    SourceResolutionError,
    build_resolution_review,
    validate_resolution_review,
)


def _smc() -> dict[str, object]:
    cmi = {
        "decisions": [
            {
                "source_record_key": "hs:2",
                "raw_name": "Variant Hotel",
                "raw_city": "Zürich",
                "detail_url": "https://www.hotelleriesuisse.ch/de/x/hotel-variant-hotel",
                "decision": "VERIFY_NEW_ENTITY",
            },
            {
                "source_record_key": "hs:3",
                "raw_name": "Brand New Lodge",
                "raw_city": "Luzern",
                "detail_url": "https://www.hotelleriesuisse.ch/de/x/hotel-brand-new-lodge",
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
    return build_source_mapping_candidate(
        cmi,
        verified,
        [],
        snapshot_id="HS-HARDENING",
        source_manifest_sha256="f" * 64,
    )


def _catalog() -> list[dict[str, object]]:
    return [
        {
            "hotel_id": "H-0002",
            "name": "Variant Hotel",
            "city": "Zurich",
            "detail_url": "https://www.hotelleriesuisse.ch/de/x/hotel-variant-hotel",
            "is_active": True,
        }
    ]


class SourceResolutionHardeningTests(unittest.TestCase):
    def test_catalog_requires_explicit_is_active_presence(self) -> None:
        catalog = _catalog()
        del catalog[0]["is_active"]
        with self.assertRaisesRegex(SourceResolutionError, "explicitly present"):
            build_resolution_review(_smc(), catalog)

    def test_review_scalars_do_not_coerce_numbers_to_strings(self) -> None:
        reviews = [
            {
                "source_record_key": "hs:2",
                "action": 123,
                "canonical_hotel_id": "H-0002",
                "reason_code": "MATCH",
                "evidence_ref": "review:e1",
            }
        ]
        with self.assertRaisesRegex(SourceResolutionError, "action must be a string"):
            build_resolution_review(_smc(), _catalog(), reviews)

    def test_reason_and_evidence_review_scalars_are_strict(self) -> None:
        reviews = [
            {
                "source_record_key": "hs:2",
                "action": "MATCH_EXISTING",
                "canonical_hotel_id": "H-0002",
                "reason_code": 7,
                "evidence_ref": "review:e1",
            }
        ]
        with self.assertRaisesRegex(SourceResolutionError, "reason_code must be a string"):
            build_resolution_review(_smc(), _catalog(), reviews)

    def test_transfer_validator_rejects_impossible_action_transition(self) -> None:
        result = build_resolution_review(_smc(), _catalog())
        tampered = copy.deepcopy(result)
        item = next(x for x in tampered["mappings"] if x["source_record_key"] == "hs:3")
        self.assertEqual(item["resolution_action"], "NEW_CANONICAL")
        item["mapping_state"] = "ACTIVE_CANONICAL"
        violations = validate_resolution_review(tampered)
        self.assertIn("INVALID_ACTION_MAPPING_TRANSITION", violations)

    def test_transfer_validator_rejects_existing_action_without_current_evidence(self) -> None:
        result = build_resolution_review(_smc(), _catalog())
        tampered = copy.deepcopy(result)
        item = next(x for x in tampered["mappings"] if x["source_record_key"] == "hs:2")
        self.assertEqual(item["resolution_action"], "MATCH_EXISTING")
        item["current_evidence_verified"] = False
        violations = validate_resolution_review(tampered)
        self.assertIn("EXISTING_ACTION_REQUIRES_CURRENT_EVIDENCE", violations)

    def test_authority_batch_ready_is_strict_boolean_and_recomputed(self) -> None:
        result = build_resolution_review(_smc(), _catalog())
        tampered = copy.deepcopy(result)
        tampered["authority_batch_ready"] = "true"
        violations = validate_resolution_review(tampered)
        self.assertIn("AUTHORITY_BATCH_READY_MISMATCH", violations)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import unittest

from swiss_os.source_mapping import build_source_mapping_candidate
from swiss_os.source_resolution import SourceResolutionError
from swiss_os.source_resolution_batch_safe import (
    build_batch_safe_resolution_review,
    validate_batch_safe_resolution_review,
)


SNAPSHOT = "HS-BATCH-SAFE"


def _smc() -> dict[str, object]:
    cmi = {
        "decisions": [
            {
                "source_record_key": "hs:victoria",
                "raw_name": "Victoria – Alpine Boutique Hotel & Fine Dining",
                "raw_city": "Meiringen",
                "detail_url": "https://source.example/victoria-alpine",
                "decision": "VERIFY_NEW_ENTITY",
            },
            {
                "source_record_key": "hs:river",
                "raw_name": "River Pearl Lodge",
                "raw_city": "Meiringen",
                "detail_url": "https://source.example/river-pearl",
                "decision": "VERIFY_NEW_ENTITY",
            },
            {
                "source_record_key": "hs:exact",
                "raw_name": "Exact Hotel",
                "raw_city": "Zürich",
                "detail_url": "https://source.example/exact",
                "decision": "VERIFY_NEW_ENTITY",
            },
        ]
    }
    verified = [
        {
            "source_record_key": "hs:victoria",
            "verification_state": "CURRENT_DETAIL_VERIFIED",
            "response_sha256": "a" * 64,
        },
        {
            "source_record_key": "hs:river",
            "verification_state": "CURRENT_DETAIL_VERIFIED",
            "response_sha256": "b" * 64,
        },
        {
            "source_record_key": "hs:exact",
            "verification_state": "CURRENT_DETAIL_VERIFIED",
            "response_sha256": "c" * 64,
        },
    ]
    return build_source_mapping_candidate(
        cmi,
        verified,
        [],
        snapshot_id=SNAPSHOT,
        source_manifest_sha256="f" * 64,
    )


def _catalog() -> list[dict[str, object]]:
    return [
        {
            "hotel_id": "H-0686",
            "name": "Victoria Boutique Hotel & Fine Dining",
            "city": "Meiringen",
            "detail_url": "https://canonical.example/victoria",
            "is_active": True,
        },
        {
            "hotel_id": "H-0100",
            "name": "Exact Hotel",
            "city": "Zurich",
            "detail_url": "https://canonical.example/exact",
            "is_active": True,
        },
    ]


class BatchSafeSourceResolutionTests(unittest.TestCase):
    def test_same_city_name_variant_fails_closed_instead_of_new_canonical(self) -> None:
        result = build_batch_safe_resolution_review(
            _smc(), _catalog(), expected_snapshot_id=SNAPSHOT
        )
        victoria = next(
            row for row in result["mappings"] if row["source_record_key"] == "hs:victoria"
        )
        self.assertEqual(victoria["resolution_action"], "UNRESOLVED")
        self.assertEqual(
            victoria["resolution_reason_code"],
            "SAME_CITY_DUPLICATE_RISK_REVIEW_REQUIRED",
        )
        self.assertEqual(victoria["canonical_hotel_id"], "")
        self.assertEqual(victoria["resolution_candidate_hotel_ids"], ["H-0686"])
        self.assertEqual(victoria["mapping_state"], "RECONCILE_REQUIRED")
        self.assertEqual(
            victoria["authority_action"], "RESEARCH_OR_MANUAL_REVIEW_REQUIRED"
        )
        self.assertFalse(result["authority_batch_ready"])

    def test_distinct_same_city_current_entity_remains_new_canonical_candidate(self) -> None:
        result = build_batch_safe_resolution_review(_smc(), _catalog())
        river = next(
            row for row in result["mappings"] if row["source_record_key"] == "hs:river"
        )
        self.assertEqual(river["resolution_action"], "NEW_CANONICAL")
        self.assertEqual(river["canonical_hotel_id"], "")
        self.assertEqual(river["mapping_state"], "RECONCILE_REQUIRED")

    def test_exact_name_city_match_keeps_exact_match_precedence(self) -> None:
        result = build_batch_safe_resolution_review(_smc(), _catalog())
        exact = next(
            row for row in result["mappings"] if row["source_record_key"] == "hs:exact"
        )
        self.assertEqual(exact["resolution_action"], "MATCH_EXISTING")
        self.assertEqual(exact["canonical_hotel_id"], "H-0100")
        self.assertEqual(exact["mapping_state"], "ACTIVE_CANONICAL")

    def test_snapshot_mismatch_fails_before_classification(self) -> None:
        with self.assertRaisesRegex(SourceResolutionError, "snapshot mismatch"):
            build_batch_safe_resolution_review(
                _smc(), _catalog(), expected_snapshot_id="OTHER-SNAPSHOT"
            )

    def test_validator_rejects_fuzzy_autobind_enablement(self) -> None:
        result = build_batch_safe_resolution_review(_smc(), _catalog())
        tampered = copy.deepcopy(result)
        tampered["batch_safe_resolver"]["fuzzy_autobind_allowed"] = True
        self.assertIn(
            "FUZZY_AUTOBIND_MUST_BE_FALSE",
            validate_batch_safe_resolution_review(tampered, _catalog()),
        )

    def test_validator_rejects_reintroduced_auto_new_canonical_duplicate_risk(self) -> None:
        result = build_batch_safe_resolution_review(_smc(), _catalog())
        tampered = copy.deepcopy(result)
        victoria = next(
            row
            for row in tampered["mappings"]
            if row["source_record_key"] == "hs:victoria"
        )
        victoria["resolution_action"] = "NEW_CANONICAL"
        victoria["resolution_reason_code"] = "CURRENT_VERIFIED_NO_CANONICAL_MATCH"
        victoria["resolution_candidate_hotel_ids"] = []
        violations = validate_batch_safe_resolution_review(tampered, _catalog())
        self.assertIn("AUTO_NEW_CANONICAL_HAS_SAME_CITY_DUPLICATE_RISK", violations)

    def test_hard_safety_invariants_remain_closed(self) -> None:
        result = build_batch_safe_resolution_review(_smc(), _catalog())
        self.assertIs(result["authority_advanced"], False)
        self.assertEqual(result["h_id_allocations"], 0)
        self.assertIs(result["crm_universe_complete"], False)
        self.assertEqual(result["outbound"], "CLOSED")
        self.assertEqual(result["send_allowed"], 0)
        self.assertIs(
            result["batch_safe_resolver"]["canonical_id_reservation_allowed"], False
        )
        self.assertEqual(validate_batch_safe_resolution_review(result, _catalog()), ())


if __name__ == "__main__":
    unittest.main()

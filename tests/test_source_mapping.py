from __future__ import annotations

import copy
import unittest

from swiss_os.source_mapping import (
    SourceMappingError,
    build_source_mapping_candidate,
    validate_source_mapping_candidate,
)


SHA = "a" * 64


def cmi_payload() -> dict[str, object]:
    return {
        "decisions": [
            {
                "provider_record_key": "source:1",
                "raw_name": "Hotel Existing",
                "raw_city": "Bern",
                "detail_url": "https://example.test/existing",
                "decision": "EXACT_MATCH",
                "matched_hotel_id": "H-0001",
            },
            {
                "provider_record_key": "source:2",
                "raw_name": "Hotel New",
                "raw_city": "Basel",
                "detail_url": "https://example.test/new",
                "decision": "NEW_CANDIDATE",
            },
            {
                "provider_record_key": "source:3",
                "raw_name": "Hotel Conflict",
                "raw_city": "Genève",
                "detail_url": "https://example.test/conflict",
                "decision": "AMBIGUOUS_MATCH",
                "matched_hotel_id": "H-0002",
            },
        ]
    }


def verified() -> list[dict[str, object]]:
    return [
        {
            "source_record_key": "source:2",
            "verification_state": "CURRENT_DETAIL_VERIFIED",
            "response_sha256": "b" * 64,
        },
        {
            "source_record_key": "source:3",
            "verification_state": "CURRENT_DETAIL_VERIFIED",
            "response_sha256": "c" * 64,
        },
    ]


class SourceMappingTests(unittest.TestCase):
    def test_exhaustive_candidate_maps_every_source_record(self) -> None:
        candidate = build_source_mapping_candidate(
            cmi_payload(),
            verified(),
            [],
            snapshot_id="SNAPSHOT-1",
            source_manifest_sha256=SHA,
        )
        self.assertEqual(candidate["source_records"], 3)
        self.assertEqual(candidate["mappings_count"], 3)
        self.assertEqual(candidate["unmapped_records"], 0)
        self.assertEqual(candidate["counts_by_mapping_state"]["ACTIVE_CANONICAL"], 1)
        self.assertEqual(candidate["counts_by_mapping_state"]["RECONCILE_REQUIRED"], 2)
        self.assertFalse(candidate["crm_universe_complete"])
        self.assertFalse(candidate["authority_advanced"])
        self.assertEqual(candidate["h_id_allocations"], 0)
        self.assertEqual(candidate["outbound"], "CLOSED")
        self.assertEqual(candidate["send_allowed"], 0)
        self.assertEqual(validate_source_mapping_candidate(candidate), ())

    def test_existing_match_requires_canonical_target(self) -> None:
        payload = cmi_payload()
        payload["decisions"][0]["matched_hotel_id"] = ""
        with self.assertRaisesRegex(SourceMappingError, "lacks canonical hotel ID"):
            build_source_mapping_candidate(
                payload,
                verified(),
                [],
                snapshot_id="SNAPSHOT-1",
                source_manifest_sha256=SHA,
            )

    def test_missing_verification_remains_reconcile_required(self) -> None:
        candidate = build_source_mapping_candidate(
            cmi_payload(),
            [verified()[0]],
            [],
            snapshot_id="SNAPSHOT-1",
            source_manifest_sha256=SHA,
        )
        conflict = next(
            item for item in candidate["mappings"] if item["source_record_key"] == "source:3"
        )
        self.assertEqual(conflict["mapping_state"], "RECONCILE_REQUIRED")
        self.assertEqual(conflict["reason_code"], "MISSING_EXACT_CURRENT_VERIFICATION")

    def test_weak_verification_is_typed(self) -> None:
        candidate = build_source_mapping_candidate(
            cmi_payload(),
            [],
            [
                {
                    "source_record_key": "source:2",
                    "verification_state": "CURRENT_DETAIL_NAME_ONLY",
                },
                {
                    "source_record_key": "source:3",
                    "verification_state": "FETCH_FAILED",
                },
            ],
            snapshot_id="SNAPSHOT-1",
            source_manifest_sha256=SHA,
        )
        reasons = {
            item["source_record_key"]: item["reason_code"]
            for item in candidate["mappings"]
        }
        self.assertEqual(reasons["source:2"], "EXACT_CURRENT_CURRENT_DETAIL_NAME_ONLY")
        self.assertEqual(reasons["source:3"], "EXACT_CURRENT_FETCH_FAILED")

    def test_duplicate_verification_keys_fail_closed(self) -> None:
        duplicate = verified() + [copy.deepcopy(verified()[0])]
        with self.assertRaisesRegex(SourceMappingError, "duplicate verification"):
            build_source_mapping_candidate(
                cmi_payload(),
                duplicate,
                [],
                snapshot_id="SNAPSHOT-1",
                source_manifest_sha256=SHA,
            )

    def test_extra_terminal_verification_key_fails_closed(self) -> None:
        extras = verified() + [
            {
                "source_record_key": "source:1",
                "verification_state": "CURRENT_DETAIL_VERIFIED",
            }
        ]
        with self.assertRaisesRegex(SourceMappingError, "non-active source keys"):
            build_source_mapping_candidate(
                cmi_payload(),
                extras,
                [],
                snapshot_id="SNAPSHOT-1",
                source_manifest_sha256=SHA,
            )

    def test_validator_detects_mapping_tamper(self) -> None:
        candidate = build_source_mapping_candidate(
            cmi_payload(),
            verified(),
            [],
            snapshot_id="SNAPSHOT-1",
            source_manifest_sha256=SHA,
        )
        candidate["mappings"][0]["canonical_hotel_id"] = ""
        violations = validate_source_mapping_candidate(candidate)
        self.assertIn("CANONICAL_MAPPING_WITHOUT_TARGET", violations)
        self.assertIn("MAPPING_SHA_MISMATCH", violations)
        self.assertIn("CANDIDATE_SHA_MISMATCH", violations)

    def test_source_manifest_digest_is_required(self) -> None:
        with self.assertRaisesRegex(SourceMappingError, "64-character"):
            build_source_mapping_candidate(
                cmi_payload(),
                verified(),
                [],
                snapshot_id="SNAPSHOT-1",
                source_manifest_sha256="bad",
            )


if __name__ == "__main__":
    unittest.main()

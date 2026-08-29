from __future__ import annotations

import unittest

from swiss_os.ecv_provider_evidence import (
    NORMALIZER_VERSION,
    PROVIDER_CHANGE_REVIEW,
    URL_NOT_FOUND,
    ProviderEvidenceError,
    normalize_packet,
)
from swiss_os.exact_current_verify import validate_verification_packet


def packet(results: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": "EXACT-CURRENT-VERIFY-1.0",
        "batch_id": "SNAPSHOT:WORK:0001:RECLASSIFY:0001",
        "items_count": len(results),
        "results_count": len(results),
        "counts_by_state": {},
        "all_verified": False,
        "results": results,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "packet_sha256": "stale-before-normalization",
    }


class ProviderEvidenceTests(unittest.TestCase):
    def test_repeat_404_becomes_terminal_detail_url_evidence(self) -> None:
        raw = packet(
            [
                {
                    "source_record_key": "MD-404",
                    "verification_state": "FETCH_FAILED",
                    "followup": "REQUEUE_EXACT_CURRENT",
                    "error": (
                        "ExactCurrentVerifyError: fetch failed: "
                        "HTTPError: HTTP Error 404: Not Found; "
                        "HTTPError: HTTP Error 404: Not Found; "
                        "HTTPError: HTTP Error 404: Not Found"
                    ),
                }
            ]
        )
        normalized = normalize_packet(raw)
        result = normalized["results"][0]
        self.assertEqual(result["verification_state"], URL_NOT_FOUND)
        self.assertEqual(result["followup"], PROVIDER_CHANGE_REVIEW)
        self.assertTrue(normalized["all_terminal"])
        self.assertFalse(normalized["all_verified"])
        self.assertEqual(normalized["terminal_evidence_count"], 1)
        self.assertEqual(normalized["provider_record_change_count"], 1)
        self.assertEqual(normalized["evidence_normalizer"], NORMALIZER_VERSION)
        self.assertEqual(validate_verification_packet(normalized), ())
        self.assertFalse(normalized["authority_advanced"])
        self.assertEqual(normalized["h_id_allocations"], 0)
        self.assertEqual(normalized["outbound"], "CLOSED")
        self.assertEqual(normalized["send_allowed"], 0)

    def test_identity_drift_is_terminal_provider_review_not_requeue(self) -> None:
        raw = packet(
            [
                {
                    "source_record_key": "MD-NAME",
                    "verification_state": "CURRENT_DETAIL_NAME_ONLY",
                    "followup": "REQUEUE_EXACT_CURRENT",
                    "name_match": True,
                    "city_match": False,
                },
                {
                    "source_record_key": "MD-MISMATCH",
                    "verification_state": "CURRENT_DETAIL_MISMATCH",
                    "followup": "REQUEUE_EXACT_CURRENT",
                    "name_match": False,
                    "city_match": False,
                },
            ]
        )
        normalized = normalize_packet(raw)
        self.assertTrue(normalized["all_terminal"])
        self.assertEqual(normalized["provider_record_change_count"], 2)
        for result in normalized["results"]:
            self.assertEqual(result["followup"], PROVIDER_CHANGE_REVIEW)
            self.assertEqual(
                result["evidence_semantics"], "CURRENT_DETAIL_IDENTITY_DRIFT"
            )
        self.assertEqual(validate_verification_packet(normalized), ())

    def test_mixed_or_transient_fetch_failure_remains_requeue(self) -> None:
        raw = packet(
            [
                {
                    "source_record_key": "MD-TRANSIENT",
                    "verification_state": "FETCH_FAILED",
                    "followup": "REQUEUE_EXACT_CURRENT",
                    "error": (
                        "ExactCurrentVerifyError: fetch failed: "
                        "HTTPError: HTTP Error 404: Not Found; "
                        "TimeoutError: timed out"
                    ),
                }
            ]
        )
        normalized = normalize_packet(raw)
        result = normalized["results"][0]
        self.assertEqual(result["verification_state"], "FETCH_FAILED")
        self.assertEqual(result["followup"], "REQUEUE_EXACT_CURRENT")
        self.assertFalse(normalized["all_terminal"])
        self.assertEqual(normalized["terminal_evidence_count"], 0)
        self.assertEqual(normalized["provider_record_change_count"], 0)
        self.assertEqual(validate_verification_packet(normalized), ())

    def test_verified_record_remains_verified_and_terminal(self) -> None:
        raw = packet(
            [
                {
                    "source_record_key": "MD-OK",
                    "verification_state": "CURRENT_DETAIL_VERIFIED",
                    "followup": "DEDUPE_GROUP_ALIAS_REVIEW",
                }
            ]
        )
        normalized = normalize_packet(raw)
        self.assertTrue(normalized["all_terminal"])
        self.assertTrue(normalized["all_verified"])
        self.assertEqual(normalized["provider_record_change_count"], 0)
        self.assertEqual(validate_verification_packet(normalized), ())

    def test_authority_or_outbound_mutation_is_rejected(self) -> None:
        raw = packet([])
        raw["authority_advanced"] = True
        with self.assertRaisesRegex(ProviderEvidenceError, "authority_advanced"):
            normalize_packet(raw)
        raw = packet([])
        raw["send_allowed"] = 1
        with self.assertRaisesRegex(ProviderEvidenceError, "send_allowed"):
            normalize_packet(raw)


if __name__ == "__main__":
    unittest.main()

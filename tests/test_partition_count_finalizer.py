from __future__ import annotations

import copy
import unittest

from swiss_os.partition_count_finalizer import (
    PartitionCountFinalizerError,
    finalize_materialized_partition_count,
    validate_finalizer,
)


def _record(key: str, name: str, city: str, url: str, page: int) -> dict[str, object]:
    return {
        "source_record_key": key,
        "name": name,
        "city": city,
        "hs_id": "",
        "detail_url": url,
        "evidence_ref": f"CAPTURE:page:{page:04d}:sha256:{'a' * 64}",
    }


def _capture() -> dict[str, object]:
    return {
        "schema_version": "MEMBER_DIRECTORY_CAPTURE_V1",
        "capture_id": "CAPTURE-NO-COUNT",
        "provider": "HotellerieSuisse",
        "surface": "member-directory",
        "locale": "de",
        "capture_mode": "LIVE_PARTIAL",
        "coverage_claim": "PARTIAL",
        "started_at": "2026-08-28T10:00:00Z",
        "completed_at": "2026-08-28T10:05:00Z",
        "expected_pages": 2,
        "reported_records": 0,
        "capture_violations": ["REPORTED_RECORDS_UNRESOLVED"],
        "pages": [
            {
                "page_id": "CAPTURE-NO-COUNT:page:0001",
                "page_position": 1,
                "source_url": "https://example.test/directory",
                "capture_id": "CAPTURE-NO-COUNT",
                "locale": "de",
                "surface": "member-directory",
                "observed_reported_records": None,
                "observed_expected_pages": 2,
                "records": [
                    _record("hs:1", "Hotel Alpha", "Bern", "https://example.test/hotel-alpha", 1),
                    _record("hs:2", "Hotel Beta", "Basel", "https://example.test/hotel-beta", 1),
                ],
            },
            {
                "page_id": "CAPTURE-NO-COUNT:page:0002",
                "page_position": 2,
                "source_url": "https://example.test/directory/hotel-page-2",
                "capture_id": "CAPTURE-NO-COUNT",
                "locale": "de",
                "surface": "member-directory",
                "observed_reported_records": None,
                "observed_expected_pages": 2,
                "records": [
                    _record("hs:3", "Hotel Gamma", "Luzern", "https://example.test/hotel-gamma", 2)
                ],
            },
        ],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }


class PartitionCountFinalizerTests(unittest.TestCase):
    def test_materialized_partition_total_can_finalize_countless_capture(self) -> None:
        result = finalize_materialized_partition_count(_capture())
        self.assertEqual(result["materialized_records"], 3)
        self.assertEqual(result["record_count_basis"], "MATERIALIZED_PARTITION_TOTAL")
        self.assertTrue(result["coverage_complete"])
        self.assertTrue(result["member_directory_manifest"]["coverage_complete"])
        self.assertEqual(
            result["member_directory_manifest"]["record_count_basis"],
            "MATERIALIZED_PARTITION_TOTAL",
        )
        self.assertEqual(validate_finalizer(result), ())
        self.assertFalse(result["authority_advanced"])
        self.assertEqual(result["h_id_allocations"], 0)
        self.assertEqual(result["outbound"], "CLOSED")
        self.assertEqual(result["send_allowed"], 0)

    def test_non_count_capture_violation_fails_closed(self) -> None:
        payload = _capture()
        payload["capture_violations"].append("PAGE_COUNT_DRIFT:2,3")
        with self.assertRaisesRegex(PartitionCountFinalizerError, "non-count violations"):
            finalize_materialized_partition_count(payload)

    def test_partition_set_must_be_exact(self) -> None:
        payload = _capture()
        payload["pages"][1]["page_position"] = 3
        with self.assertRaisesRegex(PartitionCountFinalizerError, "page-count drift|partition set"):
            finalize_materialized_partition_count(payload)

    def test_duplicate_detail_url_fails_closed(self) -> None:
        payload = _capture()
        payload["pages"][1]["records"][0]["detail_url"] = "https://example.test/hotel-alpha"
        with self.assertRaisesRegex(PartitionCountFinalizerError, "duplicate detail_url"):
            finalize_materialized_partition_count(payload)

    def test_provider_count_presence_forbids_materialized_fallback(self) -> None:
        payload = _capture()
        payload["reported_records"] = 3
        with self.assertRaisesRegex(PartitionCountFinalizerError, "provider-reported count"):
            finalize_materialized_partition_count(payload)

    def test_tampering_is_detected(self) -> None:
        result = finalize_materialized_partition_count(_capture())
        tampered = copy.deepcopy(result)
        tampered["materialized_records"] = 4
        self.assertIn("FINALIZER_SHA_MISMATCH", validate_finalizer(tampered))


if __name__ == "__main__":
    unittest.main()

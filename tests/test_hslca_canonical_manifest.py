from __future__ import annotations

import copy
import unittest

from swiss_os.hslca_canonical_manifest import (
    HSLCADeviceToCanonicalError,
    build_canonical_manifest,
)
from swiss_os.member_directory import validate_member_directory_manifest


def _record(record_id: str, name: str, city: str, slug: str, evidence: str) -> dict[str, str]:
    return {
        "record_id": record_id,
        "name": name,
        "city": city,
        "evidence_ref": evidence,
        "hs_id": "",
        "detail_url": f"https://www.hotelleriesuisse.ch/de/directory/{slug}",
    }


def _finalizer() -> dict[str, object]:
    r1 = _record("MD-0001", "Hotel Alpha", "Bern", "hotel-alpha", "CAPTURE-1:page:0001#record-001")
    r2 = _record("MD-0002", "Hotel Beta", "Genève", "hotel-beta", "CAPTURE-1:page:0002#record-001")
    def page(position: int, row: dict[str, str], captured_at: str) -> dict[str, object]:
        return {
            "page_id": f"CAPTURE-1:page:{position:04d}",
            "page_position": position,
            "source_url": "https://www.hotelleriesuisse.ch/de/directory" + ("" if position == 1 else "/hotel-page-2"),
            "capture_id": "CAPTURE-1",
            "locale": "de",
            "surface": "member-directory",
            "captured_at": captured_at,
            "captured_at_basis": "ATOMIC_CHECKPOINT_FILE_MTIME",
            "records": [{key: value for key, value in row.items() if key != "record_id"}],
        }
    low = {
        "schema_version": "swiss-os-member-directory-manifest-v1",
        "snapshot_id": "CAPTURE-1",
        "capture_id": "CAPTURE-1",
        "locale": "de",
        "coverage_complete": True,
        "records_count": 2,
        "records": [r1, r2],
        "violations": [],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    capture = {
        "schema_version": "MEMBER_DIRECTORY_CAPTURE_V1",
        "capture_id": "CAPTURE-1",
        "locale": "de",
        "completed_at": "2026-08-28T10:10:00Z",
        "expected_pages": 2,
        "capture_violations": [],
        "pages": [
            page(1, r1, "2026-08-28T10:05:00Z"),
            page(2, r2, "2026-08-28T10:06:00Z"),
        ],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    return {
        "schema_version": "PARTITION-COUNT-FINALIZER-1.0",
        "coverage_complete": True,
        "materialized_records": 2,
        "record_count_basis": "MATERIALIZED_PARTITION_TOTAL",
        "member_directory_manifest": low,
        "finalized_capture": capture,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
    }


class HSLCADeviceToCanonicalTests(unittest.TestCase):
    def test_builds_self_validating_canonical_manifest(self) -> None:
        manifest = build_canonical_manifest(_finalizer())
        self.assertEqual(manifest["schema_version"], "MEMBER-DIRECTORY-1.0")
        self.assertEqual(manifest["source_provider"], "HOTELLERIESUISSE_MEMBER_DIRECTORY")
        self.assertEqual(manifest["source_epoch"], "CAPTURE-1")
        self.assertEqual(manifest["records_count"], 2)
        self.assertTrue(manifest["coverage_complete"])
        self.assertEqual(manifest["violations"], [])
        self.assertEqual(validate_member_directory_manifest(manifest), ())
        extensions = manifest["record_extensions"]
        self.assertEqual(extensions[0]["evidence_scope"], "CURRENT_DIRECTORY_RECORD")
        self.assertIn(extensions[0]["partition_key"], {"page-0001", "page-0002"})
        self.assertFalse(manifest["authority_advanced"])
        self.assertEqual(manifest["h_id_allocations"], 0)
        self.assertFalse(manifest["outbound_opened"])
        self.assertEqual(manifest["send_allowed"], 0)

    def test_missing_hpcb_timestamp_fails_closed(self) -> None:
        payload = _finalizer()
        del payload["finalized_capture"]["pages"][0]["captured_at"]  # type: ignore[index]
        with self.assertRaisesRegex(HSLCADeviceToCanonicalError, "captured_at"):
            build_canonical_manifest(payload)

    def test_wrong_timestamp_basis_fails_closed(self) -> None:
        payload = _finalizer()
        payload["finalized_capture"]["pages"][0]["captured_at_basis"] = "GUESSED"  # type: ignore[index]
        with self.assertRaisesRegex(HSLCADeviceToCanonicalError, "HPCB"):
            build_canonical_manifest(payload)

    def test_capture_and_low_level_identity_mismatch_fails_closed(self) -> None:
        payload = _finalizer()
        payload["member_directory_manifest"]["records"][0]["city"] = "Zürich"  # type: ignore[index]
        with self.assertRaisesRegex(HSLCADeviceToCanonicalError, "city mismatch"):
            build_canonical_manifest(payload)

    def test_duplicate_capture_detail_url_fails_closed(self) -> None:
        payload = _finalizer()
        url = payload["finalized_capture"]["pages"][0]["records"][0]["detail_url"]  # type: ignore[index]
        payload["finalized_capture"]["pages"][1]["records"][0]["detail_url"] = url  # type: ignore[index]
        with self.assertRaisesRegex(HSLCADeviceToCanonicalError, "duplicate capture detail URL"):
            build_canonical_manifest(payload)

    def test_low_level_count_mismatch_fails_closed(self) -> None:
        payload = _finalizer()
        payload["member_directory_manifest"]["records_count"] = 3  # type: ignore[index]
        with self.assertRaisesRegex(HSLCADeviceToCanonicalError, "record count mismatch"):
            build_canonical_manifest(payload)

    def test_partition_gap_fails_closed(self) -> None:
        payload = _finalizer()
        payload["finalized_capture"]["pages"][1]["page_position"] = 3  # type: ignore[index]
        with self.assertRaisesRegex(HSLCADeviceToCanonicalError, "partition set mismatch"):
            build_canonical_manifest(payload)

    def test_pre_authorized_finalizer_fails_closed(self) -> None:
        payload = _finalizer()
        payload["authority_advanced"] = True
        with self.assertRaisesRegex(HSLCADeviceToCanonicalError, "authority_advanced"):
            build_canonical_manifest(payload)

    def test_boolean_integer_coercion_fails_closed(self) -> None:
        payload = _finalizer()
        payload["h_id_allocations"] = False
        with self.assertRaisesRegex(HSLCADeviceToCanonicalError, "integer 0"):
            build_canonical_manifest(payload)

    def test_incomplete_low_level_manifest_fails_closed(self) -> None:
        payload = _finalizer()
        payload["member_directory_manifest"]["coverage_complete"] = False  # type: ignore[index]
        with self.assertRaisesRegex(HSLCADeviceToCanonicalError, "coverage_complete"):
            build_canonical_manifest(payload)

    def test_non_current_post_observation_record_fails_closed_via_canonical_builder(self) -> None:
        payload = _finalizer()
        payload["finalized_capture"]["pages"][0]["captured_at"] = "2026-08-28T10:11:00Z"  # type: ignore[index]
        with self.assertRaisesRegex(HSLCADeviceToCanonicalError, "RECORD_OBSERVED_AFTER_MANIFEST"):
            build_canonical_manifest(payload)


if __name__ == "__main__":
    unittest.main()

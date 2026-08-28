from __future__ import annotations

from copy import deepcopy
import unittest

from swiss_os.directory_export import export_directory_to_cmi
from swiss_os.hslca_transfer_manifest import (
    HslcaTransferManifestError,
    compile_transfer_manifest,
)
from swiss_os.member_directory import validate_member_directory_manifest


def _record(name: str, city: str, slug: str, evidence: str) -> dict[str, str]:
    return {
        "name": name,
        "city": city,
        "hs_id": "",
        "detail_url": (
            "https://www.hotelleriesuisse.ch/de/verband/mitgliedschaft/"
            f"mitgliederverzeichnis/hotel-{slug}"
        ),
        "evidence_ref": evidence,
        "source_url": "https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis",
    }


def _capture() -> dict[str, object]:
    capture_id = "HS-MEMBER-DE-TEST"
    return {
        "schema_version": "MEMBER_DIRECTORY_CAPTURE_V1",
        "capture_id": capture_id,
        "locale": "de",
        "started_at": "2026-08-28T20:00:00+00:00",
        "completed_at": "2026-08-28T20:02:00+00:00",
        "capture_mode": "LIVE_COMPLETE_MATERIALIZED_COUNT",
        "coverage_claim": "COMPLETE",
        "record_count_basis": "MATERIALIZED_PARTITION_TOTAL",
        "declared_raw_records": 3,
        "expected_pages": 2,
        "capture_violations": [],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
        "pages": [
            {
                "capture_id": capture_id,
                "locale": "de",
                "page_position": 1,
                "captured_at": "2026-08-28T20:00:30+00:00",
                "source_url": "https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis",
                "records": [
                    _record("Hotel Alpha", "Bern", "alpha", f"{capture_id}:page:0001#record-001"),
                    _record("Hotel Beta", "Basel", "beta", f"{capture_id}:page:0001#record-002"),
                ],
            },
            {
                "capture_id": capture_id,
                "locale": "de",
                "page_position": 2,
                "captured_at": "2026-08-28T20:01:30+00:00",
                "source_url": "https://www.hotelleriesuisse.ch/de/verband-und-geschaeftsstelle/mitglieder/mitgliederverzeichnis/hotel-page-2",
                "records": [
                    _record("Hotel Gamma", "Zürich", "gamma", f"{capture_id}:page:0002#record-001"),
                ],
            },
        ],
    }


class HslcaTransferManifestTests(unittest.TestCase):
    def test_compiles_transfer_valid_member_directory_manifest(self) -> None:
        manifest = compile_transfer_manifest(_capture())
        self.assertEqual(manifest["schema_version"], "MEMBER-DIRECTORY-1.0")
        self.assertTrue(manifest["coverage_complete"])
        self.assertEqual(manifest["records_count"], 3)
        self.assertEqual(manifest["source_provider"], "HOTELLERIESUISSE_MEMBER_DIRECTORY")
        self.assertEqual(manifest["h_id_allocations"], 0)
        self.assertFalse(manifest["authority_advanced"])
        self.assertFalse(manifest["outbound_opened"])
        self.assertEqual(manifest["send_allowed"], 0)
        self.assertEqual(validate_member_directory_manifest(manifest), ())

    def test_output_flows_directly_to_d2c_without_allocating_ids(self) -> None:
        manifest = compile_transfer_manifest(_capture())
        exported, attestation = export_directory_to_cmi(manifest)
        self.assertEqual(len(exported), 3)
        self.assertEqual(attestation["exported_records"], 3)
        self.assertTrue(attestation["ssr_pending"])
        self.assertEqual(attestation["h_id_allocations"], 0)
        self.assertFalse(attestation["authority_advanced"])
        self.assertEqual(attestation["outbound"], "CLOSED")
        self.assertEqual(attestation["send_allowed"], 0)

    def test_rejects_non_finalized_capture(self) -> None:
        payload = _capture()
        payload["capture_violations"] = ["REPORTED_RECORDS_UNRESOLVED"]
        with self.assertRaises(HslcaTransferManifestError):
            compile_transfer_manifest(payload)

    def test_rejects_wrong_count_basis(self) -> None:
        payload = _capture()
        payload["record_count_basis"] = "PROVIDER_REPORTED"
        with self.assertRaises(HslcaTransferManifestError):
            compile_transfer_manifest(payload)

    def test_rejects_boolean_zero_coercion(self) -> None:
        payload = _capture()
        payload["h_id_allocations"] = False
        with self.assertRaises(HslcaTransferManifestError):
            compile_transfer_manifest(payload)

    def test_rejects_authority_preauthorization(self) -> None:
        payload = _capture()
        payload["authority_advanced"] = True
        with self.assertRaises(HslcaTransferManifestError):
            compile_transfer_manifest(payload)

    def test_rejects_duplicate_detail_url(self) -> None:
        payload = _capture()
        pages = payload["pages"]
        assert isinstance(pages, list)
        pages[1]["records"][0]["detail_url"] = pages[0]["records"][0]["detail_url"]
        with self.assertRaises(HslcaTransferManifestError):
            compile_transfer_manifest(payload)

    def test_rejects_partition_gap_even_if_cardinality_matches(self) -> None:
        payload = _capture()
        pages = payload["pages"]
        assert isinstance(pages, list)
        pages[1]["page_position"] = 3
        with self.assertRaises(HslcaTransferManifestError):
            compile_transfer_manifest(payload)

    def test_rejects_materialized_count_drift(self) -> None:
        payload = _capture()
        payload["declared_raw_records"] = 4
        with self.assertRaises(HslcaTransferManifestError):
            compile_transfer_manifest(payload)

    def test_deterministic_manifest_hash(self) -> None:
        first = compile_transfer_manifest(_capture())
        second = compile_transfer_manifest(deepcopy(_capture()))
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
        self.assertEqual(first["records_sha256"], second["records_sha256"])


if __name__ == "__main__":
    unittest.main()

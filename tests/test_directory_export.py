from __future__ import annotations

import copy
import unittest

from swiss_os.directory_export import DirectoryExportError, export_directory_to_cmi
from swiss_os.member_directory import (
    DirectoryManifestConfig,
    DirectoryRecord,
    build_member_directory_manifest,
)


OBSERVED_AT = "2026-08-28T14:00:00+02:00"
EPOCH = "HS-DIRECTORY-DE-20260828T120000Z"


def complete_manifest() -> dict[str, object]:
    records = (
        DirectoryRecord.from_mapping(
            {
                "record_id": "directory:1",
                "name": "Hotel Alpha",
                "city": "Bern",
                "evidence_ref": "page:1",
                "hs_id": "",
                "detail_url": "https://example.test/member/hotel-alpha",
                "source_provider": "HOTELLERIESUISSE_MEMBER_DIRECTORY",
                "locale": "de",
                "source_surface": "https://example.test/member-directory",
                "source_epoch": EPOCH,
                "partition_key": "page:1",
                "observed_at": OBSERVED_AT,
                "evidence_scope": "CURRENT_DIRECTORY_RECORD",
            }
        ),
        DirectoryRecord.from_mapping(
            {
                "record_id": "directory:2",
                "name": "Hotel Beta",
                "city": "Basel",
                "evidence_ref": "page:2",
                "hs_id": "",
                "detail_url": "https://example.test/member/hotel-beta",
                "source_provider": "HOTELLERIESUISSE_MEMBER_DIRECTORY",
                "locale": "de",
                "source_surface": "https://example.test/member-directory",
                "source_epoch": EPOCH,
                "partition_key": "page:2",
                "observed_at": OBSERVED_AT,
                "evidence_scope": "CURRENT_DIRECTORY_RECORD",
            }
        ),
    )
    result = build_member_directory_manifest(
        records,
        DirectoryManifestConfig(
            snapshot_id=EPOCH,
            observed_at=OBSERVED_AT,
            source_provider="HOTELLERIESUISSE_MEMBER_DIRECTORY",
            locale="de",
            source_url="https://example.test/member-directory",
            source_epoch=EPOCH,
            expected_partitions=2,
            declared_raw_records=2,
            coverage_complete_requested=True,
        ),
    )
    assert result.coverage_complete
    return result.manifest


class DirectoryExportTests(unittest.TestCase):
    def test_complete_manifest_exports_deterministically(self) -> None:
        manifest = complete_manifest()
        first_records, first_attestation = export_directory_to_cmi(manifest)
        second_records, second_attestation = export_directory_to_cmi(manifest)
        self.assertEqual(first_records, second_records)
        self.assertEqual(first_attestation, second_attestation)
        self.assertEqual(len(first_records), 2)
        self.assertEqual(
            [row["provider_record_key"] for row in first_records],
            ["directory:1", "directory:2"],
        )
        self.assertTrue(first_attestation["ssr_pending"])
        self.assertFalse(first_attestation["authority_advanced"])
        self.assertEqual(first_attestation["h_id_allocations"], 0)
        self.assertEqual(first_attestation["outbound"], "CLOSED")
        self.assertEqual(first_attestation["send_allowed"], 0)

    def test_partial_manifest_is_rejected(self) -> None:
        manifest = complete_manifest()
        manifest["coverage_complete"] = False
        # Recompute is intentionally not done: transfer validation must fail first.
        with self.assertRaises(DirectoryExportError):
            export_directory_to_cmi(manifest)

    def test_tampered_manifest_is_rejected(self) -> None:
        manifest = complete_manifest()
        manifest["records"][0]["name"] = "Tampered"
        with self.assertRaisesRegex(DirectoryExportError, "transfer validation"):
            export_directory_to_cmi(manifest)

    def test_wrong_provider_is_rejected(self) -> None:
        manifest = complete_manifest()
        manifest["source_provider"] = "OTHER_PROVIDER"
        # Hash tampering is itself enough to fail closed.
        with self.assertRaises(DirectoryExportError):
            export_directory_to_cmi(manifest)

    def test_missing_detail_url_is_rejected(self) -> None:
        manifest = complete_manifest()
        broken = copy.deepcopy(manifest)
        broken["records"][0]["detail_url"] = ""
        with self.assertRaises(DirectoryExportError):
            export_directory_to_cmi(broken)

    def test_input_cannot_claim_authority_or_outbound(self) -> None:
        for field, value in (
            ("authority_advanced", True),
            ("h_id_allocations", 1),
            ("outbound_opened", True),
            ("send_allowed", 1),
        ):
            manifest = complete_manifest()
            manifest[field] = value
            with self.assertRaises(DirectoryExportError):
                export_directory_to_cmi(manifest)


if __name__ == "__main__":
    unittest.main()

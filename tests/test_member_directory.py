from __future__ import annotations

import unittest

from swiss_os.member_directory import (
    DirectoryManifestConfig,
    DirectoryRecord,
    build_member_directory_manifest,
    validate_member_directory_manifest,
)


OBSERVED_AT = "2026-08-28T14:00:00+02:00"
EPOCH = "HS-DIRECTORY-2026-08-28-DE-E1"


def record(
    record_id: str,
    name: str,
    city: str,
    *,
    hs_id: str,
    partition: str,
    scope: str = "CURRENT_DIRECTORY_RECORD",
    locale: str = "de",
    epoch: str = EPOCH,
) -> DirectoryRecord:
    return DirectoryRecord.from_mapping(
        {
            "record_id": record_id,
            "name": name,
            "city": city,
            "evidence_ref": f"evidence:{record_id}",
            "hs_id": hs_id,
            "detail_url": f"https://example.test/member/{hs_id}",
            "source_provider": "HOTELLERIESUISSE_MEMBER_DIRECTORY",
            "locale": locale,
            "source_surface": "member-directory",
            "source_epoch": epoch,
            "partition_key": partition,
            "observed_at": OBSERVED_AT,
            "evidence_scope": scope,
        }
    )


def config(*, records: int = 2, partitions: int = 2, complete: bool = True) -> DirectoryManifestConfig:
    return DirectoryManifestConfig(
        snapshot_id="HS-DIRECTORY-2026-08-28-DE-E1",
        observed_at=OBSERVED_AT,
        source_provider="HOTELLERIESUISSE_MEMBER_DIRECTORY",
        locale="de",
        source_url="https://example.test/member-directory",
        source_epoch=EPOCH,
        expected_partitions=partitions,
        declared_raw_records=records,
        coverage_complete_requested=complete,
    )


class MemberDirectoryManifestTests(unittest.TestCase):
    def test_complete_coherent_manifest_passes(self) -> None:
        records = (
            record("directory:1", "Hotel Alpha", "Bern", hs_id="1", partition="page:1"),
            record("directory:2", "Hotel Beta", "Basel", hs_id="2", partition="page:2"),
        )
        result = build_member_directory_manifest(records, config())
        self.assertTrue(result.coverage_complete)
        self.assertEqual(result.violations, ())
        self.assertEqual(result.manifest["records_count"], 2)
        self.assertFalse(result.manifest["authority_advanced"])
        self.assertEqual(result.manifest["h_id_allocations"], 0)
        self.assertFalse(result.manifest["outbound_opened"])
        self.assertEqual(result.manifest["send_allowed"], 0)
        self.assertEqual(validate_member_directory_manifest(result.manifest), ())

    def test_historical_scope_blocks_complete(self) -> None:
        records = (
            record(
                "directory:1",
                "Hotel Alpha",
                "Bern",
                hs_id="1",
                partition="page:1",
                scope="HISTORICAL_CACHE_DISCOVERY_ONLY",
            ),
        )
        result = build_member_directory_manifest(
            records, config(records=1, partitions=1)
        )
        self.assertFalse(result.coverage_complete)
        self.assertIn("NON_CURRENT_EVIDENCE_SCOPE", result.violations)

    def test_duplicate_hs_id_blocks_complete(self) -> None:
        records = (
            record("directory:1", "Hotel Alpha", "Bern", hs_id="1", partition="page:1"),
            record("directory:2", "Hotel Beta", "Basel", hs_id="1", partition="page:2"),
        )
        result = build_member_directory_manifest(records, config())
        self.assertFalse(result.coverage_complete)
        self.assertIn("DUPLICATE_HS_ID", result.violations)
        self.assertIn("DUPLICATE_DETAIL_URL", result.violations)

    def test_duplicate_normalized_name_city_blocks_complete(self) -> None:
        records = (
            record("directory:1", "Hôtel Éden", "Zürich", hs_id="1", partition="page:1"),
            record("directory:2", "Hotel Eden", "Zurich", hs_id="2", partition="page:2"),
        )
        result = build_member_directory_manifest(records, config())
        self.assertFalse(result.coverage_complete)
        self.assertIn("DUPLICATE_NORMALIZED_NAME_CITY", result.violations)

    def test_partition_mismatch_blocks_complete(self) -> None:
        records = (
            record("directory:1", "Hotel Alpha", "Bern", hs_id="1", partition="page:1"),
            record("directory:2", "Hotel Beta", "Basel", hs_id="2", partition="page:1"),
        )
        result = build_member_directory_manifest(records, config(partitions=2))
        self.assertFalse(result.coverage_complete)
        self.assertIn("PARTITION_COVERAGE_MISMATCH", result.violations)

    def test_record_count_mismatch_blocks_complete(self) -> None:
        records = (
            record("directory:1", "Hotel Alpha", "Bern", hs_id="1", partition="page:1"),
        )
        result = build_member_directory_manifest(
            records, config(records=2, partitions=1)
        )
        self.assertFalse(result.coverage_complete)
        self.assertIn("DECLARED_RECORD_COUNT_MISMATCH", result.violations)

    def test_mixed_locale_and_epoch_block_complete(self) -> None:
        records = (
            record("directory:1", "Hotel Alpha", "Bern", hs_id="1", partition="page:1"),
            record(
                "directory:2",
                "Hotel Beta",
                "Basel",
                hs_id="2",
                partition="page:2",
                locale="fr",
                epoch="OTHER-EPOCH",
            ),
        )
        result = build_member_directory_manifest(records, config())
        self.assertFalse(result.coverage_complete)
        self.assertIn("MIXED_LOCALE", result.violations)
        self.assertIn("MIXED_SOURCE_EPOCH", result.violations)

    def test_partial_manifest_can_be_valid_without_claiming_complete(self) -> None:
        records = (
            record(
                "directory:1",
                "Hotel Alpha",
                "Bern",
                hs_id="1",
                partition="page:1",
                scope="HISTORICAL_CACHE_DISCOVERY_ONLY",
            ),
        )
        result = build_member_directory_manifest(
            records, config(records=2050, partitions=171, complete=False)
        )
        self.assertFalse(result.coverage_complete)
        self.assertIn("PARTITION_COVERAGE_MISMATCH", result.violations)
        self.assertIn("DECLARED_RECORD_COUNT_MISMATCH", result.violations)
        self.assertEqual(validate_member_directory_manifest(result.manifest), ())

    def test_manifest_hash_is_deterministic_across_input_order(self) -> None:
        first = record("directory:1", "Hotel Alpha", "Bern", hs_id="1", partition="page:1")
        second = record("directory:2", "Hotel Beta", "Basel", hs_id="2", partition="page:2")
        result_a = build_member_directory_manifest((first, second), config())
        result_b = build_member_directory_manifest((second, first), config())
        self.assertEqual(result_a.manifest["records_sha256"], result_b.manifest["records_sha256"])
        self.assertEqual(result_a.manifest["manifest_sha256"], result_b.manifest["manifest_sha256"])


if __name__ == "__main__":
    unittest.main()

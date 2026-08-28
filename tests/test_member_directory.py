from __future__ import annotations

import unittest

from swiss_os.member_directory import (
    build_member_directory_manifest,
    validate_member_directory_manifest,
)


RECORDS = [
    {
        "name": "Hotel Alpha",
        "city": "Bern",
        "hs_id": "100",
        "detail_url": "https://example.test/hotel-alpha",
        "evidence_ref": "EV-1",
    },
    {
        "name": "Hotel Beta",
        "city": "Basel",
        "hs_id": "200",
        "detail_url": "https://example.test/hotel-beta",
        "evidence_ref": "EV-2",
    },
]


def build(**overrides):
    kwargs = dict(
        snapshot_id="HS-DIR-TEST",
        observed_at="2026-08-28T14:00:00+02:00",
        locale="de",
        source_url="https://example.test/directory",
        declared_raw_records=2,
        expected_pages=1,
        observed_pages=1,
        coverage_complete_requested=True,
    )
    kwargs.update(overrides)
    return build_member_directory_manifest(RECORDS, **kwargs)


class MemberDirectoryManifestTests(unittest.TestCase):
    def test_complete_coherent_manifest_is_ssr_ready_shape(self) -> None:
        manifest = build()
        self.assertTrue(manifest["coverage_complete"])
        self.assertEqual(manifest["materialized_records"], 2)
        self.assertEqual(manifest["coverage_violations"], [])
        self.assertEqual(manifest["authority_advanced"], False)
        self.assertEqual(manifest["h_id_allocations"], 0)
        self.assertEqual(manifest["outbound_opened"], False)
        self.assertEqual(validate_member_directory_manifest(manifest), ())

    def test_page_coverage_mismatch_fails_closed(self) -> None:
        manifest = build(expected_pages=2, observed_pages=1)
        self.assertFalse(manifest["coverage_complete"])
        self.assertIn("PAGE_COVERAGE_INCOMPLETE", manifest["coverage_violations"])

    def test_declared_record_mismatch_fails_closed(self) -> None:
        manifest = build(declared_raw_records=3)
        self.assertFalse(manifest["coverage_complete"])
        self.assertIn("DECLARED_RECORD_COUNT_MISMATCH", manifest["coverage_violations"])

    def test_coverage_request_false_cannot_become_complete(self) -> None:
        manifest = build(coverage_complete_requested=False)
        self.assertFalse(manifest["coverage_complete"])

    def test_duplicate_hsid_is_rejected(self) -> None:
        records = [dict(RECORDS[0]), {**RECORDS[1], "hs_id": "100"}]
        with self.assertRaisesRegex(ValueError, "duplicate member-directory hs_id"):
            build_member_directory_manifest(
                records,
                snapshot_id="S",
                observed_at="2026-08-28",
                locale="de",
                source_url="https://example.test",
                declared_raw_records=2,
                expected_pages=1,
                observed_pages=1,
                coverage_complete_requested=True,
            )

    def test_duplicate_detail_url_is_rejected(self) -> None:
        records = [dict(RECORDS[0]), {**RECORDS[1], "detail_url": RECORDS[0]["detail_url"]}]
        with self.assertRaisesRegex(ValueError, "duplicate member-directory detail_url"):
            build_member_directory_manifest(
                records,
                snapshot_id="S",
                observed_at="2026-08-28",
                locale="de",
                source_url="https://example.test",
                declared_raw_records=2,
                expected_pages=1,
                observed_pages=1,
                coverage_complete_requested=True,
            )

    def test_missing_evidence_ref_is_rejected(self) -> None:
        records = [{**RECORDS[0], "evidence_ref": ""}]
        with self.assertRaisesRegex(ValueError, "requires evidence_ref"):
            build_member_directory_manifest(
                records,
                snapshot_id="S",
                observed_at="2026-08-28",
                locale="de",
                source_url="https://example.test",
                declared_raw_records=1,
                expected_pages=1,
                observed_pages=1,
                coverage_complete_requested=True,
            )

    def test_name_city_fallback_record_id_is_deterministic(self) -> None:
        records = [{"name": " Hôtel Étoile ", "city": " Genève ", "evidence_ref": "EV"}]
        m1 = build_member_directory_manifest(
            records,
            snapshot_id="S",
            observed_at="2026-08-28",
            locale="fr",
            source_url="https://example.test",
            declared_raw_records=1,
            expected_pages=1,
            observed_pages=1,
            coverage_complete_requested=True,
        )
        m2 = build_member_directory_manifest(
            records,
            snapshot_id="S",
            observed_at="2026-08-28",
            locale="fr",
            source_url="https://example.test",
            declared_raw_records=1,
            expected_pages=1,
            observed_pages=1,
            coverage_complete_requested=True,
        )
        self.assertEqual(m1["records"][0]["record_id"], m2["records"][0]["record_id"])
        self.assertEqual(m1["records_sha256"], m2["records_sha256"])

    def test_tampered_hash_is_detected(self) -> None:
        manifest = build()
        manifest["records_sha256"] = "0" * 64
        self.assertIn("RECORDS_SHA256_MISMATCH", validate_member_directory_manifest(manifest))

    def test_validator_blocks_authority_or_outbound_flags(self) -> None:
        manifest = build()
        manifest["authority_advanced"] = True
        manifest["h_id_allocations"] = 1
        manifest["outbound_opened"] = True
        errors = validate_member_directory_manifest(manifest)
        self.assertIn("AUTHORITY_ADVANCED_MUST_BE_FALSE", errors)
        self.assertIn("H_ID_ALLOCATIONS_MUST_BE_ZERO", errors)
        self.assertIn("OUTBOUND_OPENED_MUST_BE_FALSE", errors)


if __name__ == "__main__":
    unittest.main()

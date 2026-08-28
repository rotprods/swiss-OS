from __future__ import annotations

import unittest

from swiss_os.member_directory import build_member_directory_manifest, validate_member_directory_manifest
from swiss_os.source_scope import EXACT, build_candidate_snapshot, reconcile_source_scope


class MemberDirectoryToSSRIntegrationTests(unittest.TestCase):
    def test_complete_mdm_flows_to_exact_frozen_candidate(self) -> None:
        directory = build_member_directory_manifest(
            [
                {
                    "name": "Hotel Alpha",
                    "city": "Bern",
                    "hs_id": "100",
                    "detail_url": "https://directory.example/hotel-alpha",
                    "evidence_ref": "EV-MD-100",
                },
                {
                    "name": "Hotel Beta",
                    "city": "Basel",
                    "hs_id": "200",
                    "detail_url": "https://directory.example/hotel-beta",
                    "evidence_ref": "EV-MD-200",
                },
            ],
            snapshot_id="MDM-INTEGRATION",
            observed_at="2026-08-28T14:00:00+02:00",
            locale="de",
            source_url="https://directory.example",
            declared_raw_records=2,
            expected_pages=1,
            observed_pages=1,
            coverage_complete_requested=True,
        )
        self.assertEqual(validate_member_directory_manifest(directory), ())
        self.assertTrue(directory["coverage_complete"])

        api = {
            "snapshot_id": "DS-INTEGRATION",
            "capture_valid": True,
            "records": [
                {
                    "source_record_key": "hs:100",
                    "hs_id": "100",
                    "name": "Hotel Alpha",
                    "city": "Bern",
                    "links": [{"url": "https://directory.example/hotel-alpha"}],
                },
                {
                    "source_record_key": "hs:200",
                    "hs_id": "200",
                    "name": "Hotel Beta",
                    "city": "Basel",
                    "links": [{"url": "https://directory.example/hotel-beta"}],
                },
            ],
        }

        result = reconcile_source_scope(api, directory)
        self.assertEqual(result.state, EXACT)
        self.assertEqual(result.matched_count, 2)
        self.assertEqual(result.conflicts, ())
        self.assertEqual(result.api_only, ())
        self.assertEqual(result.directory_only, ())

        candidate = build_candidate_snapshot(api, directory, result)
        self.assertEqual(candidate["snapshot_state"], "FROZEN_CANDIDATE")
        self.assertTrue(candidate["crm_freeze_eligible"])
        self.assertFalse(candidate["authority_advanced"])
        self.assertEqual(candidate["h_id_allocations"], 0)
        self.assertFalse(candidate["outbound_opened"])

    def test_partial_mdm_cannot_enter_ssr(self) -> None:
        directory = build_member_directory_manifest(
            [
                {
                    "name": "Hotel Alpha",
                    "city": "Bern",
                    "hs_id": "100",
                    "evidence_ref": "EV-MD-100",
                }
            ],
            snapshot_id="MDM-PARTIAL",
            observed_at="2026-08-28T14:00:00+02:00",
            locale="de",
            source_url="https://directory.example",
            declared_raw_records=1,
            expected_pages=2,
            observed_pages=1,
            coverage_complete_requested=True,
        )
        self.assertFalse(directory["coverage_complete"])
        api = {
            "snapshot_id": "DS-PARTIAL",
            "capture_valid": True,
            "records": [
                {
                    "source_record_key": "hs:100",
                    "hs_id": "100",
                    "name": "Hotel Alpha",
                    "city": "Bern",
                    "links": [],
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "coverage_complete=true"):
            reconcile_source_scope(api, directory)


if __name__ == "__main__":
    unittest.main()

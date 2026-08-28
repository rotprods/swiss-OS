import unittest

from swiss_os.pre_authority_pipeline import build_pre_authority_bundle


class PreAuthorityPipelineTests(unittest.TestCase):
    def _api(self):
        return {
            "snapshot_id": "API-E1",
            "capture_valid": True,
            "endpoint": "https://example.invalid/info/v2/lodgingbusinesses",
            "records_count": 2,
            "records": [
                {"source_record_key": "ds:1", "hs_id": "101", "name": "Hotel A", "city": "Bern", "links": [{"type": "official", "url": "https://hotel-a.example/"}]},
                {"source_record_key": "ds:2", "hs_id": "102", "name": "Hotel B", "city": "Zürich", "links": [{"type": "official", "url": "https://hotel-b.example/"}]},
            ],
        }

    def _directory(self):
        return [
            {"name": "Hotel A", "city": "Bern", "evidence_ref": "official:p1:a", "locale": "de", "epoch": "E1", "page": 1, "hs_id": "101"},
            {"name": "Hotel B", "city": "Zürich", "evidence_ref": "official:p2:b", "locale": "de", "epoch": "E1", "page": 2, "hs_id": "102"},
        ]

    def _build(self, api=None, directory=None, **kwargs):
        return build_pre_authority_bundle(
            api or self._api(),
            directory or self._directory(),
            directory_snapshot_id="MD-E1",
            directory_observed_at="2026-08-28T12:00:00Z",
            locale="de",
            epoch="E1",
            expected_pages=kwargs.pop("expected_pages", 2),
            declared_raw_records=kwargs.pop("declared_raw_records", 2),
            **kwargs,
        )

    def test_exact_complete_sources_emit_frozen_candidate_and_ingest_records(self):
        bundle = self._build()
        self.assertEqual(bundle["state"], "FROZEN_CANDIDATE_READY")
        self.assertEqual(bundle["blockers"], [])
        self.assertEqual(bundle["candidate_snapshot"]["snapshot_state"], "FROZEN_CANDIDATE")
        self.assertTrue(bundle["candidate_snapshot"]["crm_freeze_eligible"])
        self.assertEqual(bundle["reconciliation"]["state"], "EXACT")
        self.assertEqual(bundle["ingest_records_count"], 2)
        self.assertFalse(bundle["authority_advanced"])
        self.assertEqual(bundle["h_id_allocations"], 0)
        self.assertFalse(bundle["outbound_opened"])

    def test_partial_directory_fails_before_scope_reconciliation(self):
        bundle = self._build(directory=self._directory()[:1])
        self.assertEqual(bundle["state"], "BLOCKED_PRE_AUTHORITY")
        self.assertIn("MEMBER_DIRECTORY_INCOMPLETE", bundle["blockers"])
        self.assertIn("DIRECTORY_COVERAGE_WORK_REMAINS", bundle["blockers"])
        self.assertIsNone(bundle["candidate_snapshot"])
        self.assertEqual(bundle["ingest_records_count"], 0)

    def test_conflict_page_blocks_even_when_all_pages_observed(self):
        bundle = self._build(conflict_pages=[2])
        self.assertEqual(bundle["state"], "BLOCKED_PRE_AUTHORITY")
        self.assertIn("DIRECTORY_COVERAGE_WORK_REMAINS", bundle["blockers"])
        self.assertEqual(bundle["coverage"]["tasks"][0]["priority"], 950)
        self.assertEqual(bundle["ingest_records_count"], 0)

    def test_unreconciled_complete_sources_do_not_export_ingest_records(self):
        api = self._api()
        api["records"][1]["hs_id"] = "999"
        api["records"][1]["name"] = "Different Hotel"
        bundle = self._build(api=api)
        self.assertEqual(bundle["state"], "BLOCKED_PRE_AUTHORITY")
        self.assertIn("SOURCE_SCOPE_UNRESOLVED", bundle["blockers"])
        self.assertEqual(bundle["reconciliation"]["state"], "UNRESOLVED")
        self.assertEqual(bundle["ingest_records_count"], 0)

    def test_bundle_hash_is_deterministic(self):
        first = self._build()
        second = self._build()
        self.assertEqual(first["bundle_sha256"], second["bundle_sha256"])


if __name__ == "__main__":
    unittest.main()

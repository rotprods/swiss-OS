from __future__ import annotations

import unittest

from swiss_os.candidate_export import export_candidate_ingest_records


class CandidateExportTests(unittest.TestCase):
    def api(self):
        return {
            "snapshot_id": "DS-HS-TEST",
            "capture_valid": True,
            "endpoint": "https://api.discover.swiss/info/v2/lodgingbusinesses",
            "records_count": 2,
            "records": [
                {
                    "source_record_key": "hs:2",
                    "name": "Hotel Two",
                    "city": "Bern",
                    "links": [{"type": "website", "url": "https://two.example/"}],
                },
                {
                    "source_record_key": "hs:1",
                    "name": "Hotel One",
                    "city": "Zürich",
                    "links": [{"type": "other", "url": "https://z.example"}, {"type": "website", "url": "https://one.example/"}],
                },
            ],
        }

    def candidate(self):
        return {
            "api_snapshot_id": "DS-HS-TEST",
            "snapshot_state": "FROZEN_CANDIDATE",
            "crm_freeze_eligible": True,
        }

    def test_export_is_deterministic_and_mass_ingest_compatible(self):
        records = export_candidate_ingest_records(self.candidate(), self.api())
        self.assertEqual(["hs:1", "hs:2"], [r["provider_record_key"] for r in records])
        self.assertEqual("https://one.example/", records[0]["detail_url"])
        self.assertEqual("Hotel One", records[0]["raw_name"])
        self.assertEqual("Zürich", records[0]["raw_city"])
        self.assertEqual("https://api.discover.swiss/info/v2/lodgingbusinesses", records[0]["source_url"])

    def test_non_eligible_candidate_is_rejected(self):
        candidate = self.candidate()
        candidate["crm_freeze_eligible"] = False
        with self.assertRaises(ValueError):
            export_candidate_ingest_records(candidate, self.api())

    def test_snapshot_lineage_mismatch_is_rejected(self):
        candidate = self.candidate()
        candidate["api_snapshot_id"] = "OTHER"
        with self.assertRaises(ValueError):
            export_candidate_ingest_records(candidate, self.api())

    def test_record_count_drift_is_rejected(self):
        api = self.api()
        api["records_count"] = 3
        with self.assertRaises(ValueError):
            export_candidate_ingest_records(self.candidate(), api)

    def test_duplicate_provider_identity_is_rejected(self):
        api = self.api()
        api["records"][1]["source_record_key"] = "hs:2"
        with self.assertRaises(ValueError):
            export_candidate_ingest_records(self.candidate(), api)


if __name__ == "__main__":
    unittest.main()

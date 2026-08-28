import unittest

from swiss_os.member_directory_manifest import compile_member_directory_manifest


class MemberDirectoryManifestTests(unittest.TestCase):
    def _rows(self):
        return [
            {"name": "Hotel A", "city": "Bern", "evidence_ref": "official:p1:a", "locale": "de", "epoch": "E1", "page": 1, "hs_id": "1"},
            {"name": "Hotel B", "city": "Zürich", "evidence_ref": "official:p2:b", "locale": "de", "epoch": "E1", "page": 2, "hs_id": "2"},
        ]

    def test_complete_coherent_manifest_passes(self):
        result = compile_member_directory_manifest(self._rows(), snapshot_id="MD-E1", observed_at="2026-08-28T12:00:00Z", expected_pages=2, declared_raw_records=2)
        self.assertTrue(result["coverage_complete"])
        self.assertEqual(result["observed_pages"], 2)
        self.assertEqual(result["materialized_records"], 2)
        self.assertEqual(result["violations"], [])

    def test_partial_page_coverage_fails_closed(self):
        result = compile_member_directory_manifest(self._rows()[:1], snapshot_id="MD-E1", observed_at="2026-08-28T12:00:00Z", expected_pages=2, declared_raw_records=2)
        self.assertFalse(result["coverage_complete"])
        self.assertTrue(any("observed_pages=" in item for item in result["violations"]))
        self.assertTrue(any("materialized_records=" in item for item in result["violations"]))

    def test_mixed_epoch_fails_closed(self):
        rows = self._rows()
        rows[1]["epoch"] = "E2"
        result = compile_member_directory_manifest(rows, snapshot_id="MD-MIX", observed_at="2026-08-28T12:00:00Z", expected_pages=2, declared_raw_records=2)
        self.assertFalse(result["coverage_complete"])
        self.assertTrue(any(item.startswith("mixed epochs") for item in result["violations"]))

    def test_duplicate_stable_identity_fails_closed(self):
        rows = self._rows()
        rows[1]["hs_id"] = "1"
        result = compile_member_directory_manifest(rows, snapshot_id="MD-E1", observed_at="2026-08-28T12:00:00Z", expected_pages=2, declared_raw_records=2)
        self.assertFalse(result["coverage_complete"])
        self.assertTrue(result["duplicate_identity_keys"])

    def test_page_position_is_not_record_identity(self):
        rows = self._rows()
        first = compile_member_directory_manifest(rows, snapshot_id="MD-E1", observed_at="2026-08-28T12:00:00Z", expected_pages=2, declared_raw_records=2)
        rows[0]["page"], rows[1]["page"] = 2, 1
        second = compile_member_directory_manifest(rows, snapshot_id="MD-E1", observed_at="2026-08-28T12:00:00Z", expected_pages=2, declared_raw_records=2)
        self.assertEqual(first["records_sha256"], second["records_sha256"])


if __name__ == "__main__":
    unittest.main()

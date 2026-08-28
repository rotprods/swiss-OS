import unittest

from swiss_os.member_directory_manifest import compile_member_directory_manifest


class MemberDirectoryManifestTests(unittest.TestCase):
    def _rows(self):
        return [
            {
                "name": "Hotel A",
                "city": "Bern",
                "evidence_ref": "official:p1:a",
                "locale": "de",
                "epoch": "E1",
                "page": 1,
                "hs_id": "1",
            },
            {
                "name": "Hotel B",
                "city": "Zürich",
                "evidence_ref": "official:p2:b",
                "locale": "de",
                "epoch": "E1",
                "page": 2,
                "hs_id": "2",
            },
        ]

    def test_complete_coherent_manifest_passes(self):
        result = compile_member_directory_manifest(
            self._rows(),
            snapshot_id="MD-E1",
            observed_at="2026-08-28T12:00:00Z",
            expected_pages=2,
            declared_raw_records=2,
        )
        self.assertTrue(result["coverage_complete"])
        self.assertEqual(result["observed_pages"], 2)
        self.assertEqual(result["observed_page_values"], [1, 2])
        self.assertEqual(result["missing_pages"], [])
        self.assertEqual(result["out_of_range_pages"], [])
        self.assertEqual(result["materialized_records"], 2)
        self.assertEqual(result["violations"], [])
        self.assertFalse(result["authority_advanced"])
        self.assertEqual(result["h_id_allocations"], 0)
        self.assertFalse(result["outbound_opened"])

    def test_partial_page_coverage_fails_closed(self):
        result = compile_member_directory_manifest(
            self._rows()[:1],
            snapshot_id="MD-E1",
            observed_at="2026-08-28T12:00:00Z",
            expected_pages=2,
            declared_raw_records=2,
        )
        self.assertFalse(result["coverage_complete"])
        self.assertEqual(result["missing_pages"], [2])
        self.assertTrue(any(item.startswith("missing pages") for item in result["violations"]))
        self.assertTrue(any("materialized_records=" in item for item in result["violations"]))

    def test_equal_page_count_cannot_hide_missing_and_out_of_range_pages(self):
        rows = self._rows()
        rows[0]["page"] = 2
        rows[1]["page"] = 3
        result = compile_member_directory_manifest(
            rows,
            snapshot_id="MD-OFF-BY-ONE",
            observed_at="2026-08-28T12:00:00Z",
            expected_pages=2,
            declared_raw_records=2,
        )
        self.assertFalse(result["coverage_complete"])
        self.assertEqual(result["observed_page_values"], [2])
        self.assertEqual(result["missing_pages"], [1])
        self.assertEqual(result["out_of_range_pages"], [3])
        self.assertTrue(any(item.startswith("missing pages") for item in result["violations"]))
        self.assertTrue(any(item.startswith("out-of-range pages") for item in result["violations"]))

    def test_mixed_epoch_fails_closed(self):
        rows = self._rows()
        rows[1]["epoch"] = "E2"
        result = compile_member_directory_manifest(
            rows,
            snapshot_id="MD-MIX",
            observed_at="2026-08-28T12:00:00Z",
            expected_pages=2,
            declared_raw_records=2,
        )
        self.assertFalse(result["coverage_complete"])
        self.assertTrue(any(item.startswith("mixed epochs") for item in result["violations"]))

    def test_duplicate_stable_identity_fails_closed(self):
        rows = self._rows()
        rows[1]["hs_id"] = "1"
        result = compile_member_directory_manifest(
            rows,
            snapshot_id="MD-E1",
            observed_at="2026-08-28T12:00:00Z",
            expected_pages=2,
            declared_raw_records=2,
        )
        self.assertFalse(result["coverage_complete"])
        self.assertTrue(result["duplicate_identity_keys"])

    def test_page_position_is_not_record_identity(self):
        rows = self._rows()
        first = compile_member_directory_manifest(
            rows,
            snapshot_id="MD-E1",
            observed_at="2026-08-28T12:00:00Z",
            expected_pages=2,
            declared_raw_records=2,
        )
        rows[0]["page"], rows[1]["page"] = 2, 1
        second = compile_member_directory_manifest(
            rows,
            snapshot_id="MD-E1",
            observed_at="2026-08-28T12:00:00Z",
            expected_pages=2,
            declared_raw_records=2,
        )
        self.assertEqual(first["records_sha256"], second["records_sha256"])

    def test_page_input_is_a_strict_positive_integer(self):
        for invalid in (True, False, 1.0, "1", 0, -1):
            with self.subTest(invalid=invalid):
                rows = self._rows()
                rows[0]["page"] = invalid
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    compile_member_directory_manifest(
                        rows,
                        snapshot_id="MD-STRICT-PAGE",
                        observed_at="2026-08-28T12:00:00Z",
                        expected_pages=2,
                        declared_raw_records=2,
                    )

    def test_count_inputs_are_strict_positive_integers(self):
        for field in ("expected_pages", "declared_raw_records"):
            for invalid in (True, False, 1.0, "2", 0, -1):
                with self.subTest(field=field, invalid=invalid):
                    kwargs = {
                        "snapshot_id": "MD-STRICT-COUNT",
                        "observed_at": "2026-08-28T12:00:00Z",
                        "expected_pages": 2,
                        "declared_raw_records": 2,
                    }
                    kwargs[field] = invalid
                    with self.assertRaisesRegex(ValueError, "positive integer"):
                        compile_member_directory_manifest(self._rows(), **kwargs)


if __name__ == "__main__":
    unittest.main()

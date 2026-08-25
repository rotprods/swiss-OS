import unittest
from pathlib import Path

from swiss_os.manifest import ManifestError, OperationalManifest

FIXTURE = Path(__file__).parent / "fixtures" / "manifest_superseded.json"


class ManifestTests(unittest.TestCase):
    def test_physical_and_active_counts_are_distinct(self):
        manifest = OperationalManifest.load(FIXTURE)
        self.assertEqual(manifest.sheet_physical_hotel_rows, 677)
        self.assertEqual(manifest.active_canonical_hotels, 673)
        self.assertEqual(manifest.expected_active_from_physical, 673)
        self.assertEqual(manifest.validate(), [])

    def test_invalid_count_fails_closed(self):
        manifest = OperationalManifest.from_dict({
            "release": "x",
            "run_id": "r",
            "sheet_physical_hotel_rows": 10,
            "superseded_duplicate_ids": ["H-0001"],
            "active_canonical_hotels": 10,
            "sqlite_integrity_check": "ok",
            "foreign_key_violations": 0,
            "checkpoint": {"current": 10},
        })
        with self.assertRaises(ManifestError):
            manifest.require_valid()

    def test_legacy_v9_shape_is_supported(self):
        manifest = OperationalManifest.from_dict({
            "release": "V6.3.2",
            "run_id": "RUN-V9",
            "checkpoint": "CP-0750",
            "checks": {
                "sheets_canonical_count": 667,
                "canonical_unique": 667,
                "integrity_check": "ok",
                "foreign_key_violations": 0
            }
        })
        self.assertEqual(manifest.checkpoint_id, "CP-0750")
        self.assertEqual(manifest.sheet_physical_hotel_rows, 667)
        self.assertEqual(manifest.active_canonical_hotels, 667)
        self.assertEqual(manifest.validate(), [])


if __name__ == "__main__":
    unittest.main()

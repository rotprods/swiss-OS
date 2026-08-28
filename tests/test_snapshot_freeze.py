import unittest

from swiss_os.snapshot_freeze import (
    SnapshotFreezeCandidate,
    SnapshotSourceRecord,
    build_snapshot_record_id,
    validate_snapshot_freeze,
)


class SnapshotRecordIdentityTests(unittest.TestCase):
    def test_detail_url_produces_stable_identity_independent_of_page_position(self) -> None:
        a = SnapshotSourceRecord(
            source_url="https://example.invalid/directory/hotel-page-15",
            raw_name="Hotel Alpha",
            raw_city="Bern",
            detail_url="https://example.invalid/hotel/hotel-alpha/",
        )
        b = SnapshotSourceRecord(
            source_url="https://example.invalid/directory/hotel-page-99",
            raw_name="Hotel Alpha",
            raw_city="Bern",
            detail_url="https://example.invalid/hotel/hotel-alpha",
        )
        self.assertEqual(
            build_snapshot_record_id("HS-FROZEN-1", a),
            build_snapshot_record_id("HS-FROZEN-1", b),
        )

    def test_same_record_in_different_snapshot_gets_different_snapshot_record_id(self) -> None:
        record = SnapshotSourceRecord(
            source_url="https://example.invalid/directory",
            raw_name="Hotel Alpha",
            raw_city="Bern",
            detail_url="https://example.invalid/hotel/hotel-alpha",
        )
        self.assertNotEqual(
            build_snapshot_record_id("HS-FROZEN-1", record),
            build_snapshot_record_id("HS-FROZEN-2", record),
        )

    def test_provider_key_takes_precedence(self) -> None:
        record = SnapshotSourceRecord(
            source_url="https://example.invalid/page-5",
            raw_name="Display Name Can Drift",
            raw_city="Bern",
            provider_record_key="provider-123",
        )
        self.assertEqual(record.stable_source_record_key(), "provider:provider-123")

    def test_fallback_requires_source_and_name(self) -> None:
        with self.assertRaises(ValueError):
            SnapshotSourceRecord(source_url="", raw_name="", raw_city="").stable_source_record_key()


class SnapshotFreezeTests(unittest.TestCase):
    def _candidate(self, **overrides) -> SnapshotFreezeCandidate:
        values = dict(
            snapshot_id="HS-FROZEN-1",
            locale="de-CH",
            source_url="https://example.invalid/directory",
            expected_pages=171,
            observed_pages=171,
            declared_raw_records=2050,
            materialized_records=2050,
            duplicate_source_record_keys=0,
            unresolved_snapshot_conflicts=0,
            missing_record_identity=0,
        )
        values.update(overrides)
        return SnapshotFreezeCandidate(**values)

    def test_complete_coherent_snapshot_is_freeze_eligible(self) -> None:
        result = validate_snapshot_freeze(self._candidate())
        self.assertTrue(result.eligible)
        self.assertEqual(result.violations, ())

    def test_partial_page_harvest_fails(self) -> None:
        result = validate_snapshot_freeze(self._candidate(observed_pages=55))
        self.assertFalse(result.eligible)
        self.assertIn("all pages in the selected snapshot must be observed", result.violations)

    def test_declared_record_mismatch_fails(self) -> None:
        result = validate_snapshot_freeze(self._candidate(materialized_records=2049))
        self.assertFalse(result.eligible)
        self.assertIn(
            "materialized source records must equal declared raw records",
            result.violations,
        )

    def test_conflict_or_duplicate_blocks_freeze(self) -> None:
        result = validate_snapshot_freeze(
            self._candidate(
                duplicate_source_record_keys=1,
                unresolved_snapshot_conflicts=4,
            )
        )
        self.assertFalse(result.eligible)
        self.assertIn("duplicate source record keys must be zero", result.violations)
        self.assertIn("unresolved snapshot conflicts must be zero", result.violations)


if __name__ == "__main__":
    unittest.main()

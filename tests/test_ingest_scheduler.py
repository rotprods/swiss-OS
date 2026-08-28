import sqlite3
import unittest

from swiss_os.db import initialize
from swiss_os.ingest_scheduler import enqueue_ingest_work, task_for_decision
from swiss_os.mass_ingest import (
    ACTIVE_MATCH,
    ALIAS_MATCH,
    CONFLICT,
    EXCLUSION_CANDIDATE,
    TRUE_MISSING,
    IngestDecision,
)


def _decision(staging_class: str, record_id: str = "SR-1") -> IngestDecision:
    return IngestDecision(
        snapshot_record_id=record_id,
        snapshot_id="SNAP-1",
        source_record_key=f"key:{record_id}",
        staging_class=staging_class,
        matched_hotel_id="H-0001" if staging_class in {ACTIVE_MATCH, ALIAS_MATCH} else None,
        reason_code="TEST",
        normalized_name="hotel test",
        normalized_city="bern",
        normalized_detail_url="",
    )


class IngestSchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        initialize(self.conn)

    def tearDown(self) -> None:
        self.conn.close()

    def test_true_missing_routes_to_exact_current_refresh(self) -> None:
        spec = task_for_decision(_decision(TRUE_MISSING))
        self.assertIsNotNone(spec)
        self.assertEqual(spec.task_type, "REFRESH_EXACT_CURRENT")
        self.assertEqual(spec.priority, 900)

    def test_conflict_has_higher_priority_entity_resolution(self) -> None:
        spec = task_for_decision(_decision(CONFLICT))
        self.assertEqual(spec.task_type, "ENTITY_RESOLUTION")
        self.assertEqual(spec.priority, 950)

    def test_exclusion_candidate_routes_to_review(self) -> None:
        spec = task_for_decision(_decision(EXCLUSION_CANDIDATE))
        self.assertEqual(spec.task_type, "EXCLUSION_REVIEW")

    def test_active_and_alias_matches_do_not_create_scheduler_noise(self) -> None:
        self.assertIsNone(task_for_decision(_decision(ACTIVE_MATCH)))
        self.assertIsNone(task_for_decision(_decision(ALIAS_MATCH)))

    def test_enqueue_is_idempotent_for_snapshot_freshness(self) -> None:
        decisions = [
            _decision(TRUE_MISSING, "SR-1"),
            _decision(CONFLICT, "SR-2"),
            _decision(EXCLUSION_CANDIDATE, "SR-3"),
            _decision(ACTIVE_MATCH, "SR-4"),
        ]
        first = enqueue_ingest_work(self.conn, decisions)
        second = enqueue_ingest_work(self.conn, decisions)
        self.assertEqual(first["CREATED"], 3)
        self.assertEqual(first["NO_TASK_REQUIRED"], 1)
        self.assertEqual(second["CREATED"], 0)
        self.assertEqual(second["SKIPPED_EXISTING_OR_COMPLETE"], 3)
        count = self.conn.execute("SELECT COUNT(*) FROM scheduler_tasks").fetchone()[0]
        self.assertEqual(count, 3)


if __name__ == "__main__":
    unittest.main()

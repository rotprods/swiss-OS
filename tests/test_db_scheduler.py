import sqlite3
import tempfile
import unittest

from swiss_os.db import active_hotel_ids, connect, foreign_key_violations, initialize, integrity_check
from swiss_os.scheduler import TaskSpec, enqueue_if_needed


class DbSchedulerTests(unittest.TestCase):
    def test_schema_integrity_and_active_filter(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as tmp:
            conn = connect(tmp.name)
            initialize(conn)
            conn.execute(
                "INSERT INTO canonical_hotels(hotel_id, canonical_name, city, state, source_ref) VALUES (?,?,?,?,?)",
                ("H-0001", "A", "Bern", "ACTIVE", "fixture"),
            )
            conn.execute(
                "INSERT INTO canonical_hotels(hotel_id, canonical_name, city, state, superseded_by, source_ref) VALUES (?,?,?,?,?,?)",
                ("H-0002", "A old", "Bern", "SUPERSEDED_DUPLICATE", "H-0001", "fixture"),
            )
            conn.commit()
            self.assertEqual(active_hotel_ids(conn), {"H-0001"})
            self.assertEqual(integrity_check(conn), "ok")
            self.assertEqual(foreign_key_violations(conn), [])
            conn.close()

    def test_scheduler_anti_join_and_freshness(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as tmp:
            conn = connect(tmp.name)
            initialize(conn)
            spec = TaskSpec("T-1", "H-0001", "VERIFY_VACANCY", 100, freshness_key="2026-08-25")
            self.assertTrue(enqueue_if_needed(conn, spec))
            self.assertFalse(enqueue_if_needed(conn, TaskSpec("T-2", "H-0001", "VERIFY_VACANCY", 100, freshness_key="2026-08-25")))
            conn.execute("UPDATE scheduler_tasks SET state='COMPLETE' WHERE task_id='T-1'")
            conn.commit()
            self.assertFalse(enqueue_if_needed(conn, TaskSpec("T-3", "H-0001", "VERIFY_VACANCY", 100, freshness_key="2026-08-25")))
            self.assertTrue(enqueue_if_needed(conn, TaskSpec("T-4", "H-0001", "VERIFY_VACANCY", 100, freshness_key="2026-09-01")))
            conn.close()

    def test_run_record_hard_locks_send_allowed_to_zero(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as tmp:
            conn = connect(tmp.name)
            initialize(conn)
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """INSERT INTO run_records(
                    run_id, goal_id, checkpoint_id, canonical_before, canonical_after,
                    db_integrity, fk_violations, duplicate_count, snapshot_drift,
                    send_allowed_count, quality_result, created_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    ("RUN-1", "G-0001", "CP-0750", 673, 673, "ok", 0, 0, 0, 1, "PASS", "now"),
                )
            conn.close()


if __name__ == "__main__":
    unittest.main()

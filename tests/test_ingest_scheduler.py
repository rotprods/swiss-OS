import sqlite3
import unittest

from swiss_os.db import initialize
from swiss_os.ingest_scheduler import enqueue_ingest_work, task_for_decision
from swiss_os.mass_ingest import ACTIVE_MATCH, ALIAS_MATCH, CONFLICT, EXCLUSION_CANDIDATE, TRUE_MISSING, IngestDecision

def decision(cls, rid="SR-1"):
    return IngestDecision(rid,"SNAP-1",f"key:{rid}",cls,"H-0001" if cls in {ACTIVE_MATCH,ALIAS_MATCH} else None,"TEST","hotel","bern","")

class IngestSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(":memory:")
        initialize(self.conn)
    def tearDown(self): self.conn.close()
    def test_routes(self):
        self.assertEqual(task_for_decision(decision(TRUE_MISSING)).task_type,"REFRESH_EXACT_CURRENT")
        self.assertEqual(task_for_decision(decision(CONFLICT)).task_type,"ENTITY_RESOLUTION")
        self.assertEqual(task_for_decision(decision(EXCLUSION_CANDIDATE)).task_type,"EXCLUSION_REVIEW")
        self.assertIsNone(task_for_decision(decision(ACTIVE_MATCH)))
        self.assertIsNone(task_for_decision(decision(ALIAS_MATCH)))
    def test_enqueue_idempotent(self):
        ds=[decision(TRUE_MISSING,"SR-1"),decision(CONFLICT,"SR-2"),decision(EXCLUSION_CANDIDATE,"SR-3"),decision(ACTIVE_MATCH,"SR-4")]
        first=enqueue_ingest_work(self.conn,ds)
        second=enqueue_ingest_work(self.conn,ds)
        self.assertEqual(first["CREATED"],3)
        self.assertEqual(first["NO_TASK_REQUIRED"],1)
        self.assertEqual(second["CREATED"],0)
        self.assertEqual(second["SKIPPED_EXISTING_OR_COMPLETE"],3)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM scheduler_tasks").fetchone()[0],3)

if __name__ == "__main__": unittest.main()

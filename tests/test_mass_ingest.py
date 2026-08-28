import sqlite3
import unittest

from swiss_os.db import initialize
from swiss_os.mass_ingest import ACTIVE_MATCH, ALIAS_MATCH, CONFLICT, TRUE_MISSING, AliasIdentity, CanonicalIdentity, classify_batch, classify_source_record, stage_decisions, staging_metrics
from swiss_os.snapshot_freeze import SnapshotSourceRecord

class MassIngestClassificationTests(unittest.TestCase):
    def setUp(self):
        self.canonical = [CanonicalIdentity("H-0001", "Hotel Alpha", "Bern", "alpha.ch"), CanonicalIdentity("H-0002", "Hotel Beta", "Zürich", "beta.ch")]
        self.aliases = [AliasIdentity("H-0002", "Beta Zürich", "Zürich")]
    def test_domain_match_has_highest_precedence(self):
        d = classify_source_record("S1", SnapshotSourceRecord("https://directory.invalid/page-1", "Different", "Elsewhere", "https://www.alpha.ch/jobs"), self.canonical, self.aliases)
        self.assertEqual((d.staging_class, d.matched_hotel_id), (ACTIVE_MATCH, "H-0001"))
    def test_name_city_match(self):
        d = classify_source_record("S1", SnapshotSourceRecord("https://directory.invalid", " Hotel Alpha ", "BERN"), self.canonical, self.aliases)
        self.assertEqual(d.staging_class, ACTIVE_MATCH)
    def test_alias_match(self):
        d = classify_source_record("S1", SnapshotSourceRecord("https://directory.invalid", "Beta Zürich", "Zürich"), self.canonical, self.aliases)
        self.assertEqual((d.staging_class, d.matched_hotel_id), (ALIAS_MATCH, "H-0002"))
    def test_unknown_is_true_missing_without_id(self):
        d = classify_source_record("S1", SnapshotSourceRecord("https://directory.invalid", "Hotel Gamma", "Luzern"), self.canonical, self.aliases)
        self.assertEqual(d.staging_class, TRUE_MISSING)
        self.assertIsNone(d.matched_hotel_id)
    def test_ambiguous_fails_closed(self):
        canonical = self.canonical + [CanonicalIdentity("H-0003", "Hotel Alpha", "Bern")]
        d = classify_source_record("S1", SnapshotSourceRecord("https://directory.invalid", "Hotel Alpha", "Bern"), canonical, self.aliases)
        self.assertEqual(d.staging_class, CONFLICT)

class MassIngestPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON")
        initialize(self.conn)
        self.conn.execute("INSERT INTO canonical_hotels (hotel_id, canonical_name, city, canonical_domain, state, source_ref) VALUES ('H-0001','Hotel Alpha','Bern','alpha.ch','ACTIVE','seed')")
        self.conn.execute("INSERT INTO entity_aliases (alias_id, canonical_hotel_id, alias_name, alias_city, reason_code, source_ref) VALUES ('A-1','H-0001','Alpha Bern','Bern','TEST_ALIAS','seed')")
        self.conn.commit()
    def tearDown(self): self.conn.close()
    def test_batch_stage_and_no_h_id_allocation(self):
        records = [SnapshotSourceRecord("https://directory.invalid","Hotel Alpha","Bern"), SnapshotSourceRecord("https://directory.invalid","Alpha Bern","Bern"), SnapshotSourceRecord("https://directory.invalid","Hotel New","Lugano")]
        decisions = classify_batch(self.conn, "SNAP-1", records)
        metrics = staging_metrics(decisions)
        self.assertEqual((metrics[ACTIVE_MATCH], metrics[ALIAS_MATCH], metrics[TRUE_MISSING], metrics["H_ID_ALLOCATIONS"]), (1,1,1,0))
        stage_decisions(self.conn, decisions, "2026-08-28T13:30:00+02:00")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM crm_ingest_staging").fetchone()[0], 3)
    def test_stage_is_idempotent(self):
        decisions = classify_batch(self.conn, "SNAP-1", [SnapshotSourceRecord("https://directory.invalid","Hotel New","Lugano")])
        stage_decisions(self.conn, decisions, "2026-08-28T13:30:00+02:00")
        stage_decisions(self.conn, decisions, "2026-08-28T13:31:00+02:00")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM crm_ingest_staging").fetchone()[0], 1)

if __name__ == "__main__": unittest.main()

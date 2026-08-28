import sqlite3
import unittest

from swiss_os.db import initialize
from swiss_os.mass_ingest import (
    ALIAS_MATCH,
    ACTIVE_MATCH,
    CONFLICT,
    TRUE_MISSING,
    AliasIdentity,
    CanonicalIdentity,
    classify_batch,
    classify_source_record,
    stage_decisions,
    staging_metrics,
)
from swiss_os.snapshot_freeze import SnapshotSourceRecord


class MassIngestClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.canonical = [
            CanonicalIdentity("H-0001", "Hotel Alpha", "Bern", "alpha.ch"),
            CanonicalIdentity("H-0002", "Hotel Beta", "Zürich", "beta.ch"),
        ]
        self.aliases = [AliasIdentity("H-0002", "Beta Zürich", "Zürich")]

    def test_domain_match_has_highest_precedence(self) -> None:
        record = SnapshotSourceRecord(
            source_url="https://directory.invalid/page-1",
            raw_name="Completely Different Display Name",
            raw_city="Elsewhere",
            detail_url="https://www.alpha.ch/jobs",
        )
        decision = classify_source_record("S1", record, self.canonical, self.aliases)
        self.assertEqual(decision.staging_class, ACTIVE_MATCH)
        self.assertEqual(decision.matched_hotel_id, "H-0001")
        self.assertEqual(decision.reason_code, "EXACT_CANONICAL_DOMAIN")

    def test_exact_name_city_matches_canonical(self) -> None:
        record = SnapshotSourceRecord("https://directory.invalid", " Hotel Alpha ", "BERN")
        decision = classify_source_record("S1", record, self.canonical, self.aliases)
        self.assertEqual(decision.staging_class, ACTIVE_MATCH)
        self.assertEqual(decision.matched_hotel_id, "H-0001")

    def test_alias_match_is_distinct_from_canonical_match(self) -> None:
        record = SnapshotSourceRecord("https://directory.invalid", "Beta Zürich", "Zürich")
        decision = classify_source_record("S1", record, self.canonical, self.aliases)
        self.assertEqual(decision.staging_class, ALIAS_MATCH)
        self.assertEqual(decision.matched_hotel_id, "H-0002")

    def test_unknown_record_is_true_missing_without_h_id(self) -> None:
        record = SnapshotSourceRecord("https://directory.invalid", "Hotel Gamma", "Luzern")
        decision = classify_source_record("S1", record, self.canonical, self.aliases)
        self.assertEqual(decision.staging_class, TRUE_MISSING)
        self.assertIsNone(decision.matched_hotel_id)

    def test_ambiguous_name_city_fails_closed(self) -> None:
        canonical = self.canonical + [CanonicalIdentity("H-0003", "Hotel Alpha", "Bern", "")]
        record = SnapshotSourceRecord("https://directory.invalid", "Hotel Alpha", "Bern")
        decision = classify_source_record("S1", record, canonical, self.aliases)
        self.assertEqual(decision.staging_class, CONFLICT)
        self.assertIsNone(decision.matched_hotel_id)


class MassIngestPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON")
        initialize(self.conn)
        self.conn.execute(
            """
            INSERT INTO canonical_hotels (
                hotel_id, canonical_name, city, canonical_domain, state, source_ref
            ) VALUES ('H-0001', 'Hotel Alpha', 'Bern', 'alpha.ch', 'ACTIVE', 'seed')
            """
        )
        self.conn.execute(
            """
            INSERT INTO entity_aliases (
                alias_id, canonical_hotel_id, alias_name, alias_city, reason_code, source_ref
            ) VALUES ('A-1', 'H-0001', 'Alpha Bern', 'Bern', 'TEST_ALIAS', 'seed')
            """
        )
        self.conn.commit()

    def tearDown(self) -> None:
        self.conn.close()

    def test_batch_classifies_and_stages_without_allocating_h_ids(self) -> None:
        records = [
            SnapshotSourceRecord("https://directory.invalid", "Hotel Alpha", "Bern"),
            SnapshotSourceRecord("https://directory.invalid", "Alpha Bern", "Bern"),
            SnapshotSourceRecord("https://directory.invalid", "Hotel New", "Lugano"),
        ]
        decisions = classify_batch(self.conn, "SNAP-1", records)
        metrics = staging_metrics(decisions)
        self.assertEqual(metrics[ACTIVE_MATCH], 1)
        self.assertEqual(metrics[ALIAS_MATCH], 1)
        self.assertEqual(metrics[TRUE_MISSING], 1)
        self.assertEqual(metrics["H_ID_ALLOCATIONS"], 0)

        stage_decisions(self.conn, decisions, "2026-08-28T13:30:00+02:00")
        rows = self.conn.execute(
            "SELECT staging_class, matched_hotel_id FROM crm_ingest_staging ORDER BY staging_class"
        ).fetchall()
        self.assertEqual(len(rows), 3)

    def test_staging_upsert_is_idempotent(self) -> None:
        records = [SnapshotSourceRecord("https://directory.invalid", "Hotel New", "Lugano")]
        decisions = classify_batch(self.conn, "SNAP-1", records)
        stage_decisions(self.conn, decisions, "2026-08-28T13:30:00+02:00")
        stage_decisions(self.conn, decisions, "2026-08-28T13:31:00+02:00")
        count = self.conn.execute("SELECT COUNT(*) FROM crm_ingest_staging").fetchone()[0]
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()

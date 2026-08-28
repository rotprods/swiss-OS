import sqlite3
import unittest

from swiss_os.crm_universe import inspect_crm_snapshot
from swiss_os.db import initialize


def _memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    initialize(conn)
    return conn


def _insert_snapshot(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO crm_snapshots (
            snapshot_id, source_url, locale, observed_at, raw_directory_count,
            page_count, source_scope, snapshot_state, created_at, frozen_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "HS-SNAPSHOT-1",
            "https://example.invalid/directory",
            "de-CH",
            "2026-08-28T12:00:00+02:00",
            2,
            1,
            "HOTELLERIESUISSE_DIRECTORY",
            "FROZEN_VERIFIED",
            "2026-08-28T12:00:00+02:00",
            "2026-08-28T12:01:00+02:00",
        ),
    )


def _insert_record(conn: sqlite3.Connection, record_id: str, source_key: str) -> None:
    conn.execute(
        """
        INSERT INTO crm_snapshot_records (
            snapshot_record_id, snapshot_id, source_record_key, source_url,
            raw_name, raw_city, normalized_name, normalized_city,
            observed_at, evidence_ref
        ) VALUES (?, 'HS-SNAPSHOT-1', ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record_id,
            source_key,
            f"https://example.invalid/{source_key}",
            f"Hotel {source_key}",
            "Bern",
            f"hotel {source_key.lower()}",
            "bern",
            "2026-08-28T12:00:00+02:00",
            f"E-{source_key}",
        ),
    )


class CRMSnapshotSchemaTests(unittest.TestCase):
    def test_snapshot_record_key_is_unique_within_snapshot(self) -> None:
        conn = _memory_db()
        _insert_snapshot(conn)
        _insert_record(conn, "SR-1", "A")
        with self.assertRaises(sqlite3.IntegrityError):
            _insert_record(conn, "SR-2", "A")

    def test_terminal_canonical_mapping_requires_existing_hotel(self) -> None:
        conn = _memory_db()
        _insert_snapshot(conn)
        _insert_record(conn, "SR-1", "A")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO crm_source_mappings (
                    snapshot_record_id, mapping_state, canonical_hotel_id,
                    evidence_ref, mapped_at
                ) VALUES ('SR-1', 'ACTIVE_CANONICAL', 'H-9999', 'E-A', '2026-08-28T12:02:00+02:00')
                """
            )

    def test_exclusion_requires_reason(self) -> None:
        conn = _memory_db()
        _insert_snapshot(conn)
        _insert_record(conn, "SR-1", "A")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO crm_source_mappings (
                    snapshot_record_id, mapping_state, evidence_ref, mapped_at
                ) VALUES ('SR-1', 'EXCLUDED_WITH_REASON', 'E-A', '2026-08-28T12:02:00+02:00')
                """
            )

    def test_reconcile_required_requires_reason_and_is_not_terminal_complete(self) -> None:
        conn = _memory_db()
        _insert_snapshot(conn)
        _insert_record(conn, "SR-1", "A")
        conn.execute(
            """
            INSERT INTO crm_source_mappings (
                snapshot_record_id, mapping_state, reconcile_reason,
                evidence_ref, mapped_at
            ) VALUES (
                'SR-1', 'RECONCILE_REQUIRED', 'current identity conflict',
                'E-A', '2026-08-28T12:02:00+02:00'
            )
            """
        )
        state = conn.execute(
            "SELECT mapping_state FROM crm_source_mappings WHERE snapshot_record_id = 'SR-1'"
        ).fetchone()[0]
        self.assertEqual(state, "RECONCILE_REQUIRED")

    def test_one_mapping_per_snapshot_record(self) -> None:
        conn = _memory_db()
        _insert_snapshot(conn)
        _insert_record(conn, "SR-1", "A")
        conn.execute(
            """
            INSERT INTO crm_source_mappings (
                snapshot_record_id, mapping_state, exclusion_reason,
                evidence_ref, mapped_at
            ) VALUES (
                'SR-1', 'EXCLUDED_WITH_REASON', 'out of scope',
                'E-A', '2026-08-28T12:02:00+02:00'
            )
            """
        )
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO crm_source_mappings (
                    snapshot_record_id, mapping_state, exclusion_reason,
                    evidence_ref, mapped_at
                ) VALUES (
                    'SR-1', 'EXCLUDED_WITH_REASON', 'duplicate',
                    'E-A2', '2026-08-28T12:03:00+02:00'
                )
                """
            )

    def test_inspect_snapshot_separates_declared_and_materialized_coverage(self) -> None:
        conn = _memory_db()
        _insert_snapshot(conn)
        _insert_record(conn, "SR-1", "A")
        conn.execute(
            """
            INSERT INTO crm_source_mappings (
                snapshot_record_id, mapping_state, exclusion_reason,
                evidence_ref, mapped_at
            ) VALUES (
                'SR-1', 'EXCLUDED_WITH_REASON', 'out of scope',
                'E-A', '2026-08-28T12:02:00+02:00'
            )
            """
        )
        stats = inspect_crm_snapshot(conn, "HS-SNAPSHOT-1")
        self.assertEqual(stats.declared_raw_directory_count, 2)
        self.assertEqual(stats.materialized_source_records, 1)
        self.assertEqual(stats.terminal_mapped_records, 1)
        self.assertEqual(stats.unmapped_records, 0)
        self.assertEqual(stats.materialized_coverage_pct, 1.0)
        self.assertEqual(stats.declared_coverage_pct, 0.5)

    def test_inspect_snapshot_counts_unmapped_materialized_records(self) -> None:
        conn = _memory_db()
        _insert_snapshot(conn)
        _insert_record(conn, "SR-1", "A")
        _insert_record(conn, "SR-2", "B")
        conn.execute(
            """
            INSERT INTO crm_source_mappings (
                snapshot_record_id, mapping_state, reconcile_reason,
                evidence_ref, mapped_at
            ) VALUES (
                'SR-1', 'RECONCILE_REQUIRED', 'identity conflict',
                'E-A', '2026-08-28T12:02:00+02:00'
            )
            """
        )
        stats = inspect_crm_snapshot(conn, "HS-SNAPSHOT-1")
        self.assertEqual(stats.materialized_source_records, 2)
        self.assertEqual(stats.reconcile_required, 1)
        self.assertEqual(stats.unmapped_records, 1)
        self.assertEqual(stats.terminal_mapped_records, 0)


if __name__ == "__main__":
    unittest.main()

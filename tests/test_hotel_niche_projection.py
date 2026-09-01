import sqlite3
import unittest
from pathlib import Path

from swiss_os.hotel_niche_projection import (
    compatibility_receipt,
    materialize_canary,
    organization_id_for_hotel,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "src" / "swiss_os" / "schema.sql"
OVERLAY = ROOT / "src" / "swiss_os" / "multi_niche_schema.sql"


def build_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(BASE.read_text())
    db.executescript(OVERLAY.read_text())
    hotels = [
        ("H-0001", "Hotel Victoria", "Brig", "Valais", "Switzerland", "victoria-brig.ch", "ACTIVE", "E-1", 0.99),
        ("H-0002", "Hotel Victoria", "Basel", "Basel-Stadt", "Switzerland", "victoria-basel.ch", "ACTIVE", "E-2", 0.98),
        ("H-0003", "Legacy Lodge", "Bern", "Bern", "Switzerland", None, "QUARANTINED", "E-3", 0.80),
    ]
    db.executemany(
        """INSERT INTO canonical_hotels(
             hotel_id,canonical_name,city,canton,country,canonical_domain,
             state,source_ref,identity_confidence
           ) VALUES(?,?,?,?,?,?,?,?,?)""",
        hotels,
    )
    db.commit()
    return db


class HotelNicheProjectionTests(unittest.TestCase):
    def test_deterministic_org_id(self):
        self.assertEqual(organization_id_for_hotel("H-0690"), "ORG-HOTEL-0690")
        with self.assertRaises(ValueError):
            organization_id_for_hotel("HOTEL-690")

    def test_materialization_is_1_to_1_and_integrity_clean(self):
        db = build_db()
        self.assertEqual(materialize_canary(db, "W2-FIXTURE"), 3)
        receipt = compatibility_receipt(db)
        self.assertTrue(receipt["pass"], receipt)
        self.assertEqual(receipt["legacy_hotels"], 3)
        self.assertEqual(receipt["niche001_organizations"], 3)
        self.assertEqual(receipt["bridge_rows"], 3)
        self.assertEqual(receipt["integrity_check"], "ok")
        self.assertEqual(receipt["fk_violations"], 0)

    def test_same_name_different_city_remains_distinct(self):
        db = build_db()
        materialize_canary(db, "W2-FIXTURE")
        rows = db.execute(
            """SELECT o.organization_id,l.city
               FROM organizations o JOIN organization_locations l USING(organization_id)
               WHERE o.canonical_name='Hotel Victoria' ORDER BY l.city"""
        ).fetchall()
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(rows[0][0], rows[1][0])

    def test_rerun_is_idempotent(self):
        db = build_db()
        materialize_canary(db, "W2-FIXTURE")
        materialize_canary(db, "W2-FIXTURE")
        receipt = compatibility_receipt(db)
        self.assertTrue(receipt["pass"], receipt)
        self.assertEqual(receipt["bridge_rows"], 3)

    def test_preexisting_drift_is_not_overwritten_and_fails_closed(self):
        db = build_db()
        materialize_canary(db, "W2-FIXTURE")
        db.execute("UPDATE organization_locations SET city='Wrong City' WHERE organization_id='ORG-HOTEL-0001'")
        db.commit()
        materialize_canary(db, "W2-FIXTURE")
        receipt = compatibility_receipt(db)
        self.assertFalse(receipt["pass"])
        self.assertIn(
            {"hotel_id": "H-0001", "mismatch": "CITY"},
            receipt["semantic_mismatches"],
        )

    def test_bridge_fk_blocks_nonexistent_authority_rows(self):
        db = build_db()
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute(
                """INSERT INTO legacy_hotel_org_bridge(
                     hotel_id,organization_id,bridge_state,evidence_ref
                   ) VALUES('H-9999','ORG-HOTEL-9999','CANARY','E-X')"""
            )


if __name__ == "__main__":
    unittest.main()

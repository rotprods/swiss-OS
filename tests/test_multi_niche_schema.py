import sqlite3
import unittest
from pathlib import Path

from swiss_os.niche_contract import HOTELS_V1, NicheContract

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'src' / 'swiss_os' / 'schema.sql'
OVERLAY = ROOT / 'src' / 'swiss_os' / 'multi_niche_schema.sql'


def build_db():
    conn = sqlite3.connect(':memory:')
    conn.executescript(BASE.read_text())
    conn.executescript(OVERLAY.read_text())
    return conn


class MultiNicheSchemaTests(unittest.TestCase):
    def test_overlay_is_additive_and_integrity_clean(self):
        db = build_db()
        self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn('canonical_hotels', tables)
        self.assertIn('organizations', tables)
        self.assertIn('legacy_hotel_org_bridge', tables)

    def test_hotels_seeded_as_niche_001(self):
        db = build_db()
        row = db.execute("SELECT niche_id,slug,state FROM niches WHERE niche_id='NICHE-001'").fetchone()
        self.assertEqual(row, ('NICHE-001','hotels','ACTIVE'))

    def test_bridge_cannot_reference_missing_hotel_or_org(self):
        db = build_db()
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute("INSERT INTO legacy_hotel_org_bridge VALUES('H-0001','ORG-X','CANARY','E-1',NULL)")

    def test_contract_validates(self):
        HOTELS_V1.validate()
        invalid = NicheContract(
            'bad','x','1',frozenset({'X'}),frozenset(),
            frozenset({'CURRENT'}),frozenset(),frozenset({'ENTRY'})
        )
        with self.assertRaises(ValueError):
            invalid.validate()


if __name__ == '__main__':
    unittest.main()

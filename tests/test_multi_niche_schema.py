import sqlite3
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


def test_overlay_is_additive_and_integrity_clean():
    db = build_db()
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert db.execute('PRAGMA foreign_key_check').fetchall() == []
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert 'canonical_hotels' in tables
    assert 'organizations' in tables
    assert 'legacy_hotel_org_bridge' in tables


def test_hotels_seeded_as_niche_001():
    db = build_db()
    row = db.execute("SELECT niche_id,slug,state FROM niches WHERE niche_id='NICHE-001'").fetchone()
    assert row == ('NICHE-001','hotels','ACTIVE')


def test_bridge_cannot_reference_missing_hotel_or_org():
    db = build_db()
    try:
        db.execute("INSERT INTO legacy_hotel_org_bridge VALUES('H-0001','ORG-X','CANARY','E-1',NULL)")
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError('bridge accepted nonexistent authority entities')


def test_contract_validates():
    HOTELS_V1.validate()
    try:
        NicheContract('bad','x','1',frozenset({'X'}),frozenset(),frozenset({'CURRENT'}),frozenset(),frozenset({'ENTRY'})).validate()
    except ValueError:
        pass
    else:
        raise AssertionError('invalid niche id accepted')

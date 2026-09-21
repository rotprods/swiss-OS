import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "src" / "swiss_os" / "schema.sql"
V2 = ROOT / "src" / "swiss_os" / "multi_niche_schema.sql"
V3 = ROOT / "src" / "swiss_os" / "employment_market_schema_v3.sql"


def build_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(BASE.read_text())
    conn.executescript(V2.read_text())
    conn.executescript(V3.read_text())
    return conn


def seed_surface(db):
    db.execute("INSERT INTO source_families_v1 VALUES(?,?,?,?)",
               ("FAM-T","Test Family","Test Provider","PRIVATE_PLATFORM"))
    db.execute(
        "INSERT INTO source_surfaces_v1 VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        ("SRC-T","FAM-T","Test Jobs","https://example.test/jobs","NATIONAL_JOB_BOARD",
         "TEST_MULTI_NICHE",1,"UNKNOWN_REQUIRES_REVIEW","DISCOVERY","NONE","2026-09-21T00:00:00Z")
    )
    db.execute(
        "INSERT INTO source_snapshots_v3 VALUES(?,?,?,?,?,?,?,?)",
        ("SNAP-1","SRC-T","2026-09-21T00:00:00Z","FIXTURE_ONLY","a"*64,"test-v1",
         "CAPTURED","CURRENT_SNAPSHOT")
    )


def seed_two_source_records(db):
    seed_surface(db)
    for rid, key, url in (
        ("SR-1","JOB-42","https://example.test/jobs/42"),
        ("SR-2","JOB-42-MIRROR","https://example.test/jobs/42?mirror=1"),
    ):
        db.execute(
            "INSERT INTO vacancy_source_records_v1 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rid,"SNAP-1","SRC-T",key,url,"Housekeeping Attendant","Hotel Example",
             "Zurich",None,"2026-09-21T00:00:00Z","b"*64,f"fixture://{rid}","PARSED","fixture")
        )
        db.execute(
            "INSERT INTO normalized_vacancy_candidates_v1 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("NVC-"+rid,rid,"Housekeeping Attendant","Hotel Example","Zurich","ZH","PERMANENT",
             80,100,None,None,"test-v1","NORMALIZED")
        )


class EmploymentMarketSchemaV3Tests(unittest.TestCase):
    def test_overlay_is_additive_and_integrity_clean(self):
        db = build_db()
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for expected in (
            "opportunities_v2","source_snapshots_v2","source_families_v1","source_surfaces_v1",
            "source_snapshots_v3","vacancy_source_records_v1","normalized_vacancy_candidates_v1",
            "canonical_vacancies_v1","canonical_vacancy_sources_v1","opportunities_v3"
        ):
            self.assertIn(expected, tables)
        self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_cross_niche_surface_has_one_snapshot_not_per_niche(self):
        db = build_db()
        seed_surface(db)
        db.execute("INSERT INTO niches VALUES(?,?,?,?,?,?)", ("NICHE-002","retail","Retail","ACTIVE","TEST-1","2026-09-21T00:00:00Z"))
        db.execute("INSERT INTO source_surface_niches_v1 VALUES(?,?,?)", ("SRC-T","NICHE-001","OBSERVED"))
        db.execute("INSERT INTO source_surface_niches_v1 VALUES(?,?,?)", ("SRC-T","NICHE-002","OBSERVED"))
        self.assertEqual(db.execute(
            "SELECT COUNT(*) FROM source_surface_niches_v1 WHERE source_surface_id='SRC-T'"
        ).fetchone()[0], 2)
        self.assertEqual(db.execute(
            "SELECT COUNT(*) FROM source_snapshots_v3 WHERE source_surface_id='SRC-T'"
        ).fetchone()[0], 1)

    def test_two_source_records_can_preserve_lineage_for_one_canonical_vacancy(self):
        db = build_db()
        seed_two_source_records(db)
        db.execute(
            "INSERT INTO canonical_vacancies_v1("
            "vacancy_id,employer_name,canonical_title,city,canton,first_seen_at,last_verified_at,vacancy_state"
            ") VALUES(?,?,?,?,?,?,?,?)",
            ("VAC-1","Hotel Example","Housekeeping Attendant","Zurich","ZH",
             "2026-09-21T00:00:00Z","2026-09-21T00:00:00Z","LIVE_VERIFIED")
        )
        db.execute("INSERT INTO canonical_vacancy_sources_v1 VALUES(?,?,?,?)",
                   ("VAC-1","SR-1","EXACT_PROVIDER_KEY","2026-09-21T00:00:00Z"))
        db.execute("INSERT INTO canonical_vacancy_sources_v1 VALUES(?,?,?,?)",
                   ("VAC-1","SR-2","MANUAL_REVIEW_CONFIRMED","2026-09-21T00:00:00Z"))
        self.assertEqual(db.execute("SELECT COUNT(*) FROM vacancy_source_records_v1").fetchone()[0], 2)
        self.assertEqual(db.execute(
            "SELECT COUNT(*) FROM canonical_vacancy_sources_v1 WHERE vacancy_id='VAC-1'"
        ).fetchone()[0], 2)

    def test_similarity_is_not_an_identity_basis(self):
        db = build_db()
        seed_two_source_records(db)
        db.execute(
            "INSERT INTO canonical_vacancies_v1("
            "vacancy_id,employer_name,canonical_title,first_seen_at,last_verified_at,vacancy_state"
            ") VALUES(?,?,?,?,?,?)",
            ("VAC-1","Hotel Example","Housekeeping Attendant",
             "2026-09-21T00:00:00Z","2026-09-21T00:00:00Z","CANONICAL_REVIEWED")
        )
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute("INSERT INTO canonical_vacancy_sources_v1 VALUES(?,?,?,?)",
                       ("VAC-1","SR-1","SIMILARITY","2026-09-21T00:00:00Z"))

    def test_requirement_states_and_unknown_after_search_proof(self):
        db = build_db()
        seed_two_source_records(db)
        db.execute(
            "INSERT INTO canonical_vacancies_v1("
            "vacancy_id,employer_name,canonical_title,first_seen_at,last_verified_at,vacancy_state"
            ") VALUES(?,?,?,?,?,?)",
            ("VAC-1","Hotel Example","Housekeeping Attendant",
             "2026-09-21T00:00:00Z","2026-09-21T00:00:00Z","LIVE_VERIFIED")
        )
        db.execute(
            "INSERT INTO requirement_assertions_v1 VALUES(?,?,?,?,?,?,?,?,?,?)",
            ("REQ-1","VAC-1","LANGUAGE","English","REQUIRED","very good English",
             "https://example.test/jobs/42","SR-1",None,"2026-09-21T00:00:00Z")
        )
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO requirement_assertions_v1 VALUES(?,?,?,?,?,?,?,?,?,?)",
                ("REQ-2","VAC-1","LANGUAGE","German","UNKNOWN_AFTER_SEARCH",None,
                 "https://example.test/jobs/42","SR-1",None,"2026-09-21T00:00:00Z")
            )
        db.execute(
            "INSERT INTO requirement_assertions_v1 VALUES(?,?,?,?,?,?,?,?,?,?)",
            ("REQ-3","VAC-1","LANGUAGE","German","UNKNOWN_AFTER_SEARCH",None,
             "https://example.test/jobs/42","SR-1","SEARCH-PROOF-1","2026-09-21T00:00:00Z")
        )

    def test_salary_state_does_not_conflate_estimate_with_disclosure(self):
        db = build_db()
        seed_surface(db)
        db.execute(
            "INSERT INTO canonical_vacancies_v1("
            "vacancy_id,employer_name,canonical_title,first_seen_at,last_verified_at,vacancy_state"
            ") VALUES(?,?,?,?,?,?)",
            ("VAC-1","Employer","Role","2026-09-21T00:00:00Z","2026-09-21T00:00:00Z","LIVE_VERIFIED")
        )
        db.execute(
            "INSERT INTO salary_assertions_v1 VALUES(?,?,?,?,?,?,?,?,?)",
            ("SAL-1","VAC-1","MARKET_ESTIMATE","CHF",5000,6000,"MONTH",
             "market://estimate-v1","2026-09-21T00:00:00Z")
        )
        self.assertEqual(db.execute(
            "SELECT salary_state FROM salary_assertions_v1 WHERE salary_assertion_id='SAL-1'"
        ).fetchone()[0], "MARKET_ESTIMATE")
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO salary_assertions_v1 VALUES(?,?,?,?,?,?,?,?,?)",
                ("SAL-2","VAC-1","DISCLOSED_ESTIMATE","CHF",5000,6000,"MONTH",
                 "market://estimate-v1","2026-09-21T00:00:00Z")
            )

    def test_opportunity_is_candidate_relative_and_hard_locked_no_send(self):
        db = build_db()
        seed_surface(db)
        db.execute(
            "INSERT INTO canonical_vacancies_v1("
            "vacancy_id,employer_name,canonical_title,first_seen_at,last_verified_at,vacancy_state"
            ") VALUES(?,?,?,?,?,?)",
            ("VAC-1","Employer","Role","2026-09-21T00:00:00Z","2026-09-21T00:00:00Z","LIVE_VERIFIED")
        )
        db.execute(
            "INSERT INTO opportunities_v3 VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            ("OPP-1","VAC-1","candidate://canon","ENTRY","READY_NO_SEND","[]","[]","{}",
             "HIGH","2026-09-21T00:00:00Z","CLOSED",0)
        )
        self.assertEqual(db.execute(
            "SELECT vacancy_id,candidate_ref,send_allowed FROM opportunities_v3 WHERE opportunity_id='OPP-1'"
        ).fetchone(), ("VAC-1","candidate://canon",0))
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO opportunities_v3 VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                ("OPP-2","VAC-1","candidate://other","ENTRY","READY_NO_SEND","[]","[]","{}",
                 "HIGH","2026-09-21T00:00:00Z","CLOSED",1)
            )


if __name__ == "__main__":
    unittest.main()

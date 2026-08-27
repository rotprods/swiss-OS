from __future__ import annotations

import csv
import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    module_name = "swiss_os_test_" + name.replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


crawl = load_script("crawl_hotelleriesuisse.py")
queue = load_script("build_full_market_queue.py")


class CrawlParserTests(unittest.TestCase):
    def test_live_count_and_page_parser(self):
        html = '''
        <html><body>
          <div>4473 von 4473 Hotels</div>
          <a href="/de/branche/branchenverzeichnis/hotel-page-2">2</a>
          <a href="/de/branche/branchenverzeichnis/hotel-page-373">373</a>
        </body></html>
        '''
        self.assertEqual(crawl.observed_counts(html), (4473, 373))

    def test_card_extracts_city_name_and_official_classification(self):
        html = '''
        <a class="Card small" href="/de/branche/branchenverzeichnis/hotel-25hours-hotel-langstrasse">
          <span class="Card--content"><span class="Card--content-inner">
            <em class="Card--subtitle">Zürich</em>
            <strong class="Card--title">25hours Hotel Langstrasse
              <span class="StarsRating small stars-4" title="4-Sterne Hotel"></span>
            </strong>
          </span></span>
        </a>
        '''
        rows = crawl.extract_page(html, 1, "2026-08-27T00:00:00+00:00")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.canonical_name_candidate, "25hours Hotel Langstrasse")
        self.assertEqual(row.city_candidate, "Zürich")
        self.assertEqual(row.listing_classification, "4-Sterne Hotel")
        self.assertEqual(row.accommodation_type_hint, "HOTEL")
        self.assertEqual(row.classification_basis, "CARD_STARS_RATING")

    def test_serviced_apartment_type_from_rating(self):
        html = '''
        <a class="Card small" href="/de/branche/branchenverzeichnis/hotel-riverside">
          <em class="Card--subtitle">Basel</em>
          <strong class="Card--title">63 Riverside Apartments Basel
            <span class="StarsRating small stars-4 apartment" title="4-Sterne Serviced Apartments"></span>
          </strong>
        </a>
        '''
        row = crawl.extract_page(html, 1, "now")[0]
        self.assertEqual(row.accommodation_type_hint, "SERVICED_APARTMENTS")


class QueueRoutingTests(unittest.TestCase):
    def test_new_entity_blocks_downstream_until_canonical_gate(self):
        row = {"entity_resolution_state": "NEW_ENTITY_CANDIDATE"}
        self.assertEqual(queue.routing_state(row, "entity_resolution_engine"), "READY_EXACT_DETAIL_VALIDATION")
        self.assertEqual(queue.routing_state(row, "vacancy_engine"), "WAITING_CANONICAL_PROMOTION_GATE")
        self.assertEqual(queue.routing_state(row, "governance_engine"), "OUTBOUND_CLOSED")

    def test_existing_canonical_routes_without_reallocating_identity(self):
        row = {"entity_resolution_state": "MATCHED_EXISTING_CANONICAL"}
        self.assertEqual(queue.routing_state(row, "entity_resolution_engine"), "COMPLETE_MATCHED_CANONICAL")
        self.assertEqual(queue.routing_state(row, "intelligence_engine"), "READY_CANONICAL_ROUTE")

    def test_identity_review_blocks_downstream(self):
        row = {"entity_resolution_state": "ALIAS_OR_DUPLICATE_REVIEW"}
        self.assertEqual(queue.routing_state(row, "entity_resolution_engine"), "BLOCKED_IDENTITY_REVIEW")
        self.assertEqual(queue.routing_state(row, "people_engine"), "BLOCKED_IDENTITY_REVIEW")


class FullMarketPostprocessGauntletTests(unittest.TestCase):
    def test_reconcile_order_queue_and_sqlite_end_to_end(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            canonical_db = td / "canonical.sqlite"
            con = sqlite3.connect(canonical_db)
            con.execute('''CREATE TABLE hotels(
                hotel_id TEXT PRIMARY KEY,
                canonical_name TEXT,
                city TEXT,
                hotelleriesuisse_url TEXT,
                canonical_domain TEXT,
                official_website TEXT,
                state TEXT
            )''')
            con.execute('''CREATE TABLE hotel_aliases(
                alias_hotel_id TEXT PRIMARY KEY,
                canonical_hotel_id TEXT NOT NULL
            )''')
            con.executemany(
                "INSERT INTO hotels VALUES (?,?,?,?,?,?,?)",
                [
                    ("H-0001", "Existing Hotel", "Zürich", "https://www.hotelleriesuisse.ch/de/branche/branchenverzeichnis/hotel-existing-hotel", "existing.example", "https://existing.example", "CANONICAL_CURRENT_RECONCILED"),
                    ("H-0002", "Same Name Hotel", "Lausanne", "https://www.hotelleriesuisse.ch/de/branche/branchenverzeichnis/hotel-same-name-hotel-lausanne", "same-lausanne.example", "https://same-lausanne.example", "CANONICAL_CURRENT_RECONCILED"),
                    ("H-0003", "Old Alias", "Bern", "https://www.hotelleriesuisse.ch/de/branche/branchenverzeichnis/hotel-old-alias", "alias.example", "https://alias.example", "SUPERSEDED_DUPLICATE→H-0001"),
                ],
            )
            con.execute("INSERT INTO hotel_aliases VALUES ('H-0003','H-0001')")
            con.commit(); con.close()

            discovery = td / "discovery.csv"
            fields = [
                "discovery_id", "canonical_name_candidate", "city_candidate", "detail_url",
                "directory_page", "source_tier", "membership_state", "entity_resolution_state",
                "country_scope", "accommodation_type_hint", "listing_classification",
                "classification_basis", "observed_at",
            ]
            rows = [
                ["U-0000000000000001", "Existing Hotel", "Zürich", "https://www.hotelleriesuisse.ch/de/branche/branchenverzeichnis/hotel-existing-hotel", 1, "T1_OFFICIAL_DIRECTORY_LISTING", "UNKNOWN_PENDING_DETAIL", "PENDING_CANONICAL_ANTIJOIN", "SWITZERLAND_OR_UNKNOWN", "HOTEL", "4-Sterne Hotel", "CARD_STARS_RATING", "now"],
                ["U-0000000000000002", "Brand New Hotel", "Basel", "https://www.hotelleriesuisse.ch/de/branche/branchenverzeichnis/hotel-brand-new-hotel", 1, "T1_OFFICIAL_DIRECTORY_LISTING", "UNKNOWN_PENDING_DETAIL", "PENDING_CANONICAL_ANTIJOIN", "SWITZERLAND_OR_UNKNOWN", "HOTEL", "3-Sterne Hotel", "CARD_STARS_RATING", "now"],
                ["U-0000000000000003", "Same Name Hotel", "Genève", "https://www.hotelleriesuisse.ch/de/branche/branchenverzeichnis/hotel-same-name-hotel-geneve", 1, "T1_OFFICIAL_DIRECTORY_LISTING", "UNKNOWN_PENDING_DETAIL", "PENDING_CANONICAL_ANTIJOIN", "SWITZERLAND_OR_UNKNOWN", "HOTEL", "4-Sterne Hotel", "CARD_STARS_RATING", "now"],
            ]
            with discovery.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(fields); w.writerows(rows)

            reconcile_dir = td / "reconcile"
            subprocess.run([sys.executable, str(ROOT / "scripts/reconcile_discovery.py"), "--discovery", str(discovery), "--db", str(canonical_db), "--out", str(reconcile_dir)], check=True, capture_output=True, text=True)
            rec_manifest = json.loads((reconcile_dir / "reconciliation_manifest.json").read_text())
            self.assertEqual(rec_manifest["active_canonical_rows"], 2)
            self.assertEqual(rec_manifest["alias_rows"], 1)
            self.assertEqual(rec_manifest["resolution_counts"]["MATCHED_EXISTING_CANONICAL"], 1)
            self.assertEqual(rec_manifest["resolution_counts"]["NEW_ENTITY_CANDIDATE"], 1)
            self.assertEqual(rec_manifest["resolution_counts"]["ALIAS_OR_DUPLICATE_REVIEW"], 1)

            ordered = td / "ordered.csv"
            subprocess.run([sys.executable, str(ROOT / "scripts/order_full_market.py"), "--input", str(reconcile_dir / "discovery_reconciled.csv"), "--out", str(ordered)], check=True, capture_output=True, text=True)

            queue_dir = td / "queue"
            subprocess.run([sys.executable, str(ROOT / "scripts/build_full_market_queue.py"), "--discovery", str(ordered), "--out", str(queue_dir)], check=True, capture_output=True, text=True)
            queue_manifest = json.loads((queue_dir / "engine_queue_manifest.json").read_text())
            self.assertEqual(queue_manifest["discovery_entities"], 3)
            self.assertEqual(queue_manifest["engines_per_entity"], 22)
            self.assertEqual(queue_manifest["engine_tasks"], 66)

            market_db = td / "full_market.sqlite"
            subprocess.run([
                sys.executable, str(ROOT / "scripts/build_full_market_db.py"),
                "--discovery", str(ordered),
                "--queue", str(queue_dir / "engine_queue.csv"),
                "--nodes", str(queue_dir / "discovery_graph_nodes.csv"),
                "--edges", str(queue_dir / "discovery_graph_edges.csv"),
                "--out", str(market_db),
            ], check=True, capture_output=True, text=True)
            db_manifest = json.loads(market_db.with_suffix(".manifest.json").read_text())
            self.assertEqual(db_manifest["integrity_check"], "ok")
            self.assertEqual(db_manifest["foreign_key_violations"], 0)
            self.assertEqual(db_manifest["discovery_entities"], 3)
            self.assertEqual(db_manifest["engine_tasks"], 66)
            self.assertEqual(db_manifest["outbound_allowed_true"], 0)
            self.assertEqual(db_manifest["errors"], [])

            con = sqlite3.connect(market_db)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM engine_tasks").fetchone()[0], 66)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM engine_tasks WHERE outbound_allowed=1").fetchone()[0], 0)
            self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(len(con.execute("PRAGMA foreign_key_check").fetchall()), 0)
            con.close()


if __name__ == "__main__":
    unittest.main()

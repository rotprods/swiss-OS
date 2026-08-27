from __future__ import annotations

import importlib.util
import sys
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


if __name__ == "__main__":
    unittest.main()

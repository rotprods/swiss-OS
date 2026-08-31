import unittest

from swiss_os.market_enrichment import FetchResult
from swiss_os.vacancy_detail import (
    aggregate_shards,
    compile_shard,
    opening_route_workset,
    resolve_route,
)


class FakeClient:
    def __init__(self, pages):
        self.pages = pages

    def fetch(self, url, respect_robots=True):
        body = self.pages.get(url)
        if body is None:
            return FetchResult(url, None, "FETCH_FAILED", None, None, None, "MissingFixture")
        return FetchResult(url, url, "FETCHED", 200, "abc123", body, None)


def market_record(record_id, routes):
    return {
        "record_id": record_id,
        "name": record_id,
        "city": "Davos",
        "e07_vacancy": {"opening_routes": routes},
        "safety": {
            "authority_advanced": False,
            "canonical_id_allocations": 0,
            "canonical_id_reservations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "irreversible_external_actions": 0,
        },
    }


def aggregate(records):
    return {
        "source_records": 2061,
        "source_snapshot_id": "S",
        "records": records,
        "safety": {
            "authority_advanced": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "irreversible_external_actions": 0,
        },
    }


class VacancyDetailTests(unittest.TestCase):
    def test_workset_only_contains_opening_route_hotels(self):
        data = aggregate([
            market_record("a", ["https://example.com/jobs/housekeeping"]),
            market_record("b", []),
            market_record("c", ["https://example.com/jobs/kitchen"]),
        ])
        self.assertEqual([item["record_id"] for item in opening_route_workset(data)], ["a", "c"])

    def test_structured_jobposting_is_current_role_signal(self):
        url = "https://example.com/jobs/housekeeping"
        body = '''<html><head><script type="application/ld+json">{"@type":"JobPosting","title":"Housekeeping Attendant","datePosted":"2026-08-30"}</script></head><body><h1>Housekeeping Attendant</h1></body></html>'''
        result = resolve_route(FakeClient({url: body}), url, "2026-08-31T17:15:00Z")
        self.assertEqual(result["resolution_state"], "CURRENT_ROLE_SIGNALS_FOUND")
        self.assertTrue(any(signal["title"] == "Housekeeping Attendant" for signal in result["role_signals"]))
        self.assertTrue(any(signal["evidence_type"] == "CURRENT_STRUCTURED_JOBPOSTING" for signal in result["role_signals"]))
        self.assertEqual(result["send_allowed"], 0)

    def test_heading_and_child_role_links_are_evidence_not_authority(self):
        url = "https://example.com/careers"
        body = '''<html><head><title>Careers</title></head><body><h1>Join our team</h1><a href="/jobs/chef-de-rang">Chef de Rang 100%</a><a href="/jobs">All jobs</a></body></html>'''
        result = resolve_route(FakeClient({url: body}), url, "2026-08-31T17:15:00Z")
        titles = [signal["title"] for signal in result["role_signals"]]
        self.assertIn("Chef de Rang 100%", titles)
        self.assertNotIn("All jobs", titles)
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertEqual(result["outbound"], "CLOSED")

    def test_requirement_snippets_are_captured_without_inventing_levels(self):
        url = "https://example.com/jobs/service"
        body = '''<html><body><h1>Service Mitarbeiter</h1><p>Sehr gute Deutsch- und Englischkenntnisse.</p><p>Berufserfahrung im Service ist von Vorteil.</p><p>Eintritt per sofort.</p><p>Mitarbeiterunterkunft vorhanden.</p></body></html>'''
        result = resolve_route(FakeClient({url: body}), url, "2026-08-31T17:15:00Z")
        self.assertTrue(result["language_signal_snippets"])
        self.assertTrue(result["experience_signal_snippets"])
        self.assertTrue(result["start_signal_snippets"])
        self.assertTrue(result["housing_signal"])

    def test_explicit_no_openings_stays_nonterminal(self):
        url = "https://example.com/jobs"
        body = "<html><body><h1>Jobs</h1><p>Currently no open positions.</p></body></html>"
        result = resolve_route(FakeClient({url: body}), url, "2026-08-31T17:15:00Z")
        self.assertEqual(result["resolution_state"], "CURRENT_NO_OPENINGS_EXPLICIT")
        self.assertTrue(result["no_openings_explicit"])
        self.assertFalse(result["role_signals"])
        self.assertEqual(result["send_allowed"], 0)

    def test_shard_and_aggregate_preserve_exact_workset_coverage(self):
        routes_a = ["https://example.com/jobs/housekeeping"]
        routes_b = ["https://example.org/jobs/kitchen"]
        data = aggregate([market_record("a", routes_a), market_record("b", routes_b)])
        pages = {
            routes_a[0]: "<html><body><h1>Housekeeping Attendant</h1></body></html>",
            routes_b[0]: "<html><body><h1>Kitchen Helper</h1></body></html>",
        }
        s0 = compile_shard(data, shard_index=0, shard_count=2, observed_at="2026-08-31T17:15:00Z", client=FakeClient(pages))
        s1 = compile_shard(data, shard_index=1, shard_count=2, observed_at="2026-08-31T17:15:00Z", client=FakeClient(pages))
        result = aggregate_shards(data, [s0, s1])
        self.assertEqual(result["workset_total"], 2)
        self.assertEqual([record["record_id"] for record in result["records"]], ["a", "b"])
        self.assertEqual(result["role_signal_hotels"], 2)
        self.assertFalse(result["authority_advanced"])
        self.assertEqual(result["send_allowed"], 0)

    def test_fail_closed_on_market_safety_drift(self):
        data = aggregate([market_record("a", ["https://example.com/jobs"])])
        data["safety"]["send_allowed"] = 1
        with self.assertRaises(ValueError):
            opening_route_workset(data)


if __name__ == "__main__":
    unittest.main()

import json
import socket
import unittest
from unittest import mock

from swiss_os import market_enrichment as me


class MarketEnrichmentTests(unittest.TestCase):
    def test_shard_exact_cover_and_stable_order(self):
        records = [{"record_id": f"MD-{i:04d}"} for i in range(2061)]
        parts = [me.shard(records, i, 42) for i in range(42)]
        flattened = [record for part in parts for record in part]
        self.assertEqual(flattened, records)
        self.assertEqual(len(flattened), 2061)
        self.assertEqual(len({r["record_id"] for r in flattened}), 2061)
        self.assertLessEqual(max(map(len, parts)) - min(map(len, parts)), 1)

    def test_official_site_requires_explicit_website_signal(self):
        hs = '<a href="https://facebook.com/x">Social</a><a href="https://vendor.example/">Booking technology</a><a href="https://hotel.example/">Website</a>'
        self.assertEqual(me.external_official_candidates("https://www.hotelleriesuisse.ch/hotel-x", hs), ["https://hotel.example/"])

    def test_route_discovery_is_same_site_and_typed(self):
        home = '<a href="/about/team">Team</a><a href="/karriere">Karriere</a><a href="/staff-accommodation">Staff accommodation</a><a href="https://jobs.vendor.example/posting">External jobs</a>'
        self.assertEqual(me.route_candidates("https://hotel.example/", home, me.CAREER_RE), ["https://hotel.example/karriere"])
        self.assertEqual(me.route_candidates("https://hotel.example/", home, me.HOUSING_RE), ["https://hotel.example/staff-accommodation"])
        self.assertEqual(me.route_candidates("https://hotel.example/", home, me.TEAM_RE), ["https://hotel.example/about/team"])

    def test_structured_jobposting_is_strong_t1_signal(self):
        html = '<script type="application/ld+json">{"@type":"JobPosting","title":"Chef de Rang","datePosted":"2026-08-30","validThrough":"2026-09-30"}</script>'
        jobs = me.extract_jobpostings(html, "https://hotel.example/jobs/chef")
        self.assertEqual(jobs[0]["title"], "Chef de Rang")

    def test_negative_vacancy_claim_requires_explicit_language(self):
        self.assertTrue(me.explicit_no_openings("Currently no open positions."))
        self.assertTrue(me.explicit_no_openings("Derzeit keine Stellen."))
        self.assertFalse(me.explicit_no_openings("We are always interested in hospitality professionals."))

    @mock.patch("swiss_os.market_enrichment.socket.getaddrinfo")
    def test_public_url_guard(self, getaddrinfo):
        getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
        self.assertEqual(me.validate_public_https_url("https://example.com/x").hostname, "example.com")
        for url in ("http://example.com", "https://127.0.0.1", "https://user:pass@example.com"):
            with self.assertRaises(ValueError):
                me.validate_public_https_url(url)

    def test_aggregate_requires_exact_secure_shard_coverage(self):
        manifest={"snapshot_id":"HS-MEMBER-DE-33206402141","records_sha256":"abc","authority_advanced":False,"send_allowed":0,"records":[{"record_id":"a"},{"record_id":"b"}]}
        def rec(rid):
            r={"record_id":rid,"e07_vacancy":{"state":"CAREERS_ROUTE_NOT_DISCOVERED","structured_openings_count":0,"opening_routes":[],"careers_routes":[]},"official_site":{"url":None},"e08_housing":{"state":"STAFF_HOUSING_RESEARCH_PENDING"},"e09_people":{"state":"PEOPLE_RESEARCH_PENDING"},"e10_channel":{"state":"CHANNEL_RESEARCH_PENDING","spontaneous_application_policy":"NOT_OBSERVED"},"e17_application":{"candidate_truth_block_required":True},"e22_security":{"outbound":"CLOSED","send_allowed":0,"irreversible_external_actions":0},"safety":{"authority_advanced":False,"canonical_id_allocations":0,"canonical_id_reservations":0,"outbound":"CLOSED","send_allowed":0,"irreversible_external_actions":0}}
            r["record_sha256"]=me.sha256_value(r)
            return r
        safety={"authority_advanced":False,"outbound":"CLOSED","send_allowed":0,"irreversible_external_actions":0}
        r0,r1=rec("a"),rec("b")
        packets=[{"schema_version":me.SCHEMA_VERSION,"source_snapshot_id":"HS-MEMBER-DE-33206402141","source_records_sha256":"abc","observed_at":"2026-08-30T21:05:00Z","shard_index":0,"shard_count":2,"records":[r0],"records_sha256":me.sha256_value([r0]),"safety":safety},{"schema_version":me.SCHEMA_VERSION,"source_snapshot_id":"HS-MEMBER-DE-33206402141","source_records_sha256":"abc","observed_at":"2026-08-30T21:05:00Z","shard_index":1,"shard_count":2,"records":[r1],"records_sha256":me.sha256_value([r1]),"safety":safety}]
        aggregate,summary=me.aggregate(manifest,packets,"2026-08-30T21:05:00Z")
        self.assertEqual(aggregate["source_records"],2)
        self.assertEqual(summary["personalized_application_seeds"],2)
        self.assertEqual(summary["send_allowed"],0)
        with self.assertRaises(ValueError):
            me.aggregate(manifest,packets[:1],"2026-08-30T21:05:00Z")
        corrupted=json.loads(json.dumps(packets))
        corrupted[0]["records_sha256"]="0"*64
        with self.assertRaises(ValueError):
            me.aggregate(manifest,corrupted,"2026-08-30T21:05:00Z")

    def test_source_contains_engine_and_security_locks(self):
        with open("src/swiss_os/market_enrichment.py", encoding="utf-8") as handle:
            text=handle.read().replace(" ","")
        for marker in ('"e07_vacancy"','"e08_housing"','"e09_people"','"e10_channel"','"e11_intelligence"','"e12_graph"','"e14_scheduler"','"e15_score"','"e16_candidate_truth"','"e17_application"','"e18_qa"','"e19_observability"','"e20_recovery"','"e21_delivery"','"e22_security"','"candidate_truth_block_required":True','"final_send_ready":False','"outbound":"CLOSED"','"send_allowed":0','"canonical_id_reservations":0'):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()

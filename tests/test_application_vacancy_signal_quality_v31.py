import unittest

from swiss_os.application_wave_v31 import compile_top_resolved_vacancy_seeds_v31
from swiss_os.vacancy_signal_quality import evaluate_signal, semantic_quality, temporal_quality


class VacancySignalQualityV31Tests(unittest.TestCase):
    def market_record(self, record_id, name):
        return {
            "record_id": record_id,
            "name": name,
            "city": "Davos",
            "observed_at": "2026-08-31T20:31:55Z",
            "e07_vacancy": {"careers_routes": ["https://example.com/jobs"], "opening_routes": ["https://example.com/jobs"]},
            "e08_housing": {"state": "UNKNOWN"},
            "e15_score": {"market_readiness_score": 50},
            "safety": {
                "authority_advanced": False,
                "canonical_id_allocations": 0,
                "canonical_id_reservations": 0,
                "outbound": "CLOSED",
                "send_allowed": 0,
                "irreversible_external_actions": 0,
            },
        }

    def market(self, *records):
        return {
            "source_snapshot_id": "S",
            "observed_at": "2026-08-31T20:31:55Z",
            "records": list(records),
            "safety": {"authority_advanced": False, "outbound": "CLOSED", "send_allowed": 0},
        }

    def detail_record(self, record_id, routes):
        return {"record_id": record_id, "routes": routes, "outbound": "CLOSED", "send_allowed": 0}

    def detail(self, *records):
        return {
            "payload_sha256": "abc",
            "records": list(records),
            "authority_advanced": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
        }

    def route(self, signals, requested="https://example.com/jobs", observed="2026-08-31T20:31:55Z"):
        return {
            "requested_url": requested,
            "final_url": requested,
            "observed_at": observed,
            "no_openings_explicit": False,
            "housing_signal": False,
            "role_signals": signals,
            "language_signal_snippets": [],
            "experience_signal_snippets": [],
            "start_signal_snippets": [],
            "contact_emails": [],
        }

    def test_navigation_link_is_not_a_role(self):
        signal = {
            "title": "Signature Restaurant",
            "source_url": "https://hotel.example/en/enjoy/signature-restaurant",
            "evidence_type": "CURRENT_PAGE_ROLE_LINK",
        }
        quality = semantic_quality(signal, self.route([signal], requested="https://hotel.example/en/career"))
        self.assertFalse(quality["valid"])
        self.assertIn("NAVIGATION_OR_VENUE_LABEL_NOT_ROLE", quality["reasons"])
        self.assertIn("ROLE_LINK_URL_NOT_JOBLIKE", quality["reasons"])

    def test_generic_opening_bucket_is_not_exact_role(self):
        signal = {
            "title": "Opening Crew Positionen",
            "source_url": "https://hotel.example/career",
            "evidence_type": "CURRENT_STRUCTURED_JOBPOSTING",
        }
        quality = semantic_quality(signal, self.route([signal], requested="https://hotel.example/career"))
        self.assertFalse(quality["valid"])
        self.assertIn("GENERIC_VACANCY_BUCKET_NOT_EXACT_ROLE", quality["reasons"])

    def test_future_posted_and_expired_valid_through_is_temporal_conflict(self):
        signal = {
            "title": "Mitarbeiter/in Hauswirtschaft",
            "date_posted": "2027-01-01",
            "valid_through": "2026-04-01",
            "source_url": "https://example.com/jobs/hauswirtschaft",
            "evidence_type": "CURRENT_STRUCTURED_JOBPOSTING",
        }
        quality = temporal_quality(signal, "2026-08-31T20:31:55Z")
        self.assertFalse(quality["current"])
        self.assertIn("DATE_POSTED_AFTER_VALID_THROUGH", quality["reasons"])
        self.assertIn("DATE_POSTED_IN_FUTURE_AT_OBSERVATION", quality["reasons"])
        self.assertIn("VALID_THROUGH_EXPIRED_AT_OBSERVATION", quality["reasons"])

    def test_route_temporal_conflict_blocks_sibling_page_title_until_recheck(self):
        structured = {
            "title": "Servicemitarbeiter/in",
            "date_posted": "2027-01-01",
            "valid_through": "2026-04-01",
            "source_url": "https://example.com/jobs/servicemitarbeiter",
            "evidence_type": "CURRENT_STRUCTURED_JOBPOSTING",
            "requires_requirement_detail": False,
        }
        page_title = {
            "title": "Servicemitarbeiter/in – Hotel",
            "source_url": "https://example.com/jobs/servicemitarbeiter",
            "evidence_type": "CURRENT_PAGE_TITLE",
            "requires_requirement_detail": True,
        }
        market = self.market(self.market_record("a", "Hotel A"))
        detail = self.detail(self.detail_record("a", [self.route([structured, page_title], requested="https://example.com/jobs/servicemitarbeiter")]))
        result = compile_top_resolved_vacancy_seeds_v31(market, detail)
        self.assertEqual(result["selected_count"], 0)
        self.assertGreaterEqual(result["rejected_signal_reason_counts"].get("ROUTE_STRUCTURED_TEMPORAL_CONFLICT_REQUIRES_RECHECK", 0), 1)

    def test_same_vacancy_repeated_across_properties_goes_to_owner_review(self):
        signal = {
            "title": "Housekeeping/ Allrounder:in Rinerhorn",
            "source_url": "https://group.example/jobs/housekeeping-rinerhorn_j_1",
            "evidence_type": "CURRENT_PAGE_ROLE_LINK",
            "requires_requirement_detail": True,
        }
        market = self.market(self.market_record("a", "Hotel A"), self.market_record("b", "Hotel B"))
        route = self.route([signal], requested="https://group.example/jobs")
        detail = self.detail(self.detail_record("a", [route]), self.detail_record("b", [route]))
        result = compile_top_resolved_vacancy_seeds_v31(market, detail)
        self.assertEqual(result["selected_count"], 0)
        self.assertEqual(result["ownership_review_count"], 1)
        self.assertEqual(result["ownership_review_queue"][0]["record_ids"], ["a", "b"])

    def test_same_property_duplicate_evidence_keeps_one_strongest_signal(self):
        structured = {
            "title": "Housekeeping Attendant",
            "date_posted": "2026-08-01",
            "valid_through": "2026-10-01T23:59:59+02:00",
            "source_url": "https://hotel.example/jobs/housekeeping",
            "evidence_type": "CURRENT_STRUCTURED_JOBPOSTING",
            "requires_requirement_detail": False,
        }
        heading = {
            "title": "Housekeeping Attendant",
            "source_url": "https://hotel.example/jobs/housekeeping",
            "evidence_type": "CURRENT_PAGE_HEADING",
            "requires_requirement_detail": True,
        }
        market = self.market(self.market_record("a", "Hotel A"))
        detail = self.detail(self.detail_record("a", [self.route([structured, heading], requested="https://hotel.example/jobs/housekeeping")]))
        result = compile_top_resolved_vacancy_seeds_v31(market, detail)
        self.assertEqual(result["selected_count"], 1)
        self.assertEqual(result["selected"][0]["vacancy_evidence_type"], "CURRENT_STRUCTURED_JOBPOSTING")

    def test_valid_unique_vacancy_is_research_shortlist_only_and_stays_no_send(self):
        signal = {
            "title": "Housekeeping Attendant",
            "date_posted": "2026-08-01",
            "valid_through": "2026-10-01",
            "source_url": "https://hotel.example/jobs/housekeeping",
            "evidence_type": "CURRENT_STRUCTURED_JOBPOSTING",
            "requires_requirement_detail": False,
        }
        market = self.market(self.market_record("a", "Hotel A"))
        detail = self.detail(self.detail_record("a", [self.route([signal], requested="https://hotel.example/jobs/housekeeping")]))
        result = compile_top_resolved_vacancy_seeds_v31(market, detail)
        self.assertEqual(result["selected_count"], 1)
        seed = result["selected"][0]
        self.assertEqual(seed["owner_scope_state"], "UNIQUE_SOURCE_RECORD_CANDIDATE_REQUIRES_PRIVATE_RECHECK")
        self.assertTrue(seed["owner_scope_verification_required_before_aag_ready"])
        self.assertFalse(seed["application_ready_no_send"])
        self.assertFalse(seed["final_send_ready"])
        self.assertEqual(seed["send_allowed"], 0)
        self.assertEqual(result["application_adversarial_gate_required"], "APPLICATION-ADVERSARIAL-GATE-3.0")


if __name__ == "__main__":
    unittest.main()

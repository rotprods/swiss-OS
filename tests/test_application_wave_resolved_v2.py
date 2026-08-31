import unittest

from swiss_os.application_wave import compile_top_resolved_vacancy_seeds, role_accessibility_score


def market_record(record_id, name, jobs=None, opening_routes=None, score=50):
    return {
        "record_id": record_id,
        "name": name,
        "city": "Davos",
        "observed_at": "2026-08-30T21:05:00Z",
        "e07_vacancy": {
            "state": "CURRENT_OPENING_ROUTES_FOUND_T1",
            "structured_openings": jobs or [],
            "opening_routes": opening_routes or [],
            "careers_routes": [f"https://{record_id}.example/careers"],
            "explicit_no_openings_proof": False,
        },
        "e08_housing": {"state": "STAFF_HOUSING_RESEARCH_PENDING"},
        "e15_score": {"market_readiness_score": score},
        "safety": {
            "authority_advanced": False,
            "canonical_id_allocations": 0,
            "canonical_id_reservations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "irreversible_external_actions": 0,
        },
    }


def market_aggregate(records):
    return {
        "source_snapshot_id": "S",
        "observed_at": "2026-08-30T21:05:00Z",
        "records": records,
        "safety": {"authority_advanced": False, "outbound": "CLOSED", "send_allowed": 0},
    }


class ResolvedApplicationWaveTests(unittest.TestCase):
    def test_generic_entry_accessibility_is_only_a_ranking_hint(self):
        self.assertGreater(role_accessibility_score("Housekeeping Mitarbeiter 100%"), 0)
        self.assertLess(role_accessibility_score("General Manager"), 0)

    def test_resolved_current_role_signal_becomes_no_send_seed(self):
        market = market_aggregate([
            market_record("a", "Hotel A", opening_routes=["https://a.example/jobs"]),
        ])
        detail = {
            "payload_sha256": "D",
            "authority_advanced": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "records": [{
                "record_id": "a",
                "outbound": "CLOSED",
                "send_allowed": 0,
                "routes": [{
                    "observed_at": "2026-08-31T17:15:00Z",
                    "no_openings_explicit": False,
                    "housing_signal": True,
                    "language_signal_snippets": ["Deutsch oder Englisch"],
                    "experience_signal_snippets": ["Erfahrung von Vorteil"],
                    "start_signal_snippets": ["Eintritt per sofort"],
                    "contact_emails": ["jobs@a.example"],
                    "role_signals": [{
                        "title": "Housekeeping Mitarbeiter 100%",
                        "source_url": "https://a.example/jobs/housekeeping",
                        "evidence_type": "CURRENT_PAGE_ROLE_LINK",
                        "requires_requirement_detail": True,
                    }],
                }],
            }],
        }
        result = compile_top_resolved_vacancy_seeds(market, detail, limit=25)
        self.assertEqual(result["selected_count"], 1)
        item = result["selected"][0]
        self.assertEqual(item["target_role"], "Housekeeping Mitarbeiter 100%")
        self.assertEqual(item["strategy"]["application_mode"], "PRIMARY_EXACT_VACANCY")
        self.assertTrue(item["requires_private_fit_validation"])
        self.assertFalse(item["application_ready_no_send"])
        self.assertFalse(item["final_send_ready"])
        self.assertEqual(item["send_allowed"], 0)
        self.assertEqual(item["requirement_evidence"]["contact_emails"], ["jobs@a.example"])

    def test_explicit_no_openings_route_does_not_become_candidate(self):
        market = market_aggregate([market_record("a", "Hotel A", opening_routes=["https://a.example/jobs"])])
        detail = {
            "payload_sha256": "D",
            "authority_advanced": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "records": [{
                "record_id": "a", "outbound": "CLOSED", "send_allowed": 0,
                "routes": [{"no_openings_explicit": True, "role_signals": [{"title": "Old Role", "source_url": "https://a.example/old", "evidence_type": "CURRENT_PAGE_TITLE"}]}],
            }],
        }
        result = compile_top_resolved_vacancy_seeds(market, detail)
        self.assertEqual(result["selected_count"], 0)

    def test_evidence_quality_breaks_priority_before_accessibility(self):
        market = market_aggregate([
            market_record("a", "Hotel A", opening_routes=["https://a.example/jobs"]),
            market_record("b", "Hotel B", opening_routes=["https://b.example/jobs"]),
        ])
        detail = {
            "payload_sha256": "D", "authority_advanced": False, "outbound": "CLOSED", "send_allowed": 0,
            "records": [
                {"record_id": "a", "outbound": "CLOSED", "send_allowed": 0, "routes": [{"no_openings_explicit": False, "housing_signal": False, "role_signals": [{"title": "General Manager", "source_url": "https://a.example/jobs/gm", "evidence_type": "CURRENT_STRUCTURED_JOBPOSTING"}]}]},
                {"record_id": "b", "outbound": "CLOSED", "send_allowed": 0, "routes": [{"no_openings_explicit": False, "housing_signal": False, "role_signals": [{"title": "Housekeeping Mitarbeiter", "source_url": "https://b.example/jobs/hk", "evidence_type": "CURRENT_PAGE_ROLE_LINK"}]}]},
            ],
        }
        result = compile_top_resolved_vacancy_seeds(market, detail, limit=2)
        self.assertEqual(result["selected_count"], 2)
        self.assertEqual({item["target_role"] for item in result["selected"]}, {"General Manager", "Housekeeping Mitarbeiter"})
        self.assertTrue(all(item["requires_private_fit_validation"] for item in result["selected"]))

    def test_fail_closed_on_detail_send_gate_drift(self):
        market = market_aggregate([market_record("a", "Hotel A")])
        detail = {"authority_advanced": False, "outbound": "CLOSED", "send_allowed": 1, "records": []}
        with self.assertRaises(ValueError):
            compile_top_resolved_vacancy_seeds(market, detail)


if __name__ == "__main__":
    unittest.main()

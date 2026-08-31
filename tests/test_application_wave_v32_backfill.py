import unittest

from swiss_os.application_wave_v32 import compile_top_resolved_vacancy_seeds


class ApplicationWaveV32BackfillTests(unittest.TestCase):
    def market_record(self, rid, name):
        return {
            "record_id": rid,
            "name": name,
            "city": "Davos",
            "observed_at": "2026-08-31T20:31:55Z",
            "e07_vacancy": {
                "careers_routes": [f"https://{rid}.example/jobs"],
                "opening_routes": [f"https://{rid}.example/jobs"],
            },
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

    def route(self, rid, title, evidence_type):
        url = f"https://{rid}.example/jobs/{title.lower().replace(' ', '-')}"
        return {
            "requested_url": url,
            "final_url": url,
            "observed_at": "2026-08-31T20:31:55Z",
            "no_openings_explicit": False,
            "housing_signal": False,
            "language_signal_snippets": [],
            "experience_signal_snippets": [],
            "start_signal_snippets": [],
            "contact_emails": [],
            "role_signals": [
                {
                    "title": title,
                    "source_url": url,
                    "evidence_type": evidence_type,
                    "requires_requirement_detail": evidence_type != "CURRENT_STRUCTURED_JOBPOSTING",
                    "date_posted": "2026-08-01" if evidence_type == "CURRENT_STRUCTURED_JOBPOSTING" else None,
                    "valid_through": "2026-10-01" if evidence_type == "CURRENT_STRUCTURED_JOBPOSTING" else None,
                }
            ],
        }

    def test_noise_in_top_rank_is_removed_and_next_real_role_backfills(self):
        market = {
            "source_snapshot_id": "S",
            "observed_at": "2026-08-31T20:31:55Z",
            "records": [self.market_record("a", "Noise Hotel"), self.market_record("b", "Real Hotel")],
            "safety": {"authority_advanced": False, "outbound": "CLOSED", "send_allowed": 0},
        }
        vacancy = {
            "payload_sha256": "v",
            "authority_advanced": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "records": [
                {"record_id": "a", "outbound": "CLOSED", "send_allowed": 0, "routes": [self.route("a", "Services", "CURRENT_PAGE_HEADING")]},
                {"record_id": "b", "outbound": "CLOSED", "send_allowed": 0, "routes": [self.route("b", "Housekeeping Mitarbeiter/in 60%", "CURRENT_STRUCTURED_JOBPOSTING")]},
            ],
        }
        result = compile_top_resolved_vacancy_seeds(market, vacancy, limit=1)
        self.assertEqual(result["selected_count"], 1)
        self.assertEqual(result["selected"][0]["record_id"], "b")
        self.assertEqual(result["selected"][0]["target_role"], "Housekeeping Mitarbeiter/in 60%")
        self.assertEqual(result["shortlist_exact_role_rejected_count"], 1)
        self.assertEqual(result["shortlist_exact_role_rejections"][0]["target_role"], "Services")
        self.assertFalse(result["selected"][0]["application_ready_no_send"])
        self.assertEqual(result["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()

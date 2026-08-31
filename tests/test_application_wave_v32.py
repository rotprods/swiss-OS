import unittest

from swiss_os.application_adversarial_v31 import SCHEMA_VERSION as AAG_SCHEMA_VERSION
from swiss_os.application_wave_v32 import SCHEMA_VERSION, compile_top_resolved_vacancy_seeds


class ApplicationWaveV32Tests(unittest.TestCase):
    def test_shortlist_contract_is_aag31_bound_and_no_send(self):
        market_record = {
            "record_id": "a",
            "name": "Hotel A",
            "city": "Davos",
            "observed_at": "2026-09-01T00:00:00Z",
            "e07_vacancy": {
                "careers_routes": ["https://hotel.example/jobs"],
                "opening_routes": ["https://hotel.example/jobs/housekeeping"],
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
        market = {
            "source_snapshot_id": "S",
            "observed_at": "2026-09-01T00:00:00Z",
            "records": [market_record],
            "safety": {"authority_advanced": False, "outbound": "CLOSED", "send_allowed": 0},
        }
        vacancy = {
            "payload_sha256": "v",
            "authority_advanced": False,
            "outbound": "CLOSED",
            "send_allowed": 0,
            "records": [
                {
                    "record_id": "a",
                    "outbound": "CLOSED",
                    "send_allowed": 0,
                    "routes": [
                        {
                            "requested_url": "https://hotel.example/jobs/housekeeping",
                            "final_url": "https://hotel.example/jobs/housekeeping",
                            "observed_at": "2026-09-01T00:00:00Z",
                            "no_openings_explicit": False,
                            "housing_signal": False,
                            "language_signal_snippets": [],
                            "experience_signal_snippets": [],
                            "start_signal_snippets": [],
                            "contact_emails": [],
                            "role_signals": [
                                {
                                    "title": "Housekeeping Attendant",
                                    "source_url": "https://hotel.example/jobs/housekeeping",
                                    "evidence_type": "CURRENT_STRUCTURED_JOBPOSTING",
                                    "date_posted": "2026-08-01",
                                    "valid_through": "2026-10-01",
                                    "requires_requirement_detail": False,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        result = compile_top_resolved_vacancy_seeds(market, vacancy)
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertEqual(result["application_adversarial_gate_required"], AAG_SCHEMA_VERSION)
        self.assertEqual(result["selected_count"], 1)
        seed = result["selected"][0]
        self.assertEqual(seed["application_adversarial_gate_required"], AAG_SCHEMA_VERSION)
        self.assertEqual(seed["strategy"]["application_adversarial_gate"]["schema_version"], AAG_SCHEMA_VERSION)
        self.assertEqual(seed["private_packet_compiler_required"], "APPLICATION-PRIVATE-PACKET-3.1")
        self.assertFalse(seed["application_ready_no_send"])
        self.assertFalse(seed["final_send_ready"])
        self.assertEqual(seed["send_allowed"], 0)


if __name__ == "__main__":
    unittest.main()

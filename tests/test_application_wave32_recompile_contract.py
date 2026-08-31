import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "docs/state/market/APPLICATION_WAVE32_RECOMPILE_REQUEST_2026-09-01.json"
WORKFLOW = ROOT / ".github/workflows/application-wave32-recompile.yml"


class ApplicationWave32RecompileContractTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_request_is_exact_existing_artifacts_only(self):
        self.assertEqual(self.request["execution_mode"], "RECOMPILE_EXISTING_ARTIFACTS_ONLY_NO_PROVIDER_RESEARCH")
        self.assertEqual(self.request["source_market"]["artifact_id"], 9739544628)
        self.assertEqual(self.request["source_market"]["records_expected"], 2061)
        self.assertEqual(self.request["source_vacancy_detail"]["artifact_id"], 9774670880)
        self.assertEqual(self.request["source_vacancy_detail"]["records_expected"], 436)
        self.assertEqual(self.request["source_vacancy_detail"]["reused_shards"], 43)
        self.assertEqual(self.request["source_vacancy_detail"]["rerun_shards"], [14])
        self.assertFalse(self.request["network_policy"]["hotel_provider_requests_allowed"])
        self.assertFalse(self.request["network_policy"]["source_recrawl_allowed"])
        self.assertTrue(self.request["network_policy"]["github_artifact_download_only"])

    def test_request_requires_wave32_aag31_and_no_send(self):
        self.assertEqual(self.request["compiler"]["schema_version"], "APPLICATION-WAVE-3.2")
        self.assertEqual(self.request["compiler"]["application_adversarial_gate_required"], "APPLICATION-ADVERSARIAL-GATE-3.1")
        self.assertEqual(self.request["compiler"]["private_packet_compiler_required"], "APPLICATION-PRIVATE-PACKET-3.1")
        safety = self.request["safety"]
        self.assertFalse(safety["authority_advanced"])
        self.assertEqual(safety["canonical_id_allocations"], 0)
        self.assertEqual(safety["canonical_id_reservations"], 0)
        self.assertEqual(safety["outbound"], "CLOSED")
        self.assertEqual(safety["send_allowed"], 0)
        self.assertEqual(safety["application_ready_no_send"], 0)
        self.assertFalse(safety["final_send_ready"])

    def test_workflow_never_invokes_market_or_vacancy_crawler(self):
        forbidden = (
            "market_enrichment run-shard",
            "vacancy_detail run-shard",
            "vacancy_detail_fault_isolation run-shard",
            "curl https://",
            "requests.get(",
            "urllib.request",
        )
        lower = self.workflow.lower()
        for token in forbidden:
            with self.subTest(token=token):
                # GitHub API artifact curl is allowed and explicitly contains api.github.com.
                if token == "curl https://":
                    self.assertNotIn("curl https://", lower)
                else:
                    self.assertNotIn(token.lower(), lower)
        self.assertIn("api.github.com/repos/${github_repository}/actions/artifacts", lower)
        self.assertIn("provider_requests_performed': 0", lower)

    def test_workflow_uses_compiler_not_ad_hoc_scoring(self):
        self.assertIn("from swiss_os.application_wave_v32 import compile_top_resolved_vacancy_seeds", self.workflow)
        self.assertIn("assert result['application_ready_no_send'] == 0", self.workflow)
        self.assertIn("assert result['send_allowed'] == 0", self.workflow)


if __name__ == "__main__":
    unittest.main()

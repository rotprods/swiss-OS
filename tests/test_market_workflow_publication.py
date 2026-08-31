import json
from pathlib import Path
import unittest


class MarketWorkflowPublicationTests(unittest.TestCase):
    def test_market_workflow_does_not_attempt_forbidden_actions_pr_creation(self):
        text = Path('.github/workflows/market-enrichment-2061.yml').read_text(encoding='utf-8')
        self.assertNotIn('gh pr create', text)
        self.assertIn('Persist public-safe summary branch', text)
        self.assertIn('authorized interactive orchestrator', text)

    def test_vacancy_detail_workflow_is_no_send_and_no_actions_pr_create(self):
        text = Path('.github/workflows/vacancy-detail-436.yml').read_text(encoding='utf-8')
        self.assertNotIn('gh pr create', text)
        self.assertIn('vacancy-detail-436', text)
        self.assertIn('application-wave2-public-seeds.json', text)
        self.assertIn('authorized interactive orchestrator', text)

    def test_vacancy_detail_full_workflow_uses_route_fault_isolation_adapter(self):
        text = Path('.github/workflows/vacancy-detail-436.yml').read_text(encoding='utf-8')
        self.assertIn('python -m swiss_os.vacancy_detail_fault_isolation', text)
        self.assertNotIn('python -m swiss_os.vacancy_detail run-shard', text)
        self.assertIn('route fault isolation', text.lower())

    def test_vacancy_detail_workflow_validates_self_addressed_market_hash_without_hashing_itself(self):
        text = Path('.github/workflows/vacancy-detail-436.yml').read_text(encoding='utf-8')
        self.assertIn("declared=market.get('aggregate_sha256')", text)
        self.assertIn("if k!='aggregate_sha256'", text)
        self.assertIn("assert recomputed == declared", text)
        self.assertNotIn("assert sha256_value(market) == request['source_market_aggregate_sha256']", text)

    def test_vacancy_detail_run_request_is_exact_and_fail_closed(self):
        data = json.loads(Path('docs/state/market/VACANCY_DETAIL_RUN_REQUEST_436_2026-08-31.json').read_text(encoding='utf-8'))
        self.assertEqual(data['source_market_run_id'], '33336272106')
        self.assertEqual(data['source_market_artifact_id'], 9739544628)
        self.assertEqual(data['source_market_aggregate_sha256'], '19308eae6b56ca0b43fc76bc98aa69d57bb885b2c009134bbf58f2f58fe47e23')
        self.assertEqual(data['source_market_hash_contract'], 'SHA256_CANONICAL_JSON_EXCLUDING_AGGREGATE_SHA256_FIELD')
        self.assertGreaterEqual(data['retry_generation'], 1)
        self.assertEqual(data['expected_opening_route_hotels'], 436)
        self.assertEqual(data['shard_count'], 44)
        self.assertFalse(data['safety']['authority_advanced'])
        self.assertFalse(data['safety']['final_send_ready'])
        self.assertEqual(data['safety']['outbound'], 'CLOSED')
        self.assertEqual(data['safety']['send_allowed'], 0)

    def test_shard14_recovery_request_reuses_exact_prior_success_set(self):
        data = json.loads(Path('docs/state/market/VACANCY_DETAIL_RECOVERY_REQUEST_SHARD14_2026-08-31.json').read_text(encoding='utf-8'))
        self.assertEqual(data['failed_vacancy_detail_run_id'], '33424739389')
        self.assertEqual(data['failed_vacancy_detail_head_sha'], '1f2dacad3c222408e180d45c72a340332667237e')
        self.assertEqual(data['retry_generation'], 2)
        self.assertEqual(data['previous_recovery_run_id'], '33435997228')
        self.assertEqual(data['previous_recovery_failure'], 'GITHUB_ARTIFACT_DOWNLOAD_503_BEFORE_SHARD14_NO_WEB_RESEARCH_EXECUTED')
        self.assertEqual(data['transport_retry_contract'], 'GITHUB_ARTIFACT_DOWNLOAD_RETRY_5_ALL_ERRORS_DELAY_2_MAX_90_SECONDS')
        self.assertEqual(data['missing_shard_indexes'], [14])
        self.assertEqual(data['reused_successful_shards'], 43)
        self.assertEqual(len(data['expected_reused_indexes']), 43)
        self.assertEqual(sorted(data['expected_reused_indexes'] + data['missing_shard_indexes']), list(range(44)))
        self.assertTrue(data['mixed_observation_epochs_expected'])
        self.assertEqual(
            data['recovery_observed_at_semantics'],
            'STAMP_AT_ACTUAL_ACTIONS_EXECUTION_NOT_AT_REQUEST_CREATION',
        )
        self.assertNotIn('recovery_observed_at', data)
        self.assertEqual(data['application_adversarial_gate_required'], 'APPLICATION-ADVERSARIAL-GATE-3.0')
        self.assertFalse(data['safety']['authority_advanced'])
        self.assertFalse(data['safety']['final_send_ready'])
        self.assertEqual(data['safety']['outbound'], 'CLOSED')
        self.assertEqual(data['safety']['send_allowed'], 0)

    def test_shard14_recovery_workflow_is_minimal_exact_timestamped_retry_bounded_and_no_send(self):
        text = Path('.github/workflows/vacancy-detail-recover-shard14.yml').read_text(encoding='utf-8')
        self.assertNotIn('gh pr create', text)
        self.assertIn('failed_vacancy_detail_run_id', text)
        self.assertIn('reused_successful_shards', text)
        self.assertIn('--shard-index 14', text)
        self.assertIn('assert len(files) == 43', text)
        self.assertIn('assert len(files) == 44', text)
        self.assertIn("assert sorted(indexes) == request['expected_reused_indexes']", text)
        self.assertIn('indexes == list(range(44))', text)
        self.assertIn('python -m swiss_os.vacancy_detail_fault_isolation', text)
        self.assertIn("date -u +'%Y-%m-%dT%H:%M:%SZ'", text)
        self.assertIn('recovery-observed-at.txt', text)
        self.assertNotIn("['recovery_observed_at']", text)
        self.assertGreaterEqual(text.count('--retry 5'), 3)
        self.assertGreaterEqual(text.count('--retry-all-errors'), 3)
        self.assertGreaterEqual(text.count('--retry-delay 2'), 3)
        self.assertGreaterEqual(text.count('--retry-max-time 90'), 3)
        self.assertIn("'mixed_observation_epochs':True", text)
        self.assertIn("'outbound':'CLOSED'", text)
        self.assertIn("'send_allowed':0", text)
        self.assertIn('authorized interactive orchestrator', text)

    def test_numeric_order_regression_fixture(self):
        filenames = [
            'vacancy-detail-shard-1.json',
            'vacancy-detail-shard-10.json',
            'vacancy-detail-shard-2.json',
        ]
        lexical = [int(name.removeprefix('vacancy-detail-shard-').removesuffix('.json')) for name in sorted(filenames)]
        self.assertEqual(lexical, [1, 10, 2])
        self.assertEqual(sorted(lexical), [1, 2, 10])

    def test_recovered_market_summary_receipt_match(self):
        summary = json.loads(Path('docs/state/market/runs/33336272106/summary.json').read_text(encoding='utf-8'))
        receipt = json.loads(Path('docs/state/market/runs/33336272106/receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['aggregate_sha256'], receipt['aggregate_sha256'])
        self.assertEqual(summary['summary_sha256'], receipt['summary_sha256'])
        self.assertEqual(summary['hotels_with_opening_routes'], 436)
        self.assertEqual(summary['source_records'], 2061)
        self.assertFalse(summary['authority_advanced'])
        self.assertEqual(summary['outbound'], 'CLOSED')
        self.assertEqual(summary['send_allowed'], 0)


if __name__ == '__main__':
    unittest.main()

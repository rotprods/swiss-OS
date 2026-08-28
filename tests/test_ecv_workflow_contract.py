from __future__ import annotations

from pathlib import Path
import unittest


class EcvWorkflowContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = Path('.github/workflows/ecv-live-batch-canary.yml').read_text(encoding='utf-8')

    def test_manual_and_main_push_routes_are_both_declared(self) -> None:
        self.assertIn('workflow_dispatch:', self.workflow)
        self.assertIn('push:', self.workflow)
        self.assertIn("'docs/state/CMI_WORK_BATCH_*.json'", self.workflow)
        self.assertIn('fetch-depth: 0', self.workflow)

    def test_push_route_resolves_exactly_one_changed_batch_fail_closed(self) -> None:
        self.assertIn('git diff --name-only "$BEFORE_SHA" "$AFTER_SHA"', self.workflow)
        self.assertIn('[[ ${#changed_batches[@]} -ne 1 ]]', self.workflow)
        self.assertIn('push-triggered ECV requires exactly one changed CMI work batch', self.workflow)
        self.assertIn('docs/state/CMI_WORK_BATCH_*.json) ;;', self.workflow)

    def test_live_provider_pacing_is_conservative(self) -> None:
        self.assertIn('--delay 3.0', self.workflow)
        self.assertIn('--attempts 3', self.workflow)
        self.assertIn('timeout-minutes: 30', self.workflow)

    def test_safety_lock_remains_explicit(self) -> None:
        self.assertIn("assert p['authority_advanced'] is False", self.workflow)
        self.assertIn("assert p['h_id_allocations'] == 0", self.workflow)
        self.assertIn("assert p['outbound'] == 'CLOSED'", self.workflow)
        self.assertIn("assert p['send_allowed'] == 0", self.workflow)


if __name__ == '__main__':
    unittest.main()

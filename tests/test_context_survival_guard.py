import copy
import json
import unittest
from pathlib import Path

from scripts.context_survival_guard import CHECKPOINT, validate_checkpoint


class ContextSurvivalGuardTests(unittest.TestCase):
    def test_live_checkpoint_is_reconstructable_and_safe(self):
        payload = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        self.assertEqual(validate_checkpoint(payload), [])
        self.assertEqual(payload["primary_program"], "REPO_ARCHAEOLOGY_GRAPHIFY_V1")
        self.assertEqual(payload["latest_domain_next"], "docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B02.json")
        self.assertEqual(payload["production_route"], "CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B03")
        self.assertFalse(payload["safety"]["authority_advance_allowed"])
        self.assertFalse(payload["safety"]["canonical_id_allocation_allowed"])
        self.assertEqual(payload["safety"]["canonical_id_reservations_from_staging"], 0)
        self.assertEqual(payload["safety"]["outbound"], "CLOSED")
        self.assertEqual(payload["safety"]["send_allowed"], 0)

    def test_unsafe_checkpoint_fails_closed(self):
        payload = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        unsafe = copy.deepcopy(payload)
        unsafe["safety"]["authority_advance_allowed"] = True
        errors = validate_checkpoint(unsafe)
        self.assertIn("SAFETY_LOCK_MISMATCH:authority_advance_allowed", errors)
        self.assertIn("PAYLOAD_HASH_MISMATCH", errors)

    def test_metaprompt_is_zero_context_and_not_scheduler_routed(self):
        text = Path("docs/handoffs/NEXT_ITERATION_METAPROMPT_V3.md").read_text(encoding="utf-8")
        self.assertIn("This is NOT a request to create, edit, resume, or inspect a scheduled task", text)
        self.assertIn("CHAT/MODEL MEMORY IS DISPOSABLE CACHE", text)
        self.assertIn("START NOW WITH ZERO-CONTEXT BOOTSTRAP", text)

    def test_checkpoint_generation_requires_explicit_domain_next(self):
        text = Path("scripts/context_survival_guard.py").read_text(encoding="utf-8")
        self.assertIn("--latest-domain-next is required with --write", text)
        self.assertNotIn("DEFAULT_DOMAIN_NEXT", text)


if __name__ == "__main__":
    unittest.main()

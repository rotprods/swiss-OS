import copy
import json
import unittest
from pathlib import Path

from scripts.context_survival_guard import CHECKPOINT, validate_checkpoint


RECOVERY_CONFIG = Path("docs/refactor-v2/coordination_recovery_token8_config.json")
ROOT_NEXT = Path("docs/state/NEXT.json")
ACTIVE_CLAIMS = Path("docs/state/v2/active-claims.json")


class ContextSurvivalGuardTests(unittest.TestCase):
    def test_live_checkpoint_is_reconstructable_and_safe(self):
        payload = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        config = json.loads(RECOVERY_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(validate_checkpoint(payload), [])
        self.assertEqual(payload["primary_program"], config["primary_program"])

        # The live domain NEXT is intentionally mutable. Test the continuity
        # invariant (checkpoint -> pinned NEXT -> route), not a historical Bxx
        # literal that becomes stale after every legitimate COLETTE wave.
        latest_domain_next = payload["latest_domain_next"]
        self.assertIn(latest_domain_next, payload["survival_paths"])
        self.assertTrue(latest_domain_next.startswith("docs/state/NEXT_"))
        domain_next_path = Path(latest_domain_next)
        self.assertTrue(domain_next_path.is_file())
        domain_next = json.loads(domain_next_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["production_route"], domain_next["route"])

        self.assertFalse(payload["safety"]["authority_advance_allowed"])
        self.assertFalse(payload["safety"]["canonical_id_allocation_allowed"])
        self.assertEqual(payload["safety"]["canonical_id_reservations_from_staging"], 0)
        self.assertEqual(payload["safety"]["outbound"], "CLOSED")
        self.assertEqual(payload["safety"]["send_allowed"], 0)

    def test_primary_program_is_explicit_durable_state_not_historical_literal(self):
        payload = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        config = json.loads(RECOVERY_CONFIG.read_text(encoding="utf-8"))
        self.assertIn("primary_program", config)
        self.assertTrue(config["primary_program"].strip())
        self.assertEqual(payload["primary_program"], config["primary_program"])
        self.assertNotEqual(payload["primary_program"], "REPO_ARCHAEOLOGY_GRAPHIFY_V1")

    def test_root_next_active_claim_matches_durable_active_claim_projection(self):
        next_payload = json.loads(ROOT_NEXT.read_text(encoding="utf-8"))
        active = json.loads(ACTIVE_CLAIMS.read_text(encoding="utf-8"))
        claims = active.get("claims", [])
        self.assertEqual(len(claims), 1)
        projected = claims[0]
        root_claim = next_payload["active_claim"]
        self.assertEqual(root_claim["claim_id"], projected["claim_id"])
        self.assertEqual(root_claim["fencing_token"], projected["fencing_token"])
        self.assertEqual(root_claim["authority_ceiling"], projected["authority_ceiling"])
        self.assertEqual(active["fencing_high_watermark"], root_claim["fencing_token"])

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

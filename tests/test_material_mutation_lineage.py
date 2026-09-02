import os
import unittest
from unittest.mock import patch

import scripts.material_mutation_lineage_guard as guard


class MaterialMutationLineageTests(unittest.TestCase):
    def test_non_material_readme_can_pass_without_claim(self):
        with patch.object(guard, "active_claims", return_value=[]):
            self.assertEqual(guard.validate(["README.md"], require_receipt=False), [])

    def test_material_change_requires_exactly_one_claim(self):
        with patch.object(guard, "active_claims", return_value=[]):
            self.assertIn(
                "MATERIAL_CHANGE_REQUIRES_EXACTLY_ONE_ACTIVE_CLAIM:0",
                guard.validate(["src/swiss_os/x.py"], require_receipt=False),
            )

    def test_path_outside_claim_scope_fails(self):
        claim = {
            "branch": "feat/x",
            "resource_scopes": ["src/swiss_os/allowed.py"],
            "session_id": "SES-1",
            "claim_id": "CLAIM-1",
            "fencing_token": 13,
        }
        hb = {"graph_program": "GRAPH-REFACTOR-V2", "claim_id": "CLAIM-1", "fencing_token": 13, "state": "ACTIVE"}
        with patch.object(guard, "active_claims", return_value=[claim]), patch.object(guard, "latest_heartbeats", return_value={"SES-1": hb}), patch.dict(os.environ, {"GITHUB_HEAD_REF": "feat/x"}, clear=False):
            self.assertIn("MATERIAL_PATH_OUTSIDE_CLAIM_SCOPE:src/swiss_os/other.py", guard.validate(["src/swiss_os/other.py"], require_receipt=False))

    def test_claim_and_heartbeat_allow_inflight_material_pr(self):
        claim = {
            "branch": "feat/x",
            "resource_scopes": ["src/swiss_os/**"],
            "session_id": "SES-1",
            "claim_id": "CLAIM-1",
            "fencing_token": 13,
        }
        hb = {"graph_program": "GRAPH-REFACTOR-V2", "claim_id": "CLAIM-1", "fencing_token": 13, "state": "ACTIVE"}
        with patch.object(guard, "active_claims", return_value=[claim]), patch.object(guard, "latest_heartbeats", return_value={"SES-1": hb}), patch.dict(os.environ, {"GITHUB_HEAD_REF": "feat/x"}, clear=False):
            self.assertEqual(guard.validate(["src/swiss_os/other.py"], require_receipt=False), [])

    def test_main_material_change_requires_receipt(self):
        claim = {
            "branch": "feat/x",
            "resource_scopes": ["src/swiss_os/**"],
            "session_id": "SES-1",
            "claim_id": "CLAIM-1",
            "fencing_token": 13,
        }
        hb = {"graph_program": "GRAPH-REFACTOR-V2", "claim_id": "CLAIM-1", "fencing_token": 13, "state": "COMPLETE"}
        with patch.object(guard, "active_claims", return_value=[claim]), patch.object(guard, "latest_heartbeats", return_value={"SES-1": hb}), patch.object(guard, "receipt_sessions", return_value=set()), patch.dict(os.environ, {"GITHUB_HEAD_REF": "", "GITHUB_REF_NAME": "main"}, clear=False):
            self.assertIn("MATERIAL_CHANGE_MISSING_ITERATION_RECEIPT:SES-1", guard.validate(["src/swiss_os/other.py"], require_receipt=True))

    def test_main_material_change_with_receipt_passes(self):
        claim = {
            "branch": "feat/x",
            "resource_scopes": ["src/swiss_os/**"],
            "session_id": "SES-1",
            "claim_id": "CLAIM-1",
            "fencing_token": 13,
        }
        hb = {"graph_program": "GRAPH-REFACTOR-V2", "claim_id": "CLAIM-1", "fencing_token": 13, "state": "COMPLETE"}
        with patch.object(guard, "active_claims", return_value=[claim]), patch.object(guard, "latest_heartbeats", return_value={"SES-1": hb}), patch.object(guard, "receipt_sessions", return_value={"SES-1"}), patch.dict(os.environ, {"GITHUB_HEAD_REF": "", "GITHUB_REF_NAME": "main"}, clear=False):
            self.assertEqual(guard.validate(["src/swiss_os/other.py"], require_receipt=True), [])


if __name__ == "__main__":
    unittest.main()

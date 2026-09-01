import json
from pathlib import Path
import unittest

from swiss_os.agent_improvement_runtime import GRAPH_PROGRAM
from swiss_os.session_runtime import (
    build_registry,
    derive_progress,
    derive_session_runtime,
)
from swiss_os.session_runtime_views import build_session_bundle

ROOT = Path(__file__).resolve().parents[1]

BASE = {
    "project_id": "SWITZERLAND_JOB_OS",
    "agent_id": "AGENT-A",
    "session_id": "SES-A",
    "workstream_id": "WS-A",
    "objective_id": "OBJ-A",
    "correlation_id": "CORR-A",
    "repo": "rotprods/swiss-OS",
    "main_sha_observed": "a" * 40,
    "base_sha": "a" * 40,
    "authority_ceiling": "TEST_ONLY",
    "summary": "fixture",
    "next_action": "next",
    "idempotency_key": "fixture",
    "canonical_hotel_mutation_allowed": False,
    "h_id_allocation_allowed": False,
    "outbound_allowed": False,
}


def event(event_id: str, event_type: str, occurred_at: str, **extra):
    return {**BASE, "event_id": event_id, "event_type": event_type, "occurred_at": occurred_at, **extra}


def claim(state: str = "ACTIVE"):
    return {"session_id": "SES-A", "claim_id": "CLAIM-A", "state": state, "fencing_token": 12}


def identity():
    return {
        "graph_program": GRAPH_PROGRAM,
        "goal_ids": ["G-0001"],
        "plan_id": "PLAN-A",
        "task_id": "TASK-A",
        "claim_id": "CLAIM-A",
        "fencing_token": 12,
        "worktree": "REMOTE_GITHUB_CONNECTOR_ONLY",
        "branch": "feat/a",
        "base_main_sha": "a" * 40,
        "authority_ceiling": "TEST_ONLY",
        "pr_number": None,
    }


class SessionRuntimeTests(unittest.TestCase):
    def test_progress_is_weight_derived_not_agent_reported(self):
        progress = derive_progress({
            "plan_revision": "P1",
            "items": [
                {"item_id": "A", "state": "COMPLETED", "weight": 2},
                {"item_id": "B", "state": "IN_PROGRESS", "weight": 1},
                {"item_id": "C", "state": "PENDING", "weight": 1},
            ],
        })
        self.assertEqual(progress["completion_percent"], 50.0)
        self.assertEqual(progress["completed_weight"], 2.0)
        self.assertEqual(progress["total_weight"], 4.0)

    def test_arbitrary_percent_is_forbidden(self):
        with self.assertRaisesRegex(ValueError, "ARBITRARY_PROGRESS_PERCENT_FORBIDDEN"):
            derive_progress({
                "plan_revision": "P1",
                "percent": 99,
                "items": [{"item_id": "A", "state": "PENDING", "weight": 1}],
            })

    def test_chat_id_is_never_fabricated_when_harness_hides_it(self):
        runtime = derive_session_runtime([
            event(
                "E1", "WORK_STARTED", "2026-09-01T21:00:00Z",
                runtime_locator={"provider": "chatgpt", "chat_id": None, "chat_id_state": "UNAVAILABLE_BY_HARNESS"},
            )
        ], [], observed_at="2026-09-01T21:10:00Z")
        self.assertIsNone(runtime["runtime_locator"]["chat_id"])
        self.assertEqual(runtime["runtime_locator"]["chat_id_state"], "UNAVAILABLE_BY_HARNESS")

    def test_graph_runtime_identity_reuses_autoresearch_contract(self):
        runtime = derive_session_runtime([
            event(
                "E1", "HEARTBEAT", "2026-09-01T22:00:00Z", branch="feat/a",
                runtime_identity_required=True, runtime_identity=identity(),
            )
        ], [claim()], observed_at="2026-09-01T22:01:00Z")
        self.assertEqual(runtime["graph_runtime_identity_state"], "REPORTED")
        self.assertEqual(runtime["graph_runtime_identity"]["claim_id"], "CLAIM-A")
        self.assertNotIn("GRAPH_RUNTIME_IDENTITY_MISSING", runtime["violations"])

    def test_missing_required_runtime_identity_fails_visible(self):
        runtime = derive_session_runtime([
            event("E1", "HEARTBEAT", "2026-09-01T22:00:00Z", runtime_identity_required=True)
        ], [claim()], observed_at="2026-09-01T22:01:00Z")
        self.assertIn("GRAPH_RUNTIME_IDENTITY_MISSING", runtime["violations"])

    def test_native_session_becomes_stale_then_orphan_candidate_not_dead(self):
        ev = event(
            "E1", "HEARTBEAT", "2026-09-01T20:00:00Z", branch="feat/a",
            runtime_identity_required=True, runtime_identity=identity(),
        )
        stale = derive_session_runtime([ev], [claim()], observed_at="2026-09-01T21:30:00Z")
        orphan = derive_session_runtime([ev], [claim()], observed_at="2026-09-02T00:00:01Z")
        self.assertEqual(stale["liveness"], "STALE")
        self.assertEqual(orphan["liveness"], "ORPHANED_CANDIDATE")
        self.assertEqual(orphan["lifecycle_state"], "ACTIVE")

    def test_terminal_work_event_wins_over_ttl(self):
        runtime = derive_session_runtime([
            event("E1", "WORK_STARTED", "2026-09-01T20:00:00Z"),
            event("E2", "WORK_COMPLETED", "2026-09-01T20:10:00Z"),
        ], [], observed_at="2026-09-02T03:00:00Z")
        self.assertEqual(runtime["lifecycle_state"], "COMPLETED")
        self.assertEqual(runtime["liveness"], "TERMINAL")

    def test_claim_release_does_not_fabricate_work_completion(self):
        runtime = derive_session_runtime([
            event("E1", "WORK_STARTED", "2026-09-01T21:41:00Z")
        ], [claim("RELEASED")], observed_at="2026-09-01T22:15:00Z")
        self.assertEqual(runtime["lifecycle_state"], "ACTIVE")
        self.assertEqual(runtime["lifecycle_detail"], "CLAIM_RELEASED_BUT_WORK_NOT_TERMINAL")
        self.assertEqual(runtime["liveness"], "LEGACY_UNKNOWN")

    def test_pre_srp_history_without_claim_is_not_falsely_orphaned(self):
        runtime = derive_session_runtime([
            event("E1", "WORK_STARTED", "2026-08-20T10:00:00Z")
        ], [], observed_at="2026-09-01T22:00:00Z")
        self.assertEqual(runtime["srp_contract_state"], "LEGACY_OR_PRE_SRP")
        self.assertEqual(runtime["liveness"], "LEGACY_UNKNOWN")

    def test_registry_marks_branch_and_drive_observations_non_authoritative(self):
        runtime = derive_session_runtime([
            event("E1", "WORK_COMPLETED", "2026-09-01T21:00:00Z")
        ], [], observed_at="2026-09-01T22:00:00Z")
        registry = build_registry(
            [runtime], observed_at="2026-09-01T22:00:00Z",
            unmerged_proposals=[{"session_id": "SES-B", "state": "UNMERGED_PROPOSAL", "pr_number": 428}],
            live_leases=[{"session_id": "SES-C", "state": "ACTIVE", "source": "AGENT_WORK_LEASES"}],
        )
        self.assertIn("OBSERVABILITY_ONLY", registry["authority_contract"])
        self.assertEqual(registry["summary"]["unmerged_proposal_count"], 1)
        self.assertEqual(registry["summary"]["live_lease_count"], 1)

    def test_bundle_contains_all_requested_recovery_views(self):
        runtime = derive_session_runtime([
            event(
                "E1", "HEARTBEAT", "2026-09-01T22:00:00Z", branch="feat/a",
                runtime_identity_required=True, runtime_identity=identity(),
                runtime_locator={"provider": "chatgpt", "chat_id": None, "chat_id_state": "UNAVAILABLE_BY_HARNESS"},
                progress_snapshot={
                    "plan_revision": "P1",
                    "items": [
                        {"item_id": "I1", "state": "COMPLETED", "weight": 1, "summary": "done"},
                        {"item_id": "I2", "state": "PENDING", "weight": 1, "summary": "next"},
                    ],
                },
                recovery_inputs=["main:a"],
            )
        ], [claim()], observed_at="2026-09-01T22:01:00Z")
        files = build_session_bundle(runtime)
        self.assertEqual(set(files), {
            "session.json", "progress.state.json", "PROGRESS.md", "GOALS.md",
            "CONTEXT.md", "HANDOFF.md", "MANIFEST.json",
        })
        manifest = json.loads(files["MANIFEST.json"])
        self.assertEqual(len(manifest["files"]), 6)
        self.assertIn("I2", files["HANDOFF.md"])
        self.assertIn("UNAVAILABLE_BY_HARNESS", files["CONTEXT.md"])

    def test_current_token12_heartbeat_is_self_describing(self):
        event_path = ROOT / "docs/state/v2/events/EVT-20260901T222600Z-SRP-HEARTBEAT-001.json"
        claim_path = ROOT / "docs/state/v2/claims/CLAIM-SRP-RUNTIME-OBSERVABILITY-012.json"
        ev = json.loads(event_path.read_text(encoding="utf-8"))
        cl = json.loads(claim_path.read_text(encoding="utf-8"))
        runtime = derive_session_runtime([ev], [cl], observed_at="2026-09-01T22:27:00Z")
        self.assertEqual(runtime["session_id"], "SES-20260901T221937Z-SRP-012")
        self.assertEqual(runtime["claims"]["max_fencing_token"], 12)
        self.assertEqual(runtime["liveness"], "LIVE")
        self.assertEqual(runtime["progress"]["completion_percent"], 10.0)


if __name__ == "__main__":
    unittest.main()

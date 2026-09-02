import unittest

from swiss_os.agent_improvement_runtime import AgentRunContext, IterationProposal, MetricSpec, evaluate_iteration
from swiss_os.agent_runtime_graph import assert_takeover_safe, reduce_agent_runtime_graph


class AgentRuntimeGraphTests(unittest.TestCase):
    def receipt(self, session="SES-A", agent="AGENT-A", claim="CLAIM-A", token=1, decision_metric=2, worktree=".worktrees/a", branch="agent/a"):
        ctx = AgentRunContext(
            project_id="SWITZERLAND_JOB_OS", agent_id=agent, session_id=session,
            workstream_id="WS-X", objective_id="OBJ-X", correlation_id=f"CORR-{session}",
            goal_ids=("G-0001",), plan_id="PLAN-X", task_id="TASK-X", claim_id=claim,
            fencing_token=token, branch=branch, worktree=worktree, base_main_sha="a" * 40,
            authority_ceiling="TEST_ONLY", pr_number=100 + token,
        )
        proposal = IterationProposal(hypothesis=f"improve from {session}", changed_paths=("x.py",), evaluation_suite=("unit", "death_drill"), budget_seconds=60)
        return evaluate_iteration(ctx, proposal, (MetricSpec("quality", "MAX", 1, decision_metric, min_meaningful_delta=.1),), tests_passed=True).as_record()

    def hb(self, *, session, agent, claim, token, observed_at, state="ACTIVE", worktree=".worktrees/a", branch="agent/a"):
        return {
            "heartbeat_id": f"HB-{session}-{observed_at}", "project_id": "SWITZERLAND_JOB_OS",
            "agent_id": agent, "session_id": session, "workstream_id": "WS-X", "objective_id": "OBJ-X",
            "goal_ids": ["G-0001"], "plan_id": "PLAN-X", "task_id": "TASK-X", "claim_id": claim,
            "fencing_token": token, "observed_at": observed_at, "state": state, "branch": branch, "worktree": worktree,
            "base_main_sha": "a" * 40, "authority_ceiling": "TEST_ONLY", "graph_program": "GRAPH-REFACTOR-V2",
            "pr_number": 100 + token, "current_iteration_id": None, "next_safe_action": "resume exact task from heartbeat",
        }

    def test_heartbeat_alone_reconstructs_full_active_work_graph(self):
        graph = reduce_agent_runtime_graph([], [self.hb(session="SES-A", agent="AGENT-A", claim="CLAIM-A", token=1, observed_at="2026-09-01T22:20:00Z")], as_of="2026-09-01T22:20:10Z")
        self.assertEqual(graph["violations"], [])
        types = {n["type"] for n in graph["nodes"]}
        for expected in {"Agent", "Session", "Goal", "Plan", "Task", "Claim", "Worktree", "Branch", "PullRequest", "Heartbeat"}:
            self.assertIn(expected, types)

    def test_global_projection_contains_hypothesis_and_evaluator(self):
        graph = reduce_agent_runtime_graph([self.receipt()], [self.hb(session="SES-A", agent="AGENT-A", claim="CLAIM-A", token=1, observed_at="2026-09-01T22:20:00Z")], as_of="2026-09-01T22:20:10Z")
        self.assertEqual(graph["violations"], [])
        types = {n["type"] for n in graph["nodes"]}
        self.assertIn("Hypothesis", types)
        self.assertIn("TestSuite", types)

    def test_discarded_experiment_remains_in_projection(self):
        receipt = self.receipt(decision_metric=1)
        self.assertEqual(receipt["decision"], "DISCARD")
        graph = reduce_agent_runtime_graph([receipt], [], as_of="2026-09-01T22:20:10Z")
        experiments = [n for n in graph["nodes"] if n["type"] == "Experiment"]
        self.assertEqual(len(experiments), 1)
        self.assertEqual(experiments[0]["decision"], "DISCARD")

    def test_session_id_reuse_with_different_identity_fails(self):
        graph = reduce_agent_runtime_graph([
            self.receipt(session="SES-X", agent="AGENT-A", claim="CLAIM-A", token=1),
            self.receipt(session="SES-X", agent="AGENT-B", claim="CLAIM-B", token=2, worktree=".worktrees/b", branch="agent/b"),
        ], [], as_of="2026-09-01T22:20:10Z")
        self.assertTrue(any(v.startswith("SESSION_ID_REUSED_WITH_DIFFERENT_IDENTITY") for v in graph["violations"]))

    def test_dead_agent_takeover_requires_new_session_and_higher_fencing(self):
        receipts = [
            self.receipt(session="SES-DEAD", agent="AGENT-A", claim="CLAIM-A", token=5),
            self.receipt(session="SES-NEW", agent="AGENT-B", claim="CLAIM-B", token=6, worktree=".worktrees/b", branch="agent/b"),
        ]
        hbs = [
            self.hb(session="SES-DEAD", agent="AGENT-A", claim="CLAIM-A", token=5, observed_at="2026-09-01T20:00:00Z"),
            self.hb(session="SES-NEW", agent="AGENT-B", claim="CLAIM-B", token=6, observed_at="2026-09-01T22:19:50Z", worktree=".worktrees/b", branch="agent/b"),
        ]
        graph = reduce_agent_runtime_graph(receipts, hbs, as_of="2026-09-01T22:20:00Z", heartbeat_ttl_seconds=1800)
        assert_takeover_safe(graph, predecessor_session_id="SES-DEAD", successor_session_id="SES-NEW")

    def test_same_scope_two_fresh_writers_marks_lower_token_stale_writer(self):
        graph = reduce_agent_runtime_graph([], [
            self.hb(session="SES-A", agent="AGENT-A", claim="CLAIM-A", token=5, observed_at="2026-09-01T22:19:50Z"),
            self.hb(session="SES-B", agent="AGENT-B", claim="CLAIM-B", token=6, observed_at="2026-09-01T22:19:55Z", worktree=".worktrees/b", branch="agent/b"),
        ], as_of="2026-09-01T22:20:00Z")
        self.assertIn("STALE_ACTIVE_WRITER:SES-A:5<6", graph["violations"])

    def test_fencing_tie_fails_closed(self):
        graph = reduce_agent_runtime_graph([], [
            self.hb(session="SES-A", agent="AGENT-A", claim="CLAIM-A", token=6, observed_at="2026-09-01T22:19:50Z"),
            self.hb(session="SES-B", agent="AGENT-B", claim="CLAIM-B", token=6, observed_at="2026-09-01T22:19:55Z", worktree=".worktrees/b", branch="agent/b"),
        ], as_of="2026-09-01T22:20:00Z")
        self.assertTrue(any(v.startswith("ACTIVE_SCOPE_FENCING_TIE") for v in graph["violations"]))

    def test_future_heartbeat_fails(self):
        graph = reduce_agent_runtime_graph([], [self.hb(session="SES-A", agent="AGENT-A", claim="CLAIM-A", token=1, observed_at="2026-09-02T00:00:00Z")], as_of="2026-09-01T22:20:00Z")
        self.assertIn("FUTURE_HEARTBEAT:SES-A", graph["violations"])


if __name__ == "__main__":
    unittest.main()

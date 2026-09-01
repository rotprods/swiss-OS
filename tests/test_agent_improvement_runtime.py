import unittest

from swiss_os.agent_improvement_runtime import (
    AgentRunContext,
    IterationProposal,
    MetricSpec,
    evaluate_iteration,
)


class AgentImprovementRuntimeTests(unittest.TestCase):
    def context(self):
        return AgentRunContext(
            project_id="SWITZERLAND_JOB_OS",
            agent_id="AGENT-TEST-001",
            session_id="SES-TEST-001",
            workstream_id="WS-TEST-001",
            objective_id="OBJ-TEST-001",
            correlation_id="CORR-TEST-001",
            goal_ids=("G-0001",),
            plan_id="PLAN-TEST-001",
            task_id="TASK-TEST-001",
            claim_id="CLAIM-TEST-001",
            fencing_token=99,
            branch="agent/test-001",
            worktree=".worktrees/agent-test-001",
            base_main_sha="a" * 40,
            authority_ceiling="TEST_ONLY",
            pr_number=999,
        )

    def proposal(self, complexity_delta=0):
        return IterationProposal(
            hypothesis="reduce recovery ambiguity",
            changed_paths=("src/swiss_os/example.py",),
            evaluation_suite=("unit", "death_drill"),
            budget_seconds=900,
            complexity_delta=complexity_delta,
        )

    def test_material_improvement_is_kept(self):
        result = evaluate_iteration(
            self.context(),
            self.proposal(),
            (MetricSpec("recovery_seconds", "MIN", 300, 240, min_meaningful_delta=10, protected=True),),
            tests_passed=True,
        )
        self.assertEqual(result.decision, "KEEP")

    def test_no_improvement_is_discarded(self):
        result = evaluate_iteration(
            self.context(),
            self.proposal(),
            (MetricSpec("recovery_seconds", "MIN", 300, 299, min_meaningful_delta=10, protected=True),),
            tests_passed=True,
        )
        self.assertEqual(result.decision, "DISCARD")

    def test_simplification_win_is_kept(self):
        result = evaluate_iteration(
            self.context(),
            self.proposal(complexity_delta=-20),
            (MetricSpec("failure_rate", "MIN", 0.01, 0.01, protected=True),),
            tests_passed=True,
        )
        self.assertEqual(result.decision, "KEEP")

    def test_hard_gate_failure_discards_even_if_metric_improves(self):
        result = evaluate_iteration(
            self.context(),
            self.proposal(),
            (MetricSpec("recovery_seconds", "MIN", 300, 100, min_meaningful_delta=10),),
            tests_passed=False,
        )
        self.assertEqual(result.decision, "DISCARD")

    def test_protected_metric_regression_discards(self):
        result = evaluate_iteration(
            self.context(),
            self.proposal(),
            (
                MetricSpec("speed", "MAX", 10, 20, min_meaningful_delta=1),
                MetricSpec("integrity_errors", "MIN", 0, 1, protected=True),
            ),
            tests_passed=True,
        )
        self.assertEqual(result.decision, "DISCARD")

    def test_graph_contains_agent_session_goal_claim_worktree_pr(self):
        result = evaluate_iteration(
            self.context(),
            self.proposal(),
            (MetricSpec("quality", "MAX", 1, 2, min_meaningful_delta=0.1),),
            tests_passed=True,
        )
        types = {node["type"] for node in result.graph_nodes}
        for expected in {"Agent", "Session", "Goal", "Claim", "Worktree", "PullRequest", "Experiment"}:
            self.assertIn(expected, types)

    def test_graph_refactor_v2_is_mandatory(self):
        ctx = self.context()
        bad = AgentRunContext(**{**ctx.__dict__, "graph_program": "OTHER"})
        with self.assertRaises(ValueError):
            evaluate_iteration(
                bad,
                self.proposal(),
                (MetricSpec("quality", "MAX", 1, 2),),
                tests_passed=True,
            )

    def test_crash_and_blocked_are_persistable_decisions(self):
        crash = evaluate_iteration(self.context(), self.proposal(), (), tests_passed=False, crashed=True)
        blocked = evaluate_iteration(self.context(), self.proposal(), (), tests_passed=False, blocked_reason="AUTHORITY_BLOCK")
        self.assertEqual(crash.decision, "CRASH")
        self.assertEqual(blocked.decision, "BLOCKED")


if __name__ == "__main__":
    unittest.main()

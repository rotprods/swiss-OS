#!/usr/bin/env python3
from pathlib import Path

from swiss_os.agent_improvement_runtime import (
    AgentRunContext,
    IterationProposal,
    MetricSpec,
    evaluate_iteration,
)

ROOT = Path(__file__).resolve().parents[1]


def require(path: str, needle: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    if needle not in text:
        raise SystemExit(f"agent_improvement_guard: missing {needle!r} in {path}")


def main() -> int:
    require("AGENTS.md", "Mandatory GRAPH-REFACTOR-V2 bootstrap")
    require("AGENTS.md", "AGENT_AUTORESEARCH_PROGRAM.md")
    require("docs/operations/AGENT_AUTORESEARCH_PROGRAM.md", "KEEP | DISCARD | CRASH | BLOCKED")
    require("docs/operations/AGENT_AUTORESEARCH_PROGRAM.md", "Worktree / PR runtime graph")

    ctx = AgentRunContext(
        project_id="SWITZERLAND_JOB_OS",
        agent_id="AGENT-GUARD",
        session_id="SES-GUARD",
        workstream_id="WS-GUARD",
        objective_id="OBJ-GUARD",
        correlation_id="CORR-GUARD",
        goal_ids=("G-0001",),
        plan_id="PLAN-GUARD",
        task_id="TASK-GUARD",
        claim_id="CLAIM-GUARD",
        fencing_token=1,
        branch="guard/runtime",
        worktree=".worktrees/guard-runtime",
        base_main_sha="a" * 40,
        authority_ceiling="TEST_ONLY",
        pr_number=1,
    )
    result = evaluate_iteration(
        ctx,
        IterationProposal(
            hypothesis="guard runtime graph",
            changed_paths=("AGENTS.md",),
            evaluation_suite=("agent_improvement_guard",),
            budget_seconds=60,
        ),
        (MetricSpec("recoverability", "MAX", 0, 1, min_meaningful_delta=0.1, protected=True),),
        tests_passed=True,
    )
    if result.decision != "KEEP":
        raise SystemExit("agent_improvement_guard: runtime did not keep positive control")
    node_types = {node["type"] for node in result.graph_nodes}
    required = {"Agent", "Session", "Goal", "Claim", "Worktree", "PullRequest", "Experiment"}
    missing = required - node_types
    if missing:
        raise SystemExit(f"agent_improvement_guard: runtime graph missing {sorted(missing)}")
    print("agent_improvement_guard: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

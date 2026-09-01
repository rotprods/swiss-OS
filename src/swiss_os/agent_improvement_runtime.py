from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Iterable, Mapping, Sequence

GRAPH_PROGRAM = "GRAPH-REFACTOR-V2"
DECISIONS = frozenset({"KEEP", "DISCARD", "CRASH", "BLOCKED"})
DIRECTIONS = frozenset({"MIN", "MAX"})


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_id(prefix: str, value: object, length: int = 20) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode()).hexdigest()[:length]
    return f"{prefix}-{digest}"


@dataclass(frozen=True)
class AgentRunContext:
    project_id: str
    agent_id: str
    session_id: str
    workstream_id: str
    objective_id: str
    correlation_id: str
    goal_ids: tuple[str, ...]
    plan_id: str
    task_id: str
    claim_id: str
    fencing_token: int
    branch: str
    worktree: str
    base_main_sha: str
    authority_ceiling: str
    graph_program: str = GRAPH_PROGRAM
    pr_number: int | None = None

    def validate(self) -> None:
        required = {
            "project_id": self.project_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "workstream_id": self.workstream_id,
            "objective_id": self.objective_id,
            "correlation_id": self.correlation_id,
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "claim_id": self.claim_id,
            "branch": self.branch,
            "worktree": self.worktree,
            "base_main_sha": self.base_main_sha,
            "authority_ceiling": self.authority_ceiling,
        }
        missing = sorted(key for key, value in required.items() if not str(value).strip())
        if missing:
            raise ValueError(f"missing run context fields: {missing}")
        if self.graph_program != GRAPH_PROGRAM:
            raise ValueError("every material agent iteration must run under GRAPH-REFACTOR-V2")
        if not self.goal_ids or any(not goal.strip() for goal in self.goal_ids):
            raise ValueError("at least one durable goal_id is required")
        if isinstance(self.fencing_token, bool) or self.fencing_token < 1:
            raise ValueError("positive fencing_token required")
        if len(self.base_main_sha) != 40 or any(c not in "0123456789abcdef" for c in self.base_main_sha):
            raise ValueError("base_main_sha must be lowercase 40-hex")


@dataclass(frozen=True)
class MetricSpec:
    metric_id: str
    direction: str
    baseline: float
    candidate: float
    min_meaningful_delta: float = 0.0
    max_allowed_regression: float = 0.0
    protected: bool = False

    def validate(self) -> None:
        if not self.metric_id.strip():
            raise ValueError("metric_id required")
        if self.direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {sorted(DIRECTIONS)}")
        if self.min_meaningful_delta < 0 or self.max_allowed_regression < 0:
            raise ValueError("metric tolerances cannot be negative")

    @property
    def signed_delta(self) -> float:
        raw = self.candidate - self.baseline
        return raw if self.direction == "MAX" else -raw

    @property
    def improved(self) -> bool:
        return self.signed_delta > self.min_meaningful_delta

    @property
    def regressed_beyond_tolerance(self) -> bool:
        return self.signed_delta < -self.max_allowed_regression


@dataclass(frozen=True)
class IterationProposal:
    hypothesis: str
    changed_paths: tuple[str, ...]
    evaluation_suite: tuple[str, ...]
    budget_seconds: int
    complexity_delta: int = 0
    reversible: bool = True
    notes: str = ""

    def validate(self) -> None:
        if not self.hypothesis.strip():
            raise ValueError("hypothesis required")
        if not self.changed_paths:
            raise ValueError("changed_paths required")
        if not self.evaluation_suite:
            raise ValueError("evaluation_suite required")
        if self.budget_seconds <= 0:
            raise ValueError("budget_seconds must be positive")


@dataclass(frozen=True)
class IterationResult:
    iteration_id: str
    context: Mapping[str, object]
    proposal: Mapping[str, object]
    decision: str
    reason: str
    metric_results: tuple[MetricSpec, ...]
    tests_passed: bool
    invariant_violations: tuple[str, ...]
    security_violations: tuple[str, ...]
    complexity_delta: int
    graph_nodes: tuple[Mapping[str, object], ...] = field(default_factory=tuple)
    graph_edges: tuple[Mapping[str, object], ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if self.decision not in DECISIONS:
            raise ValueError(f"invalid decision {self.decision}")
        if not self.iteration_id.strip() or not self.reason.strip():
            raise ValueError("iteration_id and reason required")
        if not self.context or not self.proposal:
            raise ValueError("complete context and proposal are required for durable learning")

    def as_record(self) -> dict[str, object]:
        value = asdict(self)
        value["schema_version"] = "AGENT-IMPROVEMENT-ITERATION-1.1"
        return value


def evaluate_iteration(
    context: AgentRunContext,
    proposal: IterationProposal,
    metrics: Sequence[MetricSpec],
    *,
    tests_passed: bool,
    invariant_violations: Iterable[str] = (),
    security_violations: Iterable[str] = (),
    crashed: bool = False,
    blocked_reason: str | None = None,
) -> IterationResult:
    """Autoresearch-style keep/discard with hard graph/safety gates."""
    context.validate()
    proposal.validate()
    for metric in metrics:
        metric.validate()

    invariant_violations = tuple(sorted(set(invariant_violations)))
    security_violations = tuple(sorted(set(security_violations)))
    iteration_id = _stable_id(
        "ITER",
        {
            "session_id": context.session_id,
            "task_id": context.task_id,
            "claim_id": context.claim_id,
            "hypothesis": proposal.hypothesis,
            "paths": proposal.changed_paths,
            "baseline": [(m.metric_id, m.baseline) for m in metrics],
        },
    )

    if crashed:
        decision, reason = "CRASH", "experiment crashed; code must be reverted but evidence retained"
    elif blocked_reason:
        decision, reason = "BLOCKED", blocked_reason
    elif invariant_violations or security_violations or not tests_passed:
        decision, reason = "DISCARD", "hard QA/security/invariant gate failed"
    else:
        protected_regressions = [m.metric_id for m in metrics if m.protected and m.regressed_beyond_tolerance]
        improvements = [m.metric_id for m in metrics if m.improved]
        simplification_win = proposal.complexity_delta < 0 and not any(m.regressed_beyond_tolerance for m in metrics)
        if protected_regressions:
            decision, reason = "DISCARD", f"protected metric regression: {','.join(protected_regressions)}"
        elif improvements:
            decision, reason = "KEEP", f"material improvement: {','.join(improvements)}"
        elif simplification_win:
            decision, reason = "KEEP", "no material metric regression and implementation became simpler"
        else:
            decision, reason = "DISCARD", "no material improvement over baseline"

    graph_nodes, graph_edges = build_iteration_graph(context, proposal, iteration_id, decision)
    result = IterationResult(
        iteration_id=iteration_id,
        context=asdict(context),
        proposal=asdict(proposal),
        decision=decision,
        reason=reason,
        metric_results=tuple(metrics),
        tests_passed=tests_passed,
        invariant_violations=invariant_violations,
        security_violations=security_violations,
        complexity_delta=proposal.complexity_delta,
        graph_nodes=tuple(graph_nodes),
        graph_edges=tuple(graph_edges),
    )
    result.validate()
    return result


def build_iteration_graph(context: AgentRunContext, proposal: IterationProposal, iteration_id: str, decision: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    context.validate()
    proposal.validate()
    nodes: list[dict[str, object]] = [
        {"id": f"PROJECT:{context.project_id}", "type": "Project"},
        {"id": f"AGENT:{context.agent_id}", "type": "Agent"},
        {"id": f"SESSION:{context.session_id}", "type": "Session"},
        {"id": f"WORKSTREAM:{context.workstream_id}", "type": "Workstream"},
        {"id": f"OBJECTIVE:{context.objective_id}", "type": "Objective"},
        {"id": f"PLAN:{context.plan_id}", "type": "Plan"},
        {"id": f"TASK:{context.task_id}", "type": "Task"},
        {"id": f"CLAIM:{context.claim_id}", "type": "Claim", "fencing_token": context.fencing_token},
        {"id": f"WORKTREE:{context.worktree}", "type": "Worktree"},
        {"id": f"BRANCH:{context.branch}", "type": "Branch"},
        {"id": f"ITERATION:{iteration_id}", "type": "Experiment", "decision": decision},
    ]
    for goal_id in context.goal_ids:
        nodes.append({"id": f"GOAL:{goal_id}", "type": "Goal"})
    if context.pr_number is not None:
        nodes.append({"id": f"PR:{context.pr_number}", "type": "PullRequest"})
    for path in proposal.changed_paths:
        nodes.append({"id": f"FILE:{path}", "type": "File"})

    edges: list[dict[str, object]] = [
        {"from": f"AGENT:{context.agent_id}", "to": f"SESSION:{context.session_id}", "type": "EXECUTES"},
        {"from": f"SESSION:{context.session_id}", "to": f"WORKSTREAM:{context.workstream_id}", "type": "EXECUTES"},
        {"from": f"WORKSTREAM:{context.workstream_id}", "to": f"OBJECTIVE:{context.objective_id}", "type": "IMPLEMENTS"},
        {"from": f"PLAN:{context.plan_id}", "to": f"TASK:{context.task_id}", "type": "CONTAINS"},
        {"from": f"TASK:{context.task_id}", "to": f"ITERATION:{iteration_id}", "type": "TESTED_BY"},
        {"from": f"CLAIM:{context.claim_id}", "to": f"TASK:{context.task_id}", "type": "CLAIMS"},
        {"from": f"SESSION:{context.session_id}", "to": f"CLAIM:{context.claim_id}", "type": "OWNS"},
        {"from": f"WORKTREE:{context.worktree}", "to": f"BRANCH:{context.branch}", "type": "CHECKS_OUT"},
        {"from": f"ITERATION:{iteration_id}", "to": f"BRANCH:{context.branch}", "type": "EXECUTED_ON"},
    ]
    for goal_id in context.goal_ids:
        edges.append({"from": f"TASK:{context.task_id}", "to": f"GOAL:{goal_id}", "type": "CONTRIBUTES_TO"})
    if context.pr_number is not None:
        edges.append({"from": f"BRANCH:{context.branch}", "to": f"PR:{context.pr_number}", "type": "PROPOSED_BY"})
    for path in proposal.changed_paths:
        edges.append({"from": f"ITERATION:{iteration_id}", "to": f"FILE:{path}", "type": "MODIFIES"})
    return nodes, edges


def append_jsonl_record(path: str, record: Mapping[str, object]) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(_canonical_json(record) + "\n")

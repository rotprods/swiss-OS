from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Mapping, Sequence

ACTIVE_HEARTBEAT_STATES = frozenset({"ACTIVE", "BLOCKED"})
HEARTBEAT_STATES = frozenset({"ACTIVE", "BLOCKED", "COMPLETE", "SUPERSEDED"})


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _parse_time(value: str) -> datetime:
    if not value:
        raise ValueError("timestamp required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def validate_heartbeat(heartbeat: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    required = (
        "heartbeat_id", "project_id", "agent_id", "session_id", "workstream_id", "objective_id",
        "plan_id", "task_id", "claim_id", "observed_at", "state", "branch", "worktree",
        "base_main_sha", "authority_ceiling", "graph_program", "next_safe_action",
    )
    for key in required:
        if not _text(heartbeat.get(key)):
            errors.append(f"MISSING_{key.upper()}")
    goals = heartbeat.get("goal_ids")
    if not isinstance(goals, list) or not goals or any(not _text(goal) for goal in goals):
        errors.append("INVALID_GOAL_IDS")
    if heartbeat.get("graph_program") != "GRAPH-REFACTOR-V2":
        errors.append("NON_GRAPH_V2_HEARTBEAT")
    sha = _text(heartbeat.get("base_main_sha"))
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        errors.append("INVALID_BASE_MAIN_SHA")
    if heartbeat.get("state") not in HEARTBEAT_STATES:
        errors.append("INVALID_HEARTBEAT_STATE")
    token = heartbeat.get("fencing_token")
    if isinstance(token, bool) or not isinstance(token, int) or token < 1:
        errors.append("INVALID_FENCING_TOKEN")
    try:
        _parse_time(_text(heartbeat.get("observed_at")))
    except ValueError:
        errors.append("INVALID_OBSERVED_AT")
    return errors


def reduce_agent_runtime_graph(
    receipts: Sequence[Mapping[str, object]],
    heartbeats: Sequence[Mapping[str, object]],
    *,
    as_of: str,
    heartbeat_ttl_seconds: int = 1800,
) -> dict[str, object]:
    """Derive a runtime/recovery projection. Claim/event ledgers remain ownership authority."""
    if heartbeat_ttl_seconds <= 0:
        raise ValueError("heartbeat_ttl_seconds must be positive")
    now = _parse_time(as_of)
    violations: list[str] = []
    iteration_ids: set[str] = set()
    session_identity: dict[str, tuple[object, ...]] = {}
    nodes_by_id: dict[str, dict[str, object]] = {}
    edges_by_key: dict[str, dict[str, object]] = {}

    def add_node(node: Mapping[str, object]) -> None:
        node_id = _text(node.get("id"))
        if not node_id:
            violations.append("NODE_WITHOUT_ID")
            return
        candidate = dict(node)
        prior = nodes_by_id.get(node_id)
        if prior is None:
            nodes_by_id[node_id] = candidate
            return
        merged = dict(prior)
        for key, value in candidate.items():
            if key in merged and merged[key] != value:
                violations.append(f"NODE_SEMANTIC_CONFLICT:{node_id}:{key}")
                return
            merged[key] = value
        nodes_by_id[node_id] = merged

    def add_edge(edge: Mapping[str, object]) -> None:
        source, target, edge_type = _text(edge.get("from")), _text(edge.get("to")), _text(edge.get("type"))
        if not source or not target or not edge_type:
            violations.append("INVALID_EDGE")
            return
        candidate = dict(edge)
        edges_by_key[canonical_json(candidate)] = candidate

    for receipt in receipts:
        iteration_id = _text(receipt.get("iteration_id"))
        if not iteration_id:
            violations.append("RECEIPT_WITHOUT_ITERATION_ID")
            continue
        if iteration_id in iteration_ids:
            violations.append(f"DUPLICATE_ITERATION_ID:{iteration_id}")
            continue
        iteration_ids.add(iteration_id)
        if receipt.get("schema_version") != "AGENT-IMPROVEMENT-ITERATION-1.1":
            violations.append(f"UNSUPPORTED_ITERATION_SCHEMA:{iteration_id}")
        context, proposal = receipt.get("context"), receipt.get("proposal")
        if not isinstance(context, Mapping) or not isinstance(proposal, Mapping):
            violations.append(f"INCOMPLETE_ITERATION_RECEIPT:{iteration_id}")
            continue
        if context.get("graph_program") != "GRAPH-REFACTOR-V2":
            violations.append(f"NON_GRAPH_V2_ITERATION:{iteration_id}")
        session_id = _text(context.get("session_id"))
        identity = (
            context.get("agent_id"), context.get("workstream_id"), context.get("objective_id"),
            context.get("claim_id"), context.get("fencing_token"), context.get("branch"), context.get("worktree"),
        )
        prior_identity = session_identity.get(session_id)
        if prior_identity is not None and prior_identity != identity:
            violations.append(f"SESSION_ID_REUSED_WITH_DIFFERENT_IDENTITY:{session_id}")
        elif session_id:
            session_identity[session_id] = identity
        else:
            violations.append(f"RECEIPT_WITHOUT_SESSION_ID:{iteration_id}")
        for node in receipt.get("graph_nodes", []):
            if isinstance(node, Mapping):
                add_node(node)
        for edge in receipt.get("graph_edges", []):
            if isinstance(edge, Mapping):
                add_edge(edge)
        add_node({"id": f"ITERATION:{iteration_id}", "type": "Experiment", "decision": receipt.get("decision")})
        hypothesis_id = f"HYPOTHESIS:{iteration_id}"
        add_node({"id": hypothesis_id, "type": "Hypothesis", "text": proposal.get("hypothesis", "")})
        add_edge({"from": f"ITERATION:{iteration_id}", "to": hypothesis_id, "type": "TESTS"})
        suites = proposal.get("evaluation_suite", [])
        if isinstance(suites, (list, tuple)):
            for suite in suites:
                evaluator_id = f"EVALUATOR:{suite}"
                add_node({"id": evaluator_id, "type": "TestSuite"})
                add_edge({"from": f"ITERATION:{iteration_id}", "to": evaluator_id, "type": "EVALUATED_BY"})

    latest_heartbeat: dict[str, Mapping[str, object]] = {}
    heartbeat_ids: set[str] = set()
    for heartbeat in heartbeats:
        heartbeat_id = _text(heartbeat.get("heartbeat_id"))
        if heartbeat_id in heartbeat_ids:
            violations.append(f"DUPLICATE_HEARTBEAT_ID:{heartbeat_id}")
        heartbeat_ids.add(heartbeat_id)
        violations.extend(f"{heartbeat_id}:{error}" for error in validate_heartbeat(heartbeat))
        session_id = _text(heartbeat.get("session_id"))
        if not session_id:
            continue
        prior = latest_heartbeat.get(session_id)
        if prior is None or _parse_time(_text(heartbeat.get("observed_at"))) > _parse_time(_text(prior.get("observed_at"))):
            latest_heartbeat[session_id] = heartbeat

        agent_id, workstream_id, objective_id = (_text(heartbeat.get(k)) for k in ("agent_id", "workstream_id", "objective_id"))
        plan_id, task_id, claim_id = (_text(heartbeat.get(k)) for k in ("plan_id", "task_id", "claim_id"))
        worktree, branch = _text(heartbeat.get("worktree")), _text(heartbeat.get("branch"))
        add_node({"id": f"PROJECT:{heartbeat.get('project_id')}", "type": "Project"})
        add_node({"id": f"AGENT:{agent_id}", "type": "Agent"})
        add_node({"id": f"SESSION:{session_id}", "type": "Session"})
        add_node({"id": f"WORKSTREAM:{workstream_id}", "type": "Workstream"})
        add_node({"id": f"OBJECTIVE:{objective_id}", "type": "Objective"})
        add_node({"id": f"PLAN:{plan_id}", "type": "Plan"})
        add_node({"id": f"TASK:{task_id}", "type": "Task"})
        add_node({"id": f"CLAIM:{claim_id}", "type": "Claim", "fencing_token": heartbeat.get("fencing_token")})
        add_node({"id": f"WORKTREE:{worktree}", "type": "Worktree"})
        add_node({"id": f"BRANCH:{branch}", "type": "Branch"})
        for goal_id in heartbeat.get("goal_ids", []) if isinstance(heartbeat.get("goal_ids"), list) else []:
            add_node({"id": f"GOAL:{goal_id}", "type": "Goal"})
            add_edge({"from": f"TASK:{task_id}", "to": f"GOAL:{goal_id}", "type": "CONTRIBUTES_TO"})
        pr_number = heartbeat.get("pr_number")
        if isinstance(pr_number, int) and not isinstance(pr_number, bool):
            add_node({"id": f"PR:{pr_number}", "type": "PullRequest"})
            add_edge({"from": f"BRANCH:{branch}", "to": f"PR:{pr_number}", "type": "PROPOSED_BY"})
        add_edge({"from": f"AGENT:{agent_id}", "to": f"SESSION:{session_id}", "type": "EXECUTES"})
        add_edge({"from": f"SESSION:{session_id}", "to": f"CLAIM:{claim_id}", "type": "OWNS"})
        add_edge({"from": f"CLAIM:{claim_id}", "to": f"TASK:{task_id}", "type": "CLAIMS"})
        add_edge({"from": f"PLAN:{plan_id}", "to": f"TASK:{task_id}", "type": "CONTAINS"})
        add_edge({"from": f"WORKTREE:{worktree}", "to": f"BRANCH:{branch}", "type": "CHECKS_OUT"})
        add_edge({"from": f"SESSION:{session_id}", "to": f"WORKTREE:{worktree}", "type": "OPERATES_IN"})
        node_id = f"HEARTBEAT:{heartbeat_id}"
        add_node({"id": node_id, "type": "Heartbeat", "state": heartbeat.get("state"), "observed_at": heartbeat.get("observed_at"), "next_safe_action": heartbeat.get("next_safe_action")})
        add_edge({"from": f"SESSION:{session_id}", "to": node_id, "type": "HEARTBEATS_WITH"})
        current_iteration = _text(heartbeat.get("current_iteration_id"))
        if current_iteration:
            add_node({"id": f"ITERATION:{current_iteration}", "type": "Experiment", "state": "IN_PROGRESS"})
            add_edge({"from": f"SESSION:{session_id}", "to": f"ITERATION:{current_iteration}", "type": "EXECUTES"})

    active_sessions: list[dict[str, object]] = []
    stale_sessions: list[dict[str, object]] = []
    scope_owners: dict[tuple[str, str, str], list[Mapping[str, object]]] = {}
    for session_id, heartbeat in latest_heartbeat.items():
        state = heartbeat.get("state")
        age_seconds = (now - _parse_time(_text(heartbeat.get("observed_at")))).total_seconds()
        if age_seconds < 0:
            violations.append(f"FUTURE_HEARTBEAT:{session_id}")
            continue
        entry = {
            "session_id": session_id, "agent_id": heartbeat.get("agent_id"), "claim_id": heartbeat.get("claim_id"),
            "fencing_token": heartbeat.get("fencing_token"), "task_id": heartbeat.get("task_id"), "branch": heartbeat.get("branch"),
            "worktree": heartbeat.get("worktree"), "observed_at": heartbeat.get("observed_at"), "age_seconds": int(age_seconds), "state": state,
            "next_safe_action": heartbeat.get("next_safe_action"),
        }
        if state in ACTIVE_HEARTBEAT_STATES and age_seconds > heartbeat_ttl_seconds:
            stale_sessions.append(entry)
            add_edge({"from": f"SESSION:{session_id}", "to": f"CLAIM:{heartbeat.get('claim_id')}", "type": "STALE_OWNER_OF"})
        elif state in ACTIVE_HEARTBEAT_STATES:
            active_sessions.append(entry)
            key = (_text(heartbeat.get("workstream_id")), _text(heartbeat.get("objective_id")), _text(heartbeat.get("task_id")))
            scope_owners.setdefault(key, []).append(heartbeat)

    for scope, owners in scope_owners.items():
        if len(owners) <= 1:
            continue
        max_token = max(int(owner["fencing_token"]) for owner in owners)
        leaders = [owner for owner in owners if int(owner["fencing_token"]) == max_token]
        if len(leaders) != 1:
            violations.append(f"ACTIVE_SCOPE_FENCING_TIE:{'|'.join(scope)}:{max_token}")
        for owner in owners:
            if int(owner["fencing_token"]) < max_token:
                violations.append(f"STALE_ACTIVE_WRITER:{owner['session_id']}:{owner['fencing_token']}<{max_token}")

    node_ids = set(nodes_by_id)
    for edge in edges_by_key.values():
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            violations.append(f"DANGLING_EDGE:{edge['from']}->{edge['to']}:{edge['type']}")

    graph = {
        "schema_version": "AGENT-RUNTIME-GRAPH-1.0", "as_of": as_of, "heartbeat_ttl_seconds": heartbeat_ttl_seconds,
        "iteration_count": len(iteration_ids), "heartbeat_count": len(heartbeat_ids),
        "active_sessions": sorted(active_sessions, key=lambda x: str(x["session_id"])),
        "stale_sessions": sorted(stale_sessions, key=lambda x: str(x["session_id"])),
        "nodes": sorted(nodes_by_id.values(), key=lambda x: str(x.get("id", ""))),
        "edges": sorted(edges_by_key.values(), key=canonical_json), "violations": sorted(set(violations)),
    }
    graph["projection_revision"] = sha256_json(graph)
    return graph


def assert_takeover_safe(graph: Mapping[str, object], *, predecessor_session_id: str, successor_session_id: str) -> None:
    stale = {item["session_id"]: item for item in graph.get("stale_sessions", []) if isinstance(item, Mapping)}
    active = {item["session_id"]: item for item in graph.get("active_sessions", []) if isinstance(item, Mapping)}
    if predecessor_session_id not in stale:
        raise ValueError("predecessor must be stale before takeover")
    if successor_session_id not in active:
        raise ValueError("successor must have a fresh active heartbeat")
    predecessor, successor = stale[predecessor_session_id], active[successor_session_id]
    if int(successor["fencing_token"]) <= int(predecessor["fencing_token"]):
        raise ValueError("successor fencing token must strictly exceed predecessor")
    if successor_session_id == predecessor_session_id:
        raise ValueError("successor must use a new session_id")

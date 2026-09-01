from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence

from .agent_improvement_runtime import AgentRunContext, GRAPH_PROGRAM

SCHEMA_VERSION = "COS-SRP-SESSION-RUNTIME-1.0"
REGISTRY_SCHEMA = "COS-SRP-RUNTIME-REGISTRY-1.0"
PROGRESS_SCHEMA = "COS-SRP-PROGRESS-STATE-1.0"
PROGRESS_STATES = frozenset({"PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED", "SKIPPED"})
TERMINAL_WORK_EVENTS = {"WORK_COMPLETED": "COMPLETED", "WORK_BLOCKED": "BLOCKED"}
ACTIVITY_EVENTS = frozenset({
    "HELLO", "WORK_STARTED", "WORK_PROGRESS", "HEARTBEAT", "CHECKPOINT_REACHED",
    "DECISION_RECORDED", "EVIDENCE_RECORDED", "CONTEXT_PACK_EMITTED",
    "WORK_BLOCKED", "WORK_COMPLETED",
})


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _latest(events: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    if not events:
        return None
    return sorted(events, key=lambda e: (_text(e.get("occurred_at")), _text(e.get("event_id"))))[-1]


def validate_runtime_locator(locator: Any) -> list[str]:
    if locator is None:
        return []
    if not isinstance(locator, Mapping):
        return ["RUNTIME_LOCATOR_NOT_OBJECT"]
    errors: list[str] = []
    if not _text(locator.get("provider")):
        errors.append("RUNTIME_PROVIDER_MISSING")
    chat_id = locator.get("chat_id")
    state = _text(locator.get("chat_id_state"))
    if chat_id is None:
        if state != "UNAVAILABLE_BY_HARNESS":
            errors.append("NULL_CHAT_ID_REQUIRES_UNAVAILABLE_BY_HARNESS")
    else:
        if not isinstance(chat_id, str) or not chat_id.strip():
            errors.append("CHAT_ID_INVALID")
        if state != "AVAILABLE":
            errors.append("PRESENT_CHAT_ID_REQUIRES_AVAILABLE_STATE")
    return errors


def validate_graph_runtime_identity(event: Mapping[str, Any], identity: Any) -> list[str]:
    if identity is None:
        return ["GRAPH_RUNTIME_IDENTITY_MISSING"] if event.get("runtime_identity_required") is True else []
    if not isinstance(identity, Mapping):
        return ["GRAPH_RUNTIME_IDENTITY_NOT_OBJECT"]
    errors: list[str] = []
    for key in ("plan_id", "task_id", "claim_id", "worktree", "branch", "base_main_sha", "authority_ceiling"):
        if not _text(identity.get(key)):
            errors.append(f"GRAPH_RUNTIME_{key.upper()}_MISSING")
    goals = identity.get("goal_ids")
    if not isinstance(goals, list) or not goals or not all(isinstance(x, str) and x.strip() for x in goals):
        errors.append("GRAPH_RUNTIME_GOAL_IDS_INVALID")
    token = identity.get("fencing_token")
    if isinstance(token, bool) or not isinstance(token, int) or token < 1:
        errors.append("GRAPH_RUNTIME_FENCING_TOKEN_INVALID")
    if identity.get("graph_program") != GRAPH_PROGRAM:
        errors.append("GRAPH_RUNTIME_PROGRAM_MISMATCH")
    base_sha = _text(identity.get("base_main_sha"))
    if base_sha and (len(base_sha) != 40 or any(c not in "0123456789abcdef" for c in base_sha)):
        errors.append("GRAPH_RUNTIME_BASE_MAIN_SHA_INVALID")
    event_branch = _text(event.get("branch"))
    if event_branch and _text(identity.get("branch")) and event_branch != _text(identity.get("branch")):
        errors.append("GRAPH_RUNTIME_BRANCH_DRIFT")
    if errors:
        return errors
    try:
        AgentRunContext(
            project_id=_text(event.get("project_id")),
            agent_id=_text(event.get("agent_id")),
            session_id=_text(event.get("session_id")),
            workstream_id=_text(event.get("workstream_id")),
            objective_id=_text(event.get("objective_id")),
            correlation_id=_text(event.get("correlation_id")),
            goal_ids=tuple(goals),
            plan_id=_text(identity.get("plan_id")),
            task_id=_text(identity.get("task_id")),
            claim_id=_text(identity.get("claim_id")),
            fencing_token=int(token),
            branch=_text(identity.get("branch")),
            worktree=_text(identity.get("worktree")),
            base_main_sha=base_sha,
            authority_ceiling=_text(identity.get("authority_ceiling")),
            graph_program=str(identity.get("graph_program")),
            pr_number=identity.get("pr_number") if isinstance(identity.get("pr_number"), int) else None,
        ).validate()
    except ValueError as exc:
        errors.append(f"GRAPH_RUNTIME_AGENT_CONTEXT_INVALID:{exc}")
    return errors


def validate_progress_snapshot(snapshot: Any) -> list[str]:
    if snapshot is None:
        return []
    if not isinstance(snapshot, Mapping):
        return ["PROGRESS_SNAPSHOT_NOT_OBJECT"]
    errors: list[str] = []
    if "percent" in snapshot or "progress_percent" in snapshot:
        errors.append("ARBITRARY_PROGRESS_PERCENT_FORBIDDEN")
    if not _text(snapshot.get("plan_revision")):
        errors.append("PLAN_REVISION_MISSING")
    items = snapshot.get("items")
    if not isinstance(items, list) or not items:
        errors.append("PROGRESS_ITEMS_MISSING")
        return errors
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, Mapping):
            errors.append("PROGRESS_ITEM_NOT_OBJECT")
            continue
        item_id = _text(item.get("item_id"))
        if not item_id:
            errors.append("PROGRESS_ITEM_ID_MISSING")
            continue
        if item_id in seen:
            errors.append(f"PROGRESS_ITEM_DUPLICATE:{item_id}")
        seen.add(item_id)
        if _text(item.get("state")) not in PROGRESS_STATES:
            errors.append(f"PROGRESS_ITEM_STATE_INVALID:{item_id}")
        weight = item.get("weight", 1)
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight <= 0:
            errors.append(f"PROGRESS_ITEM_WEIGHT_INVALID:{item_id}")
    return errors


def derive_progress(snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    if snapshot is None:
        return {
            "schema_version": PROGRESS_SCHEMA,
            "state": "UNKNOWN_LEGACY_OR_UNREPORTED",
            "plan_revision": None,
            "completion_percent": None,
            "counts": {},
            "items": [],
        }
    errors = validate_progress_snapshot(snapshot)
    if errors:
        raise ValueError("invalid progress snapshot: " + ",".join(errors))
    items = [dict(item) for item in snapshot["items"]]
    total = sum(float(item.get("weight", 1)) for item in items)
    completed = sum(
        float(item.get("weight", 1)) for item in items
        if item.get("state") in {"COMPLETED", "SKIPPED"}
    )
    return {
        "schema_version": PROGRESS_SCHEMA,
        "state": "REPORTED",
        "plan_revision": snapshot["plan_revision"],
        "completion_percent": round(100.0 * completed / total, 1) if total else 0.0,
        "completed_weight": completed,
        "total_weight": total,
        "counts": {state: sum(item.get("state") == state for item in items) for state in sorted(PROGRESS_STATES)},
        "items": items,
    }


def _claim_summary(session_id: str, claims: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [claim for claim in claims if _text(claim.get("session_id")) == session_id]
    active = [claim for claim in rows if claim.get("state") == "ACTIVE"]
    tokens = sorted(claim.get("fencing_token") for claim in rows if isinstance(claim.get("fencing_token"), int))
    return {
        "claim_ids": sorted(_text(claim.get("claim_id")) for claim in rows if _text(claim.get("claim_id"))),
        "active_claim_ids": sorted(_text(claim.get("claim_id")) for claim in active if _text(claim.get("claim_id"))),
        "fencing_tokens": tokens,
        "max_fencing_token": max(tokens) if tokens else None,
    }


def derive_session_runtime(
    events: Sequence[Mapping[str, Any]],
    claims: Sequence[Mapping[str, Any]],
    *,
    observed_at: str,
    stale_after_seconds: int = 3600,
    orphan_after_seconds: int = 14400,
) -> dict[str, Any]:
    if not events:
        raise ValueError("session requires at least one event")
    session_ids = {_text(event.get("session_id")) for event in events}
    if len(session_ids) != 1 or "" in session_ids:
        raise ValueError("events must belong to exactly one non-empty session")
    session_id = next(iter(session_ids))
    ordered = sorted(events, key=lambda event: (_text(event.get("occurred_at")), _text(event.get("event_id"))))
    first, last = ordered[0], ordered[-1]
    violations: list[str] = []
    agent_ids = {_text(e.get("agent_id")) for e in ordered if _text(e.get("agent_id"))}
    workstreams = {_text(e.get("workstream_id")) for e in ordered if _text(e.get("workstream_id"))}
    objectives = {_text(e.get("objective_id")) for e in ordered if _text(e.get("objective_id"))}
    if len(agent_ids) != 1:
        violations.append("SESSION_AGENT_ID_DRIFT")
    if len(workstreams) != 1:
        violations.append("SESSION_WORKSTREAM_DRIFT")
    if len(objectives) != 1:
        violations.append("SESSION_OBJECTIVE_DRIFT")

    terminal = [e for e in ordered if _text(e.get("event_type")) in TERMINAL_WORK_EVENTS]
    lifecycle_state = TERMINAL_WORK_EVENTS[_text(terminal[-1].get("event_type"))] if terminal else "ACTIVE"
    claims_state = _claim_summary(session_id, claims)
    if lifecycle_state == "ACTIVE" and claims_state["active_claim_ids"]:
        lifecycle_detail = "ACTIVE_CLAIM_HELD"
    elif lifecycle_state == "ACTIVE" and claims_state["claim_ids"]:
        lifecycle_detail = "CLAIM_RELEASED_BUT_WORK_NOT_TERMINAL"
    elif lifecycle_state == "ACTIVE":
        lifecycle_detail = "ACTIVE_WITHOUT_CLAIM_OR_READ_ONLY_WORK"
    else:
        lifecycle_detail = lifecycle_state

    progress_events = [e for e in ordered if e.get("progress_snapshot") is not None]
    progress_event = _latest(progress_events)
    progress = derive_progress(progress_event.get("progress_snapshot") if progress_event else None)
    native_srp = bool(progress_events or any(e.get("runtime_identity_required") is True for e in ordered))

    identity_events = [e for e in ordered if e.get("runtime_identity") is not None or e.get("runtime_identity_required") is True]
    identity_event = _latest(identity_events)
    identity = identity_event.get("runtime_identity") if identity_event else None
    if identity_event:
        violations.extend(validate_graph_runtime_identity(identity_event, identity))

    locators = [e.get("runtime_locator") for e in ordered if e.get("runtime_locator") is not None]
    locator = locators[-1] if locators else {
        "provider": "UNKNOWN_LEGACY",
        "chat_id": None,
        "chat_id_state": "UNAVAILABLE_BY_HARNESS",
    }
    violations.extend(validate_runtime_locator(locator))

    heartbeats = [e for e in ordered if _text(e.get("event_type")) == "HEARTBEAT"]
    last_heartbeat = heartbeats[-1] if heartbeats else None
    activity = [e for e in ordered if _text(e.get("event_type")) in ACTIVITY_EVENTS]
    last_activity = activity[-1] if activity else last
    now_dt, activity_dt = _dt(observed_at), _dt(_text(last_activity.get("occurred_at")))
    age = max(0.0, (now_dt - activity_dt).total_seconds()) if now_dt and activity_dt else None

    if lifecycle_state in {"COMPLETED", "BLOCKED"}:
        liveness = "TERMINAL"
        liveness_evidence = "WORK_TERMINAL_EVENT"
    elif not native_srp and not claims_state["active_claim_ids"]:
        liveness = "LEGACY_UNKNOWN"
        liveness_evidence = "PRE_SRP_INCOMPLETE_HISTORY"
    elif age is None:
        liveness = "UNKNOWN"
        liveness_evidence = "NO_PARSEABLE_ACTIVITY_TIME"
    elif age <= stale_after_seconds:
        liveness = "LIVE"
        liveness_evidence = "HEARTBEAT" if last_heartbeat else "RECENT_ACTIVITY_FALLBACK"
    elif age <= orphan_after_seconds:
        liveness = "STALE"
        liveness_evidence = "HEARTBEAT_OR_ACTIVITY_TTL"
    else:
        liveness = "ORPHANED_CANDIDATE"
        liveness_evidence = "HEARTBEAT_OR_ACTIVITY_TTL"
    if native_srp and lifecycle_state == "ACTIVE" and not last_heartbeat:
        violations.append("SRP_HEARTBEAT_MISSING")

    blockers: list[str] = []
    recovery_inputs: list[str] = []
    for event in ordered:
        if isinstance(event.get("blockers"), list):
            blockers.extend(str(x) for x in event["blockers"] if str(x).strip())
        if isinstance(event.get("recovery_inputs"), list):
            recovery_inputs.extend(str(x) for x in event["recovery_inputs"] if str(x).strip())

    runtime = {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "agent_id": next(iter(agent_ids), ""),
        "workstream_id": next(iter(workstreams), ""),
        "objective_id": next(iter(objectives), ""),
        "srp_contract_state": "NATIVE_SRP" if native_srp else "LEGACY_OR_PRE_SRP",
        "lifecycle_state": lifecycle_state,
        "lifecycle_detail": lifecycle_detail,
        "liveness": liveness,
        "liveness_evidence": liveness_evidence,
        "observed_at": observed_at,
        "started_at": _text(first.get("occurred_at")),
        "last_event_at": _text(last.get("occurred_at")),
        "last_event_id": _text(last.get("event_id")),
        "last_heartbeat_at": _text(last_heartbeat.get("occurred_at")) if last_heartbeat else None,
        "last_activity_age_seconds": age,
        "runtime_locator": dict(locator) if isinstance(locator, Mapping) else locator,
        "graph_runtime_identity_state": "REPORTED" if isinstance(identity, Mapping) else "UNREPORTED_LEGACY_OR_PREACTIVATION",
        "graph_runtime_identity": dict(identity) if isinstance(identity, Mapping) else None,
        "progress": progress,
        "claims": claims_state,
        "branch": _text(last.get("branch")) or _text(first.get("branch")) or None,
        "pr": last.get("pr") if last.get("pr") is not None else first.get("pr"),
        "main_sha_observed": _text(last.get("main_sha_observed")),
        "base_sha": _text(first.get("base_sha")),
        "next_action": _text(last.get("next_action")) or None,
        "blockers": sorted(set(blockers)),
        "recovery_inputs": sorted(set(recovery_inputs)),
        "event_ids": [_text(e.get("event_id")) for e in ordered],
        "violations": sorted(set(violations)),
    }
    runtime["runtime_revision"] = sha256_json(runtime)
    return runtime


def build_registry(
    sessions: Sequence[Mapping[str, Any]],
    *,
    observed_at: str,
    unmerged_proposals: Sequence[Mapping[str, Any]] = (),
    live_leases: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    session_rows = sorted((dict(row) for row in sessions), key=lambda row: str(row.get("session_id")))
    proposals = sorted((dict(row) for row in unmerged_proposals), key=lambda row: (str(row.get("session_id")), str(row.get("pr_number"))))
    leases = sorted((dict(row) for row in live_leases), key=lambda row: str(row.get("session_id")))
    registry = {
        "schema_version": REGISTRY_SCHEMA,
        "observed_at": observed_at,
        "authority_contract": "GIT_EVENT_CLAIM_FENCING_IS_OWNERSHIP_AUTHORITY; LIVE_LEASES_AND_PR_OBSERVATIONS_ARE_OBSERVABILITY_ONLY",
        "sessions": session_rows,
        "unmerged_proposals": proposals,
        "live_leases": leases,
        "summary": {
            "session_count": len(session_rows),
            "live": sum(row.get("liveness") == "LIVE" for row in session_rows),
            "stale": sum(row.get("liveness") == "STALE" for row in session_rows),
            "orphaned_candidate": sum(row.get("liveness") == "ORPHANED_CANDIDATE" for row in session_rows),
            "terminal": sum(row.get("liveness") == "TERMINAL" for row in session_rows),
            "legacy_unknown": sum(row.get("liveness") == "LEGACY_UNKNOWN" for row in session_rows),
            "claim_released_work_not_terminal": sum(row.get("lifecycle_detail") == "CLAIM_RELEASED_BUT_WORK_NOT_TERMINAL" for row in session_rows),
            "unmerged_proposal_count": len(proposals),
            "live_lease_count": len(leases),
        },
    }
    registry["registry_revision"] = sha256_json(registry)
    return registry

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence

EVENT_SCHEMA = "COS-V2-EVENT-1.0"
CLAIM_SCHEMA = "COS-V2-CLAIM-1.0"
CONTEXT_SCHEMA = "COS-V2-CONTEXT-PACK-1.1"
PROJECT_STATE_SCHEMA = "COS-V2-PROJECT-STATE-1.0"
ACTIVE_CLAIM_STATES = frozenset({"ACTIVE"})
TERMINAL_CLAIM_STATES = frozenset({"RELEASED", "SUPERSEDED", "EXPIRED"})
CLAIM_EVENT_TO_STATE = {
    "CLAIM_ACQUIRED": "ACTIVE",
    "CLAIM_RELEASED": "RELEASED",
    "CLAIM_SUPERSEDED": "SUPERSEDED",
}
CLAIM_EVENT_TIMESTAMP_FIELD = {
    "CLAIM_ACQUIRED": "claimed_at",
    "CLAIM_RELEASED": "released_at",
    "CLAIM_SUPERSEDED": "superseded_at",
}
KNOWN_EVENT_TYPES = frozenset(
    {
        "HELLO",
        "WORK_STARTED",
        "WORK_PROGRESS",
        "WORK_BLOCKED",
        "WORK_COMPLETED",
        "CLAIM_ACQUIRED",
        "CLAIM_RELEASED",
        "CLAIM_SUPERSEDED",
        "CHECKPOINT_REACHED",
        "DECISION_RECORDED",
        "EVIDENCE_RECORDED",
        "CONTEXT_PACK_EMITTED",
        "HEARTBEAT",
    }
)


class CoordinationError(ValueError):
    pass


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def _text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    return value.strip() if isinstance(value, str) else ""


def _require_text(payload, key, errors):
    value = _text(payload, key)
    if not value:
        errors.append(f"MISSING_{key.upper()}")
    return value


def _is_git_sha(value: str) -> bool:
    return len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def validate_event(event):
    errors = []
    if event.get("schema_version") != EVENT_SCHEMA:
        errors.append("INVALID_EVENT_SCHEMA")
    for key in (
        "event_id", "event_type", "occurred_at", "project_id", "agent_id",
        "session_id", "workstream_id", "objective_id", "correlation_id", "repo",
        "main_sha_observed", "base_sha", "authority_ceiling", "summary",
        "next_action", "idempotency_key",
    ):
        _require_text(event, key, errors)
    event_type = _text(event, "event_type")
    if event_type and event_type not in KNOWN_EVENT_TYPES:
        errors.append("UNKNOWN_EVENT_TYPE")
    for key in ("main_sha_observed", "base_sha"):
        value = _text(event, key)
        if value and not _is_git_sha(value):
            errors.append(f"INVALID_{key.upper()}")
    for key in ("canonical_hotel_mutation_allowed", "h_id_allocation_allowed", "outbound_allowed"):
        if not isinstance(event.get(key), bool):
            errors.append(f"INVALID_{key.upper()}_BOOLEAN")
    return tuple(dict.fromkeys(errors))


def validate_claim(claim):
    errors = []
    if claim.get("schema_version") != CLAIM_SCHEMA:
        errors.append("INVALID_CLAIM_SCHEMA")
    for key in (
        "claim_id", "project_id", "agent_id", "session_id", "workstream_id",
        "objective_id", "correlation_id", "state", "claimed_at", "base_sha",
        "branch", "authority_ceiling", "idempotency_key",
    ):
        _require_text(claim, key, errors)
    value = _text(claim, "base_sha")
    if value and not _is_git_sha(value):
        errors.append("INVALID_BASE_SHA")
    token = claim.get("fencing_token")
    if isinstance(token, bool) or not isinstance(token, int) or token < 1:
        errors.append("INVALID_FENCING_TOKEN")
    for key in ("resource_scopes", "semantic_scopes", "excluded_scopes"):
        value = claim.get(key)
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            errors.append(f"INVALID_{key.upper()}")
    return tuple(dict.fromkeys(errors))


def scopes_overlap(left: Sequence[str], right: Sequence[str]) -> bool:
    return bool({x.strip() for x in left if isinstance(x, str) and x.strip()} & {x.strip() for x in right if isinstance(x, str) and x.strip()})


def detect_claim_collisions(claims):
    active = [c for c in claims if c.get("state") in ACTIVE_CLAIM_STATES]
    output = []
    for index, left in enumerate(active):
        for right in active[index + 1:]:
            if _text(left, "project_id") != _text(right, "project_id"):
                continue
            resource_overlap = scopes_overlap(
                left.get("resource_scopes", []) if isinstance(left.get("resource_scopes"), list) else [],
                right.get("resource_scopes", []) if isinstance(right.get("resource_scopes"), list) else [],
            )
            semantic_overlap = scopes_overlap(
                left.get("semantic_scopes", []) if isinstance(left.get("semantic_scopes"), list) else [],
                right.get("semantic_scopes", []) if isinstance(right.get("semantic_scopes"), list) else [],
            )
            if resource_overlap or semantic_overlap:
                output.append({
                    "left_claim_id": _text(left, "claim_id"),
                    "right_claim_id": _text(right, "claim_id"),
                    "resource_overlap": resource_overlap,
                    "semantic_overlap": semantic_overlap,
                })
    return output


def _causation_claim_ids(event: Mapping[str, object]) -> list[str]:
    value = event.get("causation")
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [item.split(":", 1)[1] for item in value if isinstance(item, str) and item.startswith("claim:") and len(item) > 6]


def _scope_set(payload: Mapping[str, object], key: str) -> set[str]:
    value = payload.get(key)
    if not isinstance(value, list):
        return set()
    return {item.strip() for item in value if isinstance(item, str) and item.strip()}


def _legacy_claim_candidates(event, claims):
    """Resolve pre-causation lifecycle records from durable evidence, fail closed on ties.

    Order of evidence strength:
    1. exact lifecycle timestamp (claimed_at/released_at/superseded_at),
    2. exact branch,
    3. exact session identity,
    4. highest fencing token among temporally and semantically compatible claims.

    The final fallback is only accepted when the highest fencing token is unique.
    """
    occurred_at = _text(event, "occurred_at")
    event_scopes = _scope_set(event, "semantic_scopes")
    candidates = []
    for claim in claims:
        if _text(claim, "project_id") != _text(event, "project_id"):
            continue
        if _text(claim, "workstream_id") != _text(event, "workstream_id"):
            continue
        if _text(claim, "objective_id") != _text(event, "objective_id"):
            continue
        claimed_at = _text(claim, "claimed_at")
        if occurred_at and claimed_at and claimed_at > occurred_at:
            continue
        claim_scopes = _scope_set(claim, "semantic_scopes")
        if event_scopes and not event_scopes.issubset(claim_scopes):
            continue
        candidates.append(claim)

    timestamp_field = CLAIM_EVENT_TIMESTAMP_FIELD.get(_text(event, "event_type"))
    if timestamp_field and occurred_at:
        exact = [claim for claim in candidates if _text(claim, timestamp_field) == occurred_at]
        if len(exact) == 1:
            return exact, "LEGACY_LIFECYCLE_TIMESTAMP"
        if len(exact) > 1:
            return exact, "LEGACY_LIFECYCLE_TIMESTAMP_AMBIGUOUS"

    branch = _text(event, "branch")
    if branch:
        exact = [claim for claim in candidates if _text(claim, "branch") == branch]
        if len(exact) == 1:
            return exact, "LEGACY_BRANCH_IDENTITY"
        if len(exact) > 1:
            return exact, "LEGACY_BRANCH_IDENTITY_AMBIGUOUS"

    session_id = _text(event, "session_id")
    if session_id:
        exact = [claim for claim in candidates if _text(claim, "session_id") == session_id]
        if len(exact) == 1:
            return exact, "LEGACY_SESSION_IDENTITY"
        if len(exact) > 1:
            return exact, "LEGACY_SESSION_IDENTITY_AMBIGUOUS"

    tokens = [claim.get("fencing_token") for claim in candidates if isinstance(claim.get("fencing_token"), int) and not isinstance(claim.get("fencing_token"), bool)]
    if tokens:
        high = max(tokens)
        highest = [claim for claim in candidates if claim.get("fencing_token") == high]
        if len(highest) == 1:
            return highest, "LEGACY_HIGHEST_FENCING_TOKEN"
        if len(highest) > 1:
            return highest, "LEGACY_HIGHEST_FENCING_TOKEN_AMBIGUOUS"

    return candidates, "LEGACY_UNIQUE_SEMANTIC"


def derive_claim_lifecycle(events, claims):
    """Replay lifecycle events and use claim-file state only as the final assertion."""
    claims = list(claims)
    by_id = {_text(claim, "claim_id"): claim for claim in claims if _text(claim, "claim_id")}
    states: dict[str, str] = {}
    seen_claims: set[str] = set()
    bindings = []
    errors = []

    ordered_events = sorted(list(events), key=lambda event: (_text(event, "occurred_at"), _text(event, "event_id")))
    for event in ordered_events:
        event_type = _text(event, "event_type")
        target_state = CLAIM_EVENT_TO_STATE.get(event_type)
        if target_state is None:
            continue

        explicit_ids = _causation_claim_ids(event)
        if len(explicit_ids) > 1:
            errors.append(f"AMBIGUOUS_CLAIM_CAUSATION:{_text(event, 'event_id')}")
            continue
        if explicit_ids:
            claim_id = explicit_ids[0]
            if claim_id not in by_id:
                errors.append(f"UNKNOWN_CLAIM_CAUSATION:{_text(event, 'event_id')}:{claim_id}")
                continue
            binding_mode = "EXPLICIT_CAUSATION"
        else:
            candidates, binding_mode = _legacy_claim_candidates(event, claims)
            if len(candidates) != 1:
                errors.append(f"UNBOUND_CLAIM_LIFECYCLE_EVENT:{_text(event, 'event_id')}:{len(candidates)}")
                continue
            claim_id = _text(candidates[0], "claim_id")

        previous_state = states.get(claim_id, "UNSEEN")
        if event_type == "CLAIM_ACQUIRED":
            if previous_state in TERMINAL_CLAIM_STATES:
                errors.append(f"INVALID_CLAIM_REACTIVATION:{claim_id}:{previous_state}->{target_state}")
                continue
            if previous_state not in ("UNSEEN", "ACTIVE"):
                errors.append(f"INVALID_CLAIM_TRANSITION:{claim_id}:{previous_state}->{target_state}")
                continue
        elif event_type in ("CLAIM_RELEASED", "CLAIM_SUPERSEDED"):
            if previous_state not in ("UNSEEN", "ACTIVE", target_state):
                errors.append(f"INVALID_CLAIM_TRANSITION:{claim_id}:{previous_state}->{target_state}")
                continue

        states[claim_id] = target_state
        seen_claims.add(claim_id)
        bindings.append({
            "event_id": _text(event, "event_id"),
            "claim_id": claim_id,
            "event_type": event_type,
            "state": target_state,
            "binding_mode": binding_mode,
        })

    for claim_id, claim in by_id.items():
        declared = _text(claim, "state")
        if claim_id not in seen_claims:
            states[claim_id] = declared
            continue
        effective = states[claim_id]
        if declared != effective:
            errors.append(f"CLAIM_STATE_DRIFT:{claim_id}:{declared}!={effective}")

    return states, bindings, sorted(set(errors))


def reduce_coordination(events, claims):
    events = list(events)
    claims = list(claims)
    errors = []
    event_ids = set()
    idempotency = {}
    sessions = {}

    for event in events:
        errors.extend(f"{_text(event, 'event_id') or '<unknown>'}:{error}" for error in validate_event(event))
        event_id = _text(event, "event_id")
        if event_id:
            if event_id in event_ids:
                errors.append(f"DUPLICATE_EVENT_ID:{event_id}")
            event_ids.add(event_id)
        idempotency_key = _text(event, "idempotency_key")
        if idempotency_key:
            prior = idempotency.get(idempotency_key)
            if prior and prior != event_id:
                errors.append(f"DUPLICATE_IDEMPOTENCY_KEY:{idempotency_key}")
            idempotency[idempotency_key] = event_id
        session_id = _text(event, "session_id")
        if session_id:
            session = sessions.setdefault(session_id, {
                "session_id": session_id,
                "agent_id": _text(event, "agent_id"),
                "workstream_id": _text(event, "workstream_id"),
                "objective_id": _text(event, "objective_id"),
                "state": "ACTIVE",
                "event_ids": [],
            })
            session["event_ids"].append(event_id)
            if _text(event, "event_type") == "WORK_COMPLETED":
                session["state"] = "COMPLETED"
            elif _text(event, "event_type") == "WORK_BLOCKED":
                session["state"] = "BLOCKED"

    for claim in claims:
        errors.extend(f"{_text(claim, 'claim_id') or '<unknown>'}:{error}" for error in validate_claim(claim))

    claim_states, claim_lifecycle, lifecycle_errors = derive_claim_lifecycle(events, claims)
    errors.extend(lifecycle_errors)
    effective_claims = []
    for claim in claims:
        effective = dict(claim)
        claim_id = _text(claim, "claim_id")
        if claim_id in claim_states:
            effective["state"] = claim_states[claim_id]
        effective_claims.append(effective)

    watermark = None
    if events:
        ordered = sorted((_text(event, "occurred_at"), _text(event, "event_id")) for event in events)
        watermark = {"occurred_at": ordered[-1][0], "event_id": ordered[-1][1]}

    projection = {
        "schema_version": "COS-V2-COORDINATION-PROJECTION-1.1",
        "events_count": len(events),
        "claims_count": len(claims),
        "sessions": sorted(sessions.values(), key=lambda item: item["session_id"]),
        "claim_states": dict(sorted(claim_states.items())),
        "claim_lifecycle": claim_lifecycle,
        "active_claim_ids": sorted(_text(claim, "claim_id") for claim in effective_claims if claim.get("state") in ACTIVE_CLAIM_STATES),
        "claim_collisions": detect_claim_collisions(effective_claims),
        "event_watermark": watermark,
        "violations": sorted(set(errors)),
    }
    projection["projection_revision"] = sha256_json(projection)
    return projection


def build_context_pack(*, project_id, base_main_sha, authority_revision, projection, state_refs, relevant_paths, relevant_scope_revision, blockers, next_safe_actions):
    if not _is_git_sha(base_main_sha):
        raise CoordinationError("base_main_sha must be lowercase 40-hex Git object ID")
    if not _is_sha256(relevant_scope_revision):
        raise CoordinationError("relevant_scope_revision must be lowercase sha256")
    if not project_id.strip():
        raise CoordinationError("project_id required")
    if not isinstance(relevant_paths, list) or not relevant_paths or not all(isinstance(item, str) and item.strip() for item in relevant_paths):
        raise CoordinationError("relevant_paths required")
    pack = {
        "schema_version": CONTEXT_SCHEMA,
        "project_id": project_id,
        "base_main_sha": base_main_sha,
        "authority_revision": authority_revision,
        "projection_revision": projection.get("projection_revision"),
        "event_watermark": projection.get("event_watermark"),
        "state_refs": list(state_refs),
        "relevant_paths": list(relevant_paths),
        "relevant_scope_revision": relevant_scope_revision,
        "active_claim_ids": list(projection.get("active_claim_ids", [])),
        "blockers": list(blockers),
        "next_safe_actions": list(next_safe_actions),
    }
    pack["context_pack_revision"] = sha256_json(pack)
    return pack


def validate_context_pack(pack, *, base_is_ancestor, current_projection_revision, current_relevant_scope_revision, current_authority_revision=None):
    errors = []
    if pack.get("schema_version") != CONTEXT_SCHEMA:
        errors.append("INVALID_CONTEXT_SCHEMA")
    base = _text(pack, "base_main_sha")
    if base and not _is_git_sha(base):
        errors.append("INVALID_BASE_MAIN_SHA")
    paths = pack.get("relevant_paths")
    if not isinstance(paths, list) or not paths or not all(isinstance(item, str) and item.strip() for item in paths):
        errors.append("INVALID_RELEVANT_PATHS")
    if not _is_sha256(_text(pack, "relevant_scope_revision")):
        errors.append("INVALID_RELEVANT_SCOPE_REVISION")
    if base_is_ancestor is not True:
        errors.append("BASE_NOT_ANCESTOR")
    if pack.get("projection_revision") != current_projection_revision:
        errors.append("STALE_PROJECTION_REVISION")
    if pack.get("relevant_scope_revision") != current_relevant_scope_revision:
        errors.append("RELEVANT_SCOPE_DRIFT")
    if current_authority_revision is not None and pack.get("authority_revision") != current_authority_revision:
        errors.append("STALE_AUTHORITY_REVISION")
    if pack.get("context_pack_revision") != sha256_json({key: value for key, value in pack.items() if key != "context_pack_revision"}):
        errors.append("CONTEXT_PACK_HASH_MISMATCH")
    return tuple(errors)


def validate_project_state(payload):
    errors = []
    if payload.get("schema_version") != PROJECT_STATE_SCHEMA:
        errors.append("INVALID_PROJECT_STATE_SCHEMA")
    for key in ("project_id", "repo", "main_sha_observed", "authority_epoch", "authority_revision", "state", "current_objective_id"):
        _require_text(payload, key, errors)
    value = _text(payload, "main_sha_observed")
    if value and not _is_git_sha(value):
        errors.append("INVALID_MAIN_SHA")
    for key in ("authority_advanced", "h_id_allocation_allowed", "outbound_allowed"):
        if not isinstance(payload.get(key), bool):
            errors.append(f"INVALID_{key.upper()}_BOOLEAN")
    if payload.get("outbound_allowed") is True:
        errors.append("V2_ARCHITECTURE_STATE_MUST_NOT_OPEN_OUTBOUND")
    return tuple(dict.fromkeys(errors))


def death_drill(snapshot):
    required = {
        "north_star_ref", "current_objective_id", "main_sha_observed", "event_watermark",
        "projection_revision", "active_claim_ids", "open_prs", "verified_work",
        "unverified_work", "blockers", "risks", "next_safe_actions", "authority_revision",
    }
    return tuple(sorted(key for key in required if key not in snapshot or snapshot.get(key) in (None, "")))
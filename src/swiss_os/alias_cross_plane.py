from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence

_HOTEL_ID_RE = re.compile(r"^H-\d{4}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA = "ASR_CROSS_PLANE_WRITESET_V1"
_REQUIRED_PLANES = {
    "constrained_db",
    "HOTELS_V2",
    "HOTEL_INTELLIGENCE_V1",
    "GRAPH_NODES_V2",
    "GRAPH_EDGES_V2",
    "ENTITY_RESOLUTION",
    "STATE_TRANSITIONS",
    "observability_and_scheduler",
}


@dataclass(frozen=True)
class CrossPlaneViolation:
    code: str
    path: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "detail": self.detail}


@dataclass(frozen=True)
class CrossPlaneResult:
    state: str
    entities: int
    violations: tuple[CrossPlaneViolation, ...]

    @property
    def valid(self) -> bool:
        return self.state == "EXACT" and not self.violations

    def as_dict(self) -> dict[str, object]:
        return {
            "cross_plane_write_set_state": self.state,
            "cross_plane_write_set_valid": self.valid,
            "entities": self.entities,
            "violations": [item.as_dict() for item in self.violations],
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }


def _mapping(value: object, path: str, errors: list[CrossPlaneViolation]) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        errors.append(CrossPlaneViolation("TYPE_MISMATCH", path, "expected object"))
        return {}
    return value


def _list(value: object, path: str, errors: list[CrossPlaneViolation]) -> list[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        errors.append(CrossPlaneViolation("TYPE_MISMATCH", path, "expected array"))
        return []
    return list(value)


def _id(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _require_false(value: object, path: str, errors: list[CrossPlaneViolation]) -> None:
    if value is not False:
        errors.append(CrossPlaneViolation("PREAUTHORIZATION_FORBIDDEN", path, "must be boolean false"))


def _require_zero(value: object, path: str, errors: list[CrossPlaneViolation]) -> None:
    if type(value) is not int or value != 0:
        errors.append(CrossPlaneViolation("NONZERO_IRREVERSIBLE_PERMISSION", path, "must be integer 0"))


def _single_mutation_keys(
    plane: Mapping[str, object],
    path: str,
    errors: list[CrossPlaneViolation],
) -> set[str]:
    mutations = _list(plane.get("mutations"), f"{path}.mutations", errors)
    if len(mutations) != 1:
        errors.append(CrossPlaneViolation("MUTATION_CARDINALITY", f"{path}.mutations", "expected exactly one mutation group"))
        return set()
    row = _mapping(mutations[0], f"{path}.mutations[0]", errors)
    keys = _list(row.get("keys"), f"{path}.mutations[0].keys", errors)
    materialized = {str(item) for item in keys if isinstance(item, str) and item}
    if len(materialized) != len(keys):
        errors.append(CrossPlaneViolation("INVALID_OR_DUPLICATE_KEYS", f"{path}.mutations[0].keys", "keys must be unique non-empty strings"))
    return materialized


def validate_cross_plane_write_set(payload: Mapping[str, object]) -> CrossPlaneResult:
    """Validate a fail-closed issue-89 style cross-plane recovery plan.

    The function is read-only. An EXACT result proves plan completeness only; it
    never authorizes a live write or a post-repair denominator.
    """

    if not isinstance(payload, Mapping):
        raise ValueError("cross-plane write set must be a JSON object")

    errors: list[CrossPlaneViolation] = []
    if payload.get("schema_version") != _SCHEMA:
        errors.append(CrossPlaneViolation("SCHEMA_MISMATCH", "schema_version", f"expected {_SCHEMA}"))
    _require_false(payload.get("execution_authorized"), "execution_authorized", errors)
    _require_false(payload.get("authority_advance_allowed"), "authority_advance_allowed", errors)
    _require_false(payload.get("canonical_id_allocation_allowed"), "canonical_id_allocation_allowed", errors)
    _require_false(payload.get("crm_universe_complete"), "crm_universe_complete", errors)
    _require_false(payload.get("outbound_allowed"), "outbound_allowed", errors)
    _require_zero(payload.get("send_allowed"), "send_allowed", errors)

    resolution_rule = payload.get("resolution_rule")
    if not isinstance(resolution_rule, str) or "stable PK" not in resolution_rule or "row numbers" not in resolution_rule:
        errors.append(CrossPlaneViolation("PK_RESOLUTION_RULE_REQUIRED", "resolution_rule", "must forbid authoritative row-offset writes"))

    revision = payload.get("observed_spreadsheet_revision")
    rollback_copy = payload.get("rollback_copy_id")
    if not isinstance(revision, str) or not revision.strip():
        errors.append(CrossPlaneViolation("SPREADSHEET_REVISION_REQUIRED", "observed_spreadsheet_revision", "missing"))
    if not isinstance(rollback_copy, str) or not rollback_copy.strip():
        errors.append(CrossPlaneViolation("ROLLBACK_COPY_REQUIRED", "rollback_copy_id", "missing"))

    entities_raw = _list(payload.get("entities"), "entities", errors)
    entities: dict[str, Mapping[str, object]] = {}
    targets: dict[str, str] = {}
    for index, raw in enumerate(entities_raw):
        row = _mapping(raw, f"entities[{index}]", errors)
        hotel_id = _id(row.get("hotel_id"))
        target = _id(row.get("invalid_target"))
        path = f"entities[{index}]"
        if not _HOTEL_ID_RE.fullmatch(hotel_id) or not _HOTEL_ID_RE.fullmatch(target):
            errors.append(CrossPlaneViolation("INVALID_HOTEL_ID", path, f"{hotel_id!r}→{target!r}"))
            continue
        if hotel_id == target:
            errors.append(CrossPlaneViolation("SELF_ALIAS", path, hotel_id))
        if hotel_id in entities:
            errors.append(CrossPlaneViolation("DUPLICATE_ENTITY", f"{path}.hotel_id", hotel_id))
            continue
        for field in ("hotel_name", "city"):
            if not isinstance(row.get(field), str) or not str(row.get(field)).strip():
                errors.append(CrossPlaneViolation("IDENTITY_FIELD_REQUIRED", f"{path}.{field}", "missing"))
        entities[hotel_id] = row
        targets[hotel_id] = target

    entity_ids = set(entities)
    if not entity_ids:
        errors.append(CrossPlaneViolation("EMPTY_ENTITY_SET", "entities", "at least one entity is required"))

    planes = _mapping(payload.get("planes"), "planes", errors)
    plane_names = set(planes)
    if plane_names != _REQUIRED_PLANES:
        errors.append(CrossPlaneViolation("PLANE_SET_MISMATCH", "planes", f"missing={sorted(_REQUIRED_PLANES-plane_names)} extra={sorted(plane_names-_REQUIRED_PLANES)}"))

    db = _mapping(planes.get("constrained_db"), "planes.constrained_db", errors)
    if db.get("action") != "REPLAY_ARR_1_0_FROM_EXACT_V13_PARENT":
        errors.append(CrossPlaneViolation("ARR_ACTION_REQUIRED", "planes.constrained_db.action", "unexpected action"))
    sha = db.get("expected_output_sha256_observation")
    if not isinstance(sha, str) or not _SHA256_RE.fullmatch(sha):
        errors.append(CrossPlaneViolation("INVALID_REPAIRED_SHA", "planes.constrained_db.expected_output_sha256_observation", "expected lowercase SHA-256"))
    if db.get("active_denominator_after_replay") is not None:
        errors.append(CrossPlaneViolation("DENOMINATOR_INFERENCE_FORBIDDEN", "planes.constrained_db.active_denominator_after_replay", "must be null before cross-plane reconciliation"))
    if db.get("denominator_state") != "RECONCILE_REQUIRED_CROSS_PLANE":
        errors.append(CrossPlaneViolation("DENOMINATOR_STATE_INVALID", "planes.constrained_db.denominator_state", "must remain reconcile-required"))

    hotels = _mapping(planes.get("HOTELS_V2"), "planes.HOTELS_V2", errors)
    hotel_keys = _single_mutation_keys(hotels, "planes.HOTELS_V2", errors)
    if hotel_keys != entity_ids:
        errors.append(CrossPlaneViolation("HOTEL_SET_MISMATCH", "planes.HOTELS_V2", f"expected {sorted(entity_ids)}, got {sorted(hotel_keys)}"))
    hotel_mutations = _list(hotels.get("mutations"), "planes.HOTELS_V2.mutations", errors)
    if hotel_mutations:
        row = _mapping(hotel_mutations[0], "planes.HOTELS_V2.mutations[0]", errors)
        set_values = _mapping(row.get("set"), "planes.HOTELS_V2.mutations[0].set", errors)
        if set_values.get("state") != "CANONICAL_CURRENT_RECONCILED":
            errors.append(CrossPlaneViolation("HOTEL_RESTORE_STATE_INVALID", "planes.HOTELS_V2.mutations[0].set.state", "unexpected state"))

    intel = _mapping(planes.get("HOTEL_INTELLIGENCE_V1"), "planes.HOTEL_INTELLIGENCE_V1", errors)
    intel_keys = _single_mutation_keys(intel, "planes.HOTEL_INTELLIGENCE_V1", errors)
    if intel_keys != entity_ids:
        errors.append(CrossPlaneViolation("INTELLIGENCE_SET_MISMATCH", "planes.HOTEL_INTELLIGENCE_V1", "must equal repaired entity set"))
    intel_mutations = _list(intel.get("mutations"), "planes.HOTEL_INTELLIGENCE_V1.mutations", errors)
    if intel_mutations:
        row = _mapping(intel_mutations[0], "planes.HOTEL_INTELLIGENCE_V1.mutations[0]", errors)
        set_values = _mapping(row.get("set"), "planes.HOTEL_INTELLIGENCE_V1.mutations[0].set", errors)
        if set_values.get("enrichment_level") != "L1" or set_values.get("identity_state") != "CANONICAL_INDEXED_RECONCILE_SEED":
            errors.append(CrossPlaneViolation("HISTORICAL_INTELLIGENCE_STATE_REQUIRED", "planes.HOTEL_INTELLIGENCE_V1.mutations[0].set", "must restore revision-464 L1 seed state"))

    graph_nodes = _mapping(planes.get("GRAPH_NODES_V2"), "planes.GRAPH_NODES_V2", errors)
    node_keys = _single_mutation_keys(graph_nodes, "planes.GRAPH_NODES_V2", errors)
    expected_nodes = {f"HOTEL:{x}" for x in entity_ids} | {f"INTEL:{x}" for x in entity_ids}
    if node_keys != expected_nodes:
        errors.append(CrossPlaneViolation("GRAPH_NODE_SET_MISMATCH", "planes.GRAPH_NODES_V2", "must include HOTEL and INTEL node for every entity"))

    graph_edges = _mapping(planes.get("GRAPH_EDGES_V2"), "planes.GRAPH_EDGES_V2", errors)
    edge_mutations = _list(graph_edges.get("mutations"), "planes.GRAPH_EDGES_V2.mutations", errors)
    actions: dict[str, set[str]] = {}
    for index, raw in enumerate(edge_mutations):
        row = _mapping(raw, f"planes.GRAPH_EDGES_V2.mutations[{index}]", errors)
        action = row.get("action")
        keys = _list(row.get("keys"), f"planes.GRAPH_EDGES_V2.mutations[{index}].keys", errors)
        if isinstance(action, str):
            actions[action] = {str(x) for x in keys if isinstance(x, str)}
    expected_alias_edges = {f"EDGE:ALIAS:{alias_id}:{targets[alias_id]}" for alias_id in entity_ids}
    expected_intel_edges = {f"EDGE:HOTEL_INTEL:{alias_id}" for alias_id in entity_ids}
    if actions.get("REMOVE_INVALID_ALIAS_EDGE") != expected_alias_edges:
        errors.append(CrossPlaneViolation("ALIAS_EDGE_SET_MISMATCH", "planes.GRAPH_EDGES_V2", "invalid ALIASES_TO set is incomplete or drifted"))
    if actions.get("RESTORE_EXISTING_EDGE_FIELDS") != expected_intel_edges:
        errors.append(CrossPlaneViolation("HAS_INTELLIGENCE_SET_MISMATCH", "planes.GRAPH_EDGES_V2", "HAS_INTELLIGENCE restore set is incomplete or drifted"))

    er = _mapping(planes.get("ENTITY_RESOLUTION"), "planes.ENTITY_RESOLUTION", errors)
    er_records = _list(er.get("records"), "planes.ENTITY_RESOLUTION.records", errors)
    if len(set(str(x) for x in er_records)) != len(entity_ids):
        errors.append(CrossPlaneViolation("ENTITY_RESOLUTION_CARDINALITY", "planes.ENTITY_RESOLUTION.records", "expected one unique anti-join record per entity"))
    if er.get("action") != "PRESERVE_RESEARCH_ANTI_JOIN_EVIDENCE":
        errors.append(CrossPlaneViolation("ENTITY_RESOLUTION_ACTION_INVALID", "planes.ENTITY_RESOLUTION.action", "must preserve research evidence without physical alias meaning"))

    transitions = _mapping(planes.get("STATE_TRANSITIONS"), "planes.STATE_TRANSITIONS", errors)
    original_ids = _list(transitions.get("preserve_original_transition_ids"), "planes.STATE_TRANSITIONS.preserve_original_transition_ids", errors)
    if len(set(str(x) for x in original_ids)) != len(entity_ids):
        errors.append(CrossPlaneViolation("TRANSITION_HISTORY_CARDINALITY", "planes.STATE_TRANSITIONS", "must preserve one original transition per repaired entity"))
    template = _mapping(transitions.get("append_template"), "planes.STATE_TRANSITIONS.append_template", errors)
    if template.get("from_state") != "SUPERSEDED_DUPLICATE" or template.get("to_state") != "CANONICAL_CURRENT_RECONCILED":
        errors.append(CrossPlaneViolation("CORRECTIVE_TRANSITION_INVALID", "planes.STATE_TRANSITIONS.append_template", "unexpected state transition"))
    if template.get("reversible") is not True:
        errors.append(CrossPlaneViolation("CORRECTIVE_TRANSITION_NOT_REVERSIBLE", "planes.STATE_TRANSITIONS.append_template.reversible", "must be true"))

    observability = _mapping(planes.get("observability_and_scheduler"), "planes.observability_and_scheduler", errors)
    required_observability = set(str(x) for x in _list(observability.get("required"), "planes.observability_and_scheduler.required", errors))
    for marker in {"active denominator", "Intelligence denominator", "Operational Graph denominator", "scheduler tasks", "engine metrics"}:
        if marker not in required_observability:
            errors.append(CrossPlaneViolation("OBSERVABILITY_RECOMPUTE_MISSING", "planes.observability_and_scheduler.required", marker))

    gates = "\n".join(str(x) for x in _list(payload.get("promotion_gates"), "promotion_gates", errors))
    for marker in ("ASR-1.0 = EXACT", "DB↔HOTELS_V2 exact", "restore/replay/idempotency PASS", "production readiness gauntlet PASS"):
        if marker not in gates:
            errors.append(CrossPlaneViolation("PROMOTION_GATE_MISSING", "promotion_gates", marker))

    state = "EXACT" if not errors else "RECONCILE_REQUIRED"
    return CrossPlaneResult(state=state, entities=len(entity_ids), violations=tuple(errors))


def load_and_validate(path: str | Path) -> CrossPlaneResult:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("cross-plane write set must be a JSON object")
    return validate_cross_plane_write_set(raw)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: python -m swiss_os.alias_cross_plane <write-set.json>", file=sys.stderr)
        return 2
    try:
        result = load_and_validate(args[0])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"cross_plane_write_set_valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0 if result.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())

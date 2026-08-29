from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import re
from typing import Iterable, Mapping, Sequence

from .asr_repair import AliasRepairPlan

_HOTEL_ID_RE = re.compile(r"^H-\d{4}$")
_REQUIRED_CAPABILITIES = (
    "constrained_db_write",
    "native_hotels_master_write",
    "intelligence_write",
    "operational_graph_write",
    "observability_write",
)


def _strict_bool(value: object, *, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field} must be a JSON boolean")
    return value


def _hotel_id_set(values: Iterable[object], *, field: str) -> frozenset[str]:
    ids: list[str] = []
    for value in tuple(values):
        if not isinstance(value, str) or not _HOTEL_ID_RE.fullmatch(value):
            raise ValueError(f"{field} contains invalid hotel ID: {value!r}")
        ids.append(value)
    if len(set(ids)) != len(ids):
        raise ValueError(f"{field} contains duplicate hotel IDs")
    return frozenset(ids)


def _edge_set(values: Iterable[Sequence[object]], *, field: str) -> frozenset[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    for value in values:
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError(f"{field} must contain [alias_id, canonical_id] pairs")
        alias_id, target_id = value
        if (
            not isinstance(alias_id, str)
            or not isinstance(target_id, str)
            or not _HOTEL_ID_RE.fullmatch(alias_id)
            or not _HOTEL_ID_RE.fullmatch(target_id)
        ):
            raise ValueError(f"{field} contains invalid edge: {value!r}")
        if alias_id == target_id:
            raise ValueError(f"{field} contains self alias: {alias_id}")
        edges.append((alias_id, target_id))
    if len(set(edges)) != len(edges):
        raise ValueError(f"{field} contains duplicate edges")
    alias_sides = [edge[0] for edge in edges]
    if len(set(alias_sides)) != len(alias_sides):
        raise ValueError(f"{field} contains more than one target for an alias ID")
    return frozenset(edges)


@dataclass(frozen=True)
class AuthorityRepairExpected:
    parent_manifest: str
    authority_epoch: str
    physical_ids: frozenset[str]
    alias_edges: frozenset[tuple[str, str]]
    active_ids: frozenset[str]
    quarantined_edges: frozenset[tuple[str, str]]

    def as_dict(self) -> dict[str, object]:
        return {
            "parent_manifest": self.parent_manifest,
            "authority_epoch": self.authority_epoch,
            "physical_ids": sorted(self.physical_ids),
            "alias_edges": [list(edge) for edge in sorted(self.alias_edges)],
            "active_ids": sorted(self.active_ids),
            "quarantined_edges": [list(edge) for edge in sorted(self.quarantined_edges)],
            "physical_count": len(self.physical_ids),
            "active_count": len(self.active_ids),
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }


@dataclass(frozen=True)
class AuthorityRepairValidation:
    state: str
    promotion_eligible: bool
    violations: tuple[str, ...]
    expected_active_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "authority_repair_state": self.state,
            "promotion_eligible": self.promotion_eligible,
            "violations": list(self.violations),
            "expected_active_count": self.expected_active_count,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound_opened": False,
            "send_allowed": 0,
        }


def compile_authority_repair_expected(
    *,
    parent_manifest: str,
    authority_epoch: str,
    physical_ids: Iterable[object],
    current_alias_edges: Iterable[Sequence[object]],
    plan: AliasRepairPlan,
) -> AuthorityRepairExpected:
    """Compile exact post-repair PK/edge sets without mutating authority."""

    if not isinstance(parent_manifest, str) or not parent_manifest.strip():
        raise ValueError("parent_manifest is required")
    if not isinstance(authority_epoch, str) or not authority_epoch.strip():
        raise ValueError("authority_epoch is required")
    if not plan.canary_eligible:
        raise ValueError("alias repair plan is not canary eligible")

    physical = _hotel_id_set(physical_ids, field="physical_ids")
    current_edges = _edge_set(current_alias_edges, field="current_alias_edges")
    quarantined = frozenset(
        (action.alias_hotel_id, action.erroneous_target_id)
        for action in plan.actions
    )
    if not quarantined:
        raise ValueError("repair plan has no quarantine actions")
    missing = quarantined - current_edges
    if missing:
        raise ValueError(f"repair plan references absent alias edges: {sorted(missing)}")
    for alias_id, target_id in current_edges:
        if alias_id not in physical or target_id not in physical:
            raise ValueError("current alias edge references a non-physical hotel ID")

    repaired_edges = current_edges - quarantined
    remaining_alias_ids = {alias_id for alias_id, _ in repaired_edges}
    active = physical - remaining_alias_ids
    return AuthorityRepairExpected(
        parent_manifest=parent_manifest.strip(),
        authority_epoch=authority_epoch.strip(),
        physical_ids=physical,
        alias_edges=repaired_edges,
        active_ids=frozenset(active),
        quarantined_edges=quarantined,
    )


def _mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return value


def _receipt_ids(receipt: Mapping[str, object], key: str, *, field: str) -> frozenset[str]:
    value = receipt.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{field}.{key} must be an array")
    return _hotel_id_set(value, field=f"{field}.{key}")


def _receipt_edges(receipt: Mapping[str, object], key: str, *, field: str) -> frozenset[tuple[str, str]]:
    value = receipt.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{field}.{key} must be an array")
    return _edge_set(value, field=f"{field}.{key}")


def validate_authority_repair(
    expected: AuthorityRepairExpected,
    receipts: Mapping[str, object],
    capabilities: Mapping[str, object],
    qa: Mapping[str, object],
    governance: Mapping[str, object],
    *,
    live_parent_manifest: str,
    live_authority_epoch: str,
) -> AuthorityRepairValidation:
    """Evaluate whether a completed cross-plane repair is eligible for promotion.

    This function is a pure gate. Even on success it does not advance authority.
    """

    violations: list[str] = []
    if live_parent_manifest != expected.parent_manifest:
        violations.append("PARENT_MANIFEST_DRIFT")
    if live_authority_epoch != expected.authority_epoch:
        violations.append("AUTHORITY_EPOCH_DRIFT")

    for name in _REQUIRED_CAPABILITIES:
        try:
            available = _strict_bool(capabilities.get(name), field=f"capabilities.{name}")
        except ValueError as exc:
            violations.append(str(exc))
            continue
        if not available:
            violations.append(f"CAPABILITY_UNAVAILABLE:{name}")

    db = _mapping(receipts.get("db"), field="receipts.db")
    sheets = _mapping(receipts.get("hotels_master"), field="receipts.hotels_master")
    intelligence = _mapping(receipts.get("intelligence"), field="receipts.intelligence")
    graph = _mapping(receipts.get("operational_graph"), field="receipts.operational_graph")
    observability = _mapping(receipts.get("observability"), field="receipts.observability")

    comparisons = (
        ("DB_PHYSICAL_PK_MISMATCH", _receipt_ids(db, "physical_ids", field="receipts.db"), expected.physical_ids),
        ("SHEETS_PHYSICAL_PK_MISMATCH", _receipt_ids(sheets, "physical_ids", field="receipts.hotels_master"), expected.physical_ids),
        ("DB_ACTIVE_PK_MISMATCH", _receipt_ids(db, "active_ids", field="receipts.db"), expected.active_ids),
        ("SHEETS_ACTIVE_PK_MISMATCH", _receipt_ids(sheets, "active_ids", field="receipts.hotels_master"), expected.active_ids),
        ("INTELLIGENCE_ACTIVE_PK_MISMATCH", _receipt_ids(intelligence, "active_ids", field="receipts.intelligence"), expected.active_ids),
        ("GRAPH_ACTIVE_PK_MISMATCH", _receipt_ids(graph, "active_hotel_ids", field="receipts.operational_graph"), expected.active_ids),
        ("DB_ALIAS_EDGE_MISMATCH", _receipt_edges(db, "alias_edges", field="receipts.db"), expected.alias_edges),
        ("SHEETS_ALIAS_EDGE_MISMATCH", _receipt_edges(sheets, "alias_edges", field="receipts.hotels_master"), expected.alias_edges),
        ("GRAPH_ALIAS_EDGE_MISMATCH", _receipt_edges(graph, "alias_edges", field="receipts.operational_graph"), expected.alias_edges),
    )
    for code, actual, wanted in comparisons:
        if actual != wanted:
            violations.append(code)

    expected_count = len(expected.active_ids)
    for key in ("metric_active_count", "checkpoint_active_count", "scheduler_denominator"):
        value = observability.get(key)
        if type(value) is not int or value != expected_count:
            violations.append(f"OBSERVABILITY_MISMATCH:{key}")
    for key in ("state_transition_emitted", "run_log_emitted", "issue_updated"):
        try:
            flag = _strict_bool(observability.get(key), field=f"observability.{key}")
        except ValueError as exc:
            violations.append(str(exc))
            continue
        if not flag:
            violations.append(f"OBSERVABILITY_MISSING:{key}")

    if qa.get("integrity_check") != "ok":
        violations.append("SQLITE_INTEGRITY_FAILED")
    for key in (
        "foreign_key_violations",
        "replay_unintended_mutations",
        "restore_logical_differences",
        "semantic_alias_violations",
        "active_name_city_duplicates",
        "invalid_alias_targets",
    ):
        value = qa.get(key)
        if type(value) is not int or value != 0:
            violations.append(f"QA_NONZERO:{key}")

    if governance.get("outbound") != "CLOSED":
        violations.append("OUTBOUND_NOT_CLOSED")
    if governance.get("send_allowed") != 0 or type(governance.get("send_allowed")) is not int:
        violations.append("SEND_ALLOWED_NOT_ZERO")
    try:
        external_actions = _strict_bool(
            governance.get("external_actions_performed"),
            field="governance.external_actions_performed",
        )
    except ValueError as exc:
        violations.append(str(exc))
    else:
        if external_actions:
            violations.append("EXTERNAL_ACTIONS_PERFORMED")

    unique = tuple(dict.fromkeys(violations))
    eligible = not unique
    return AuthorityRepairValidation(
        state="COMPLETE_AUTHORITY_ELIGIBLE" if eligible else "RECONCILE_REQUIRED",
        promotion_eligible=eligible,
        violations=unique,
        expected_active_count=expected_count,
    )


def _read_json(path: str) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("input must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.asr_authority")
    parser.add_argument("payload")
    args = parser.parse_args(argv)
    payload = _read_json(args.payload)
    expected_raw = _mapping(payload.get("expected"), field="expected")
    expected = AuthorityRepairExpected(
        parent_manifest=str(expected_raw.get("parent_manifest", "")),
        authority_epoch=str(expected_raw.get("authority_epoch", "")),
        physical_ids=_hotel_id_set(expected_raw.get("physical_ids", ()), field="expected.physical_ids"),
        alias_edges=_edge_set(expected_raw.get("alias_edges", ()), field="expected.alias_edges"),
        active_ids=_hotel_id_set(expected_raw.get("active_ids", ()), field="expected.active_ids"),
        quarantined_edges=_edge_set(expected_raw.get("quarantined_edges", ()), field="expected.quarantined_edges"),
    )
    result = validate_authority_repair(
        expected,
        _mapping(payload.get("receipts"), field="receipts"),
        _mapping(payload.get("capabilities"), field="capabilities"),
        _mapping(payload.get("qa"), field="qa"),
        _mapping(payload.get("governance"), field="governance"),
        live_parent_manifest=str(payload.get("live_parent_manifest", "")),
        live_authority_epoch=str(payload.get("live_authority_epoch", "")),
    )
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0 if result.promotion_eligible else 2


if __name__ == "__main__":
    raise SystemExit(main())

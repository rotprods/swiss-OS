from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .alias_semantics import (
    AliasSemanticResult,
    identity_key,
    validate_alias_semantics,
)


@dataclass(frozen=True)
class AliasRepairAction:
    alias_hotel_id: str
    erroneous_target_id: str
    action: str
    reason_code: str

    def as_dict(self) -> dict[str, str]:
        return {
            "alias_hotel_id": self.alias_hotel_id,
            "erroneous_target_id": self.erroneous_target_id,
            "action": self.action,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class AliasRepairPlan:
    state: str
    actions: tuple[AliasRepairAction, ...]
    blocked_alias_ids: tuple[str, ...]
    authority_advanced: bool = False
    h_id_allocations: int = 0
    outbound_opened: bool = False
    send_allowed: int = 0

    @property
    def canary_eligible(self) -> bool:
        return self.state == "CANARY_ELIGIBLE" and not self.blocked_alias_ids

    def as_dict(self) -> dict[str, object]:
        return {
            "repair_plan_state": self.state,
            "canary_eligible": self.canary_eligible,
            "actions": [item.as_dict() for item in self.actions],
            "blocked_alias_ids": list(self.blocked_alias_ids),
            "authority_advanced": self.authority_advanced,
            "h_id_allocations": self.h_id_allocations,
            "outbound_opened": self.outbound_opened,
            "send_allowed": self.send_allowed,
        }


def _as_rows(
    rows: Iterable[Mapping[str, object]],
    *,
    label: str,
) -> tuple[Mapping[str, object], ...]:
    materialized = tuple(rows)
    if not all(isinstance(row, Mapping) for row in materialized):
        raise ValueError(f"{label} must contain only mapping rows")
    return materialized


def _hotel_id(row: Mapping[str, object]) -> str:
    value = row.get("hotel_id", row.get("id", ""))
    return value.strip() if isinstance(value, str) else ""


def _hotel_name(row: Mapping[str, object]) -> object:
    return row.get("canonical_name", row.get("hotel_name", row.get("name", "")))


def _hotel_city(row: Mapping[str, object]) -> object:
    return row.get("city", "")


def _alias_id(row: Mapping[str, object]) -> str:
    value = (
        row.get("alias_hotel_id")
        or row.get("alias_id")
        or row.get("superseded_hotel_id")
        or ""
    )
    return value.strip() if isinstance(value, str) else ""


def _alias_target(row: Mapping[str, object]) -> str:
    value = (
        row.get("canonical_hotel_id")
        or row.get("canonical_id")
        or row.get("superseded_by")
        or ""
    )
    return value.strip() if isinstance(value, str) else ""


def plan_phantom_alias_quarantine(
    catalog_rows: Iterable[Mapping[str, object]],
    alias_rows: Iterable[Mapping[str, object]],
    resolution_rows: Iterable[Mapping[str, object]],
) -> AliasRepairPlan:
    """Build a fail-closed, non-authoritative repair plan.

    A repair action is emitted only for the ASR pattern where the resolution
    candidate identifies the canonical target but not the physical alias H-ID,
    and the target identity occurs exactly once in the physical catalog.

    The plan quarantines the edge; it does not delete a physical H-ID, allocate
    an H-ID, advance authority, mutate Sheets/Graph/Intelligence or open
    outbound.
    """

    catalog = _as_rows(catalog_rows, label="catalog_rows")
    aliases = _as_rows(alias_rows, label="alias_rows")
    resolutions = _as_rows(resolution_rows, label="resolution_rows")

    result: AliasSemanticResult = validate_alias_semantics(
        catalog,
        aliases,
        resolutions,
    )
    catalog_by_id = {_hotel_id(row): row for row in catalog}
    identity_frequency: dict[tuple[str, str], int] = {}
    for row in catalog:
        key = identity_key(_hotel_name(row), _hotel_city(row))
        if all(key):
            identity_frequency[key] = identity_frequency.get(key, 0) + 1

    violations_by_alias: dict[str, list[str]] = {}
    for violation in result.violations:
        violations_by_alias.setdefault(violation.alias_hotel_id, []).append(
            violation.code
        )

    actions: list[AliasRepairAction] = []
    blocked: list[str] = []

    for alias in aliases:
        alias_id = _alias_id(alias)
        target_id = _alias_target(alias)
        codes = set(violations_by_alias.get(alias_id, ()))
        target = catalog_by_id.get(target_id)
        target_key = (
            identity_key(_hotel_name(target), _hotel_city(target))
            if target is not None
            else ("", "")
        )

        eligible = (
            "ALIAS_IDENTITY_MISMATCH" in codes
            and target is not None
            and all(target_key)
            and identity_frequency.get(target_key) == 1
        )
        if eligible:
            actions.append(
                AliasRepairAction(
                    alias_hotel_id=alias_id,
                    erroneous_target_id=target_id,
                    action="QUARANTINE_ALIAS_EDGE_REACTIVATE_PHYSICAL_ID",
                    reason_code="PHANTOM_ALIAS_H_ID_ROW_DRIFT",
                )
            )
        elif codes:
            blocked.append(alias_id)

    state = (
        "CANARY_ELIGIBLE"
        if actions and not blocked and len(actions) == len(aliases)
        else "RECONCILE_REQUIRED"
    )
    return AliasRepairPlan(
        state=state,
        actions=tuple(actions),
        blocked_alias_ids=tuple(sorted(set(blocked))),
    )


def apply_plan_to_alias_rows(
    alias_rows: Iterable[Mapping[str, object]],
    plan: AliasRepairPlan,
) -> tuple[Mapping[str, object], ...]:
    """Return a canary alias set with planned phantom edges quarantined.

    This pure helper deliberately does not touch physical catalog rows or any
    persistence plane. It is safe for replay and deterministic tests.
    """

    aliases = _as_rows(alias_rows, label="alias_rows")
    if not plan.canary_eligible:
        raise ValueError("repair plan is not canary eligible")
    quarantined = {
        (action.alias_hotel_id, action.erroneous_target_id)
        for action in plan.actions
    }
    return tuple(
        row
        for row in aliases
        if (_alias_id(row), _alias_target(row)) not in quarantined
    )

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


TERMINAL_MAPPING_STATES = {
    "ACTIVE_CANONICAL",
    "ALIAS_TO_CANONICAL",
    "EXCLUDED_WITH_REASON",
}


@dataclass(frozen=True)
class CRMUniverseMetrics:
    snapshot_id: str
    snapshot_state: str
    snapshot_raw_records: int
    active_canonical_mappings: int
    alias_to_canonical_mappings: int
    excluded_with_reason_mappings: int
    reconcile_required: int
    unmapped_records: int
    unresolved_duplicate_conflicts: int
    invalid_alias_targets: int
    constrained_active_canonical: int
    sheets_active_canonical: int
    graph_active_canonical: int
    intelligence_active_canonical: int
    db_sheets_exact: bool
    graph_exact: bool
    intelligence_exact: bool
    coverage_snapshot_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def terminal_mapped_records(self) -> int:
        return (
            self.active_canonical_mappings
            + self.alias_to_canonical_mappings
            + self.excluded_with_reason_mappings
        )

    @property
    def coverage_pct(self) -> float:
        if self.snapshot_raw_records <= 0:
            return 0.0
        return self.terminal_mapped_records / self.snapshot_raw_records


@dataclass(frozen=True)
class CRMUniverseGateResult:
    complete: bool
    violations: tuple[str, ...]
    coverage_pct: float
    terminal_mapped_records: int

    def as_dict(self) -> dict[str, object]:
        return {
            "complete": self.complete,
            "violations": list(self.violations),
            "coverage_pct": self.coverage_pct,
            "terminal_mapped_records": self.terminal_mapped_records,
        }


def _non_negative(name: str, value: int, violations: list[str]) -> None:
    if value < 0:
        violations.append(f"{name} must be non-negative")


def validate_crm_universe_gate(metrics: CRMUniverseMetrics) -> CRMUniverseGateResult:
    """Validate CUP-1.0 CRM-universe completion semantics.

    This function is intentionally fail-closed. It validates mapping accounting,
    reconciliation state, cross-plane parity and snapshot lineage. It does not
    infer missing values and it does not open outbound.
    """

    violations: list[str] = []

    if not metrics.snapshot_id.strip():
        violations.append("snapshot_id is required")
    if metrics.snapshot_state != "FROZEN_VERIFIED":
        violations.append("snapshot_state must be FROZEN_VERIFIED")

    integer_fields = {
        "snapshot_raw_records": metrics.snapshot_raw_records,
        "active_canonical_mappings": metrics.active_canonical_mappings,
        "alias_to_canonical_mappings": metrics.alias_to_canonical_mappings,
        "excluded_with_reason_mappings": metrics.excluded_with_reason_mappings,
        "reconcile_required": metrics.reconcile_required,
        "unmapped_records": metrics.unmapped_records,
        "unresolved_duplicate_conflicts": metrics.unresolved_duplicate_conflicts,
        "invalid_alias_targets": metrics.invalid_alias_targets,
        "constrained_active_canonical": metrics.constrained_active_canonical,
        "sheets_active_canonical": metrics.sheets_active_canonical,
        "graph_active_canonical": metrics.graph_active_canonical,
        "intelligence_active_canonical": metrics.intelligence_active_canonical,
    }
    for name, value in integer_fields.items():
        _non_negative(name, value, violations)

    if metrics.snapshot_raw_records <= 0:
        violations.append("snapshot_raw_records must be greater than zero")

    if metrics.terminal_mapped_records != metrics.snapshot_raw_records:
        violations.append(
            "mapping accounting mismatch: raw records must equal active + alias + excluded"
        )

    if metrics.unmapped_records != 0:
        violations.append("unmapped_records must be zero")
    if metrics.reconcile_required != 0:
        violations.append("reconcile_required must be zero")
    if metrics.unresolved_duplicate_conflicts != 0:
        violations.append("unresolved_duplicate_conflicts must be zero")
    if metrics.invalid_alias_targets != 0:
        violations.append("invalid_alias_targets must be zero")

    if not metrics.db_sheets_exact:
        violations.append("DB ↔ Sheets/CRM reconciliation must be exact")
    if not metrics.graph_exact:
        violations.append("Operational Graph reconciliation must be exact")
    if not metrics.intelligence_exact:
        violations.append("Intelligence reconciliation must be exact")

    active_denominators = {
        metrics.constrained_active_canonical,
        metrics.sheets_active_canonical,
        metrics.graph_active_canonical,
        metrics.intelligence_active_canonical,
    }
    if len(active_denominators) != 1:
        violations.append("active canonical denominator differs across planes")

    if metrics.active_canonical_mappings < metrics.constrained_active_canonical:
        violations.append(
            "active canonical source mappings cannot be lower than constrained active canonical"
        )

    coverage_ids = tuple(x for x in metrics.coverage_snapshot_ids if x)
    if coverage_ids and any(x != metrics.snapshot_id for x in coverage_ids):
        violations.append("coverage metrics are not bound to one snapshot_id")

    return CRMUniverseGateResult(
        complete=not violations,
        violations=tuple(violations),
        coverage_pct=metrics.coverage_pct,
        terminal_mapped_records=metrics.terminal_mapped_records,
    )


def validate_mapping_states(states: Iterable[str]) -> tuple[str, ...]:
    """Return invalid/non-terminal mapping states for final gate evaluation."""

    return tuple(sorted({state for state in states if state not in TERMINAL_MAPPING_STATES}))

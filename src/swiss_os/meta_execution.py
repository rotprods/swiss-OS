from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class ExecutionMode(str, Enum):
    AUTHORITATIVE_WRITE = "AUTHORITATIVE_WRITE"
    READ_ONLY_RESEARCH = "READ_ONLY_RESEARCH"
    DEGRADED_CANARY = "DEGRADED_CANARY"
    RECOVERY_RECONCILE = "RECOVERY_RECONCILE"
    BLOCKED_P0 = "BLOCKED_P0"


class MetaRoute(str, Enum):
    AUTHORITY_RECOVERY = "AUTHORITY_RECOVERY"
    STRUCTURED_SOURCE_CAPTURE = "STRUCTURED_SOURCE_CAPTURE"
    MEMBER_DIRECTORY_MANIFEST = "MEMBER_DIRECTORY_MANIFEST"
    SOURCE_SCOPE_RECONCILIATION = "SOURCE_SCOPE_RECONCILIATION"
    FROZEN_CANDIDATE_EXPORT = "FROZEN_CANDIDATE_EXPORT"
    MASS_INGEST_STAGING = "MASS_INGEST_STAGING"
    EXACT_CURRENT_REFRESH = "EXACT_CURRENT_REFRESH"
    TERMINAL_MAPPING = "TERMINAL_MAPPING"
    AUTHORITATIVE_PROMOTION = "AUTHORITATIVE_PROMOTION"
    DRIVE_MOUNT_REHYDRATION = "DRIVE_MOUNT_REHYDRATION"
    ENGINEERING_QA = "ENGINEERING_QA"
    RECOVERY_PERSISTENCE = "RECOVERY_PERSISTENCE"
    NO_SAFE_ROUTE = "NO_SAFE_ROUTE"


@dataclass(frozen=True)
class MetaCapabilities:
    authority_reconstructable: bool = True
    ancestry_current: bool = True
    internal_p0: bool = False

    constrained_db_read: bool = False
    constrained_db_write: bool = False
    native_sheets_read: bool = False
    native_sheets_write: bool = False
    drive_mount_read: bool = False
    drive_create_only_write: bool = False

    github_read: bool = True
    github_write: bool = False
    github_ci: bool = False
    library_read: bool = False
    library_write: bool = False
    web_research: bool = False

    discover_swiss_subscription: bool = False
    discover_capture_valid: bool = False
    member_directory_evidence: bool = False
    member_directory_manifest_complete: bool = False
    source_scope_reconciled: bool = False
    frozen_candidate: bool = False
    ingest_records_ready: bool = False

    operational_graph_write: bool = False
    intelligence_write: bool = False
    observability_write: bool = False

    unresolved_source_records: int = 0
    reconcile_required: int = 0
    exact_current_refresh_backlog: int = 0
    crm_universe_complete: bool = False
    promotion_ready: bool = False

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "MetaCapabilities":
        fields = cls.__dataclass_fields__
        unknown = sorted(set(payload) - set(fields))
        if unknown:
            raise ValueError(f"unknown capability keys: {', '.join(unknown)}")
        values: dict[str, Any] = {}
        for name, field in fields.items():
            if name not in payload:
                continue
            raw = payload[name]
            if field.type is int or str(field.type) == "<class 'int'>":
                values[name] = int(raw)
            else:
                values[name] = bool(raw)
        return cls(**values)


@dataclass(frozen=True)
class MetaDecision:
    execution_mode: ExecutionMode
    route: MetaRoute
    reason: str
    graph_impact: str
    hard_blocks: tuple[str, ...] = ()
    capabilities_used: tuple[str, ...] = ()
    next_fallback_routes: tuple[MetaRoute, ...] = ()
    authority_advance_allowed: bool = False
    canonical_id_allocation_allowed: bool = False
    outbound_allowed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_mode": self.execution_mode.value,
            "selected_route": self.route.value,
            "reason": self.reason,
            "graph_impact": self.graph_impact,
            "hard_blocks": list(self.hard_blocks),
            "capabilities_used": list(self.capabilities_used),
            "next_fallback_routes": [r.value for r in self.next_fallback_routes],
            "authority_advance_allowed": self.authority_advance_allowed,
            "canonical_id_allocation_allowed": self.canonical_id_allocation_allowed,
            "outbound_allowed": self.outbound_allowed,
        }


def _fallbacks(*routes: MetaRoute) -> tuple[MetaRoute, ...]:
    return tuple(routes)


def choose_meta_route(c: MetaCapabilities) -> MetaDecision:
    """Choose the highest-value safe route without lowering authority gates.

    The planner intentionally defaults all irreversible/promotion permissions to
    false. It only grants authority/canonical-ID permission on the explicit
    authoritative-promotion route, and never grants outbound permission.
    """

    if c.internal_p0 or not c.authority_reconstructable or not c.ancestry_current:
        blocks: list[str] = []
        if c.internal_p0:
            blocks.append("OPEN_INTERNAL_P0")
        if not c.authority_reconstructable:
            blocks.append("AUTHORITY_NOT_RECONSTRUCTABLE")
        if not c.ancestry_current:
            blocks.append("ANCESTRY_STALE_OR_MOVED")
        return MetaDecision(
            execution_mode=ExecutionMode.RECOVERY_RECONCILE,
            route=MetaRoute.AUTHORITY_RECOVERY,
            reason="Authority or ancestry is unsafe; reconciliation outranks new production.",
            graph_impact="META",
            hard_blocks=tuple(blocks),
            capabilities_used=tuple(k for k, v in (
                ("drive_mount_read", c.drive_mount_read),
                ("native_sheets_read", c.native_sheets_read),
                ("constrained_db_read", c.constrained_db_read),
                ("github_read", c.github_read),
                ("library_read", c.library_read),
            ) if v),
            next_fallback_routes=_fallbacks(
                MetaRoute.DRIVE_MOUNT_REHYDRATION,
                MetaRoute.RECOVERY_PERSISTENCE,
                MetaRoute.ENGINEERING_QA,
            ),
        )

    authority_write_ready = all((
        c.constrained_db_write,
        c.native_sheets_write,
        c.operational_graph_write,
        c.intelligence_write,
        c.observability_write,
        c.promotion_ready,
    ))
    if authority_write_ready:
        return MetaDecision(
            execution_mode=ExecutionMode.AUTHORITATIVE_WRITE,
            route=MetaRoute.AUTHORITATIVE_PROMOTION,
            reason="All affected authority planes are writable and the promotion gate is ready.",
            graph_impact="BOTH",
            capabilities_used=(
                "constrained_db_write",
                "native_sheets_write",
                "operational_graph_write",
                "intelligence_write",
                "observability_write",
                "promotion_ready",
            ),
            next_fallback_routes=_fallbacks(MetaRoute.AUTHORITY_RECOVERY),
            authority_advance_allowed=True,
            canonical_id_allocation_allowed=True,
            outbound_allowed=False,
        )

    if c.discover_swiss_subscription and not c.discover_capture_valid:
        return MetaDecision(
            execution_mode=ExecutionMode.DEGRADED_CANARY,
            route=MetaRoute.STRUCTURED_SOURCE_CAPTURE,
            reason="Structured discover.swiss acquisition is available and removes the broadest CRM-universe bottleneck.",
            graph_impact="META",
            capabilities_used=("discover_swiss_subscription",),
            next_fallback_routes=_fallbacks(
                MetaRoute.MEMBER_DIRECTORY_MANIFEST,
                MetaRoute.EXACT_CURRENT_REFRESH,
                MetaRoute.ENGINEERING_QA,
            ),
        )

    if c.discover_capture_valid and not c.member_directory_manifest_complete:
        if c.web_research or c.member_directory_evidence:
            return MetaDecision(
                execution_mode=ExecutionMode.READ_ONLY_RESEARCH,
                route=MetaRoute.MEMBER_DIRECTORY_MANIFEST,
                reason="API capture exists, but complete coherent member-directory evidence is still required for SSR.",
                graph_impact="META",
                capabilities_used=tuple(k for k, v in (
                    ("web_research", c.web_research),
                    ("member_directory_evidence", c.member_directory_evidence),
                ) if v),
                next_fallback_routes=_fallbacks(
                    MetaRoute.EXACT_CURRENT_REFRESH,
                    MetaRoute.RECOVERY_PERSISTENCE,
                    MetaRoute.ENGINEERING_QA,
                ),
            )

    if c.discover_capture_valid and c.member_directory_manifest_complete and not c.source_scope_reconciled:
        return MetaDecision(
            execution_mode=ExecutionMode.DEGRADED_CANARY,
            route=MetaRoute.SOURCE_SCOPE_RECONCILIATION,
            reason="Both source sets exist; SSR-1.0 is the next hard gate before freeze/export.",
            graph_impact="META",
            capabilities_used=("discover_capture_valid", "member_directory_manifest_complete"),
            next_fallback_routes=_fallbacks(
                MetaRoute.MEMBER_DIRECTORY_MANIFEST,
                MetaRoute.EXACT_CURRENT_REFRESH,
            ),
        )

    if c.source_scope_reconciled and c.frozen_candidate and not c.ingest_records_ready:
        return MetaDecision(
            execution_mode=ExecutionMode.DEGRADED_CANARY,
            route=MetaRoute.FROZEN_CANDIDATE_EXPORT,
            reason="Source scope is reconciled; deterministic candidate→CMI export unlocks mass ingest without allocating IDs.",
            graph_impact="META",
            capabilities_used=("source_scope_reconciled", "frozen_candidate"),
            next_fallback_routes=_fallbacks(MetaRoute.MASS_INGEST_STAGING),
        )

    if c.ingest_records_ready and c.constrained_db_write:
        return MetaDecision(
            execution_mode=ExecutionMode.DEGRADED_CANARY,
            route=MetaRoute.MASS_INGEST_STAGING,
            reason="CMI records and constrained staging write are available; classify/anti-join/schedule at scale.",
            graph_impact="META",
            capabilities_used=("ingest_records_ready", "constrained_db_write"),
            next_fallback_routes=_fallbacks(
                MetaRoute.EXACT_CURRENT_REFRESH,
                MetaRoute.TERMINAL_MAPPING,
            ),
        )

    if c.reconcile_required > 0 or c.unresolved_source_records > 0:
        if c.web_research:
            return MetaDecision(
                execution_mode=ExecutionMode.READ_ONLY_RESEARCH,
                route=MetaRoute.EXACT_CURRENT_REFRESH,
                reason="Unresolved source records remain; exact-current evidence resolution is the highest-value safe work.",
                graph_impact="META",
                capabilities_used=("web_research",),
                next_fallback_routes=_fallbacks(
                    MetaRoute.TERMINAL_MAPPING,
                    MetaRoute.MEMBER_DIRECTORY_MANIFEST,
                    MetaRoute.ENGINEERING_QA,
                ),
            )

    if c.source_scope_reconciled and (c.reconcile_required > 0 or c.exact_current_refresh_backlog > 0):
        return MetaDecision(
            execution_mode=ExecutionMode.DEGRADED_CANARY,
            route=MetaRoute.TERMINAL_MAPPING,
            reason="Source scope is known; unresolved entity mappings must reach terminal states before CRM completion.",
            graph_impact="OPERATIONAL",
            capabilities_used=("source_scope_reconciled",),
            next_fallback_routes=_fallbacks(MetaRoute.EXACT_CURRENT_REFRESH),
        )

    if c.drive_mount_read and not c.native_sheets_read:
        return MetaDecision(
            execution_mode=ExecutionMode.RECOVERY_RECONCILE,
            route=MetaRoute.DRIVE_MOUNT_REHYDRATION,
            reason="Native Sheets access is unavailable but the authenticated Drive mount can still rehydrate persistent artifacts.",
            graph_impact="META",
            capabilities_used=("drive_mount_read",),
            next_fallback_routes=_fallbacks(
                MetaRoute.RECOVERY_PERSISTENCE,
                MetaRoute.ENGINEERING_QA,
            ),
        )

    if c.github_write and c.github_ci:
        return MetaDecision(
            execution_mode=ExecutionMode.DEGRADED_CANARY,
            route=MetaRoute.ENGINEERING_QA,
            reason="Operational routes are blocked; Git/CI work is allowed only to close measured execution or integrity debt.",
            graph_impact="META",
            capabilities_used=("github_write", "github_ci"),
            next_fallback_routes=_fallbacks(MetaRoute.RECOVERY_PERSISTENCE),
        )

    if c.library_write or c.drive_create_only_write:
        return MetaDecision(
            execution_mode=ExecutionMode.DEGRADED_CANARY,
            route=MetaRoute.RECOVERY_PERSISTENCE,
            reason="No higher-value operational route is available; persist recoverable state instead of losing work.",
            graph_impact="META",
            capabilities_used=tuple(k for k, v in (
                ("library_write", c.library_write),
                ("drive_create_only_write", c.drive_create_only_write),
            ) if v),
            next_fallback_routes=(),
        )

    return MetaDecision(
        execution_mode=ExecutionMode.BLOCKED_P0,
        route=MetaRoute.NO_SAFE_ROUTE,
        reason="No safe route can currently reduce the bottleneck without violating a hard gate.",
        graph_impact="NONE",
        hard_blocks=("NO_SAFE_PRODUCTIVE_ROUTE",),
        next_fallback_routes=(),
    )

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .v2_kernel import (
    AccessMode,
    AuthorityStatus,
    ClaimState,
    ContextPack,
    EventLedger,
    GraphEdge,
    GraphNode,
    HyperEdge,
    HyperParticipant,
    ScopeClaim,
    Session,
    SessionState,
    TemporalHyperGraph,
    stable_digest,
)
from .v2_runtime_drills import ThreadSafeCoordinationRegistry
from .v2_security import sanitize_public_payload


@dataclass(frozen=True)
class ShadowExecutionResult:
    schema_version: str
    state: str
    main_sha: str
    session_id: str
    work_item_id: str
    graph: dict[str, Any]
    event_ledger_jsonl: str
    event_watermark: str
    contextpack: dict[str, Any]
    next_route: str
    assertions: tuple[str, ...]
    authority_advanced: bool = False
    h_id_allocations: int = 0
    outbound_opened: bool = False
    send_allowed: int = 0

    @property
    def passed(self) -> bool:
        return self.state == "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "state": self.state,
            "passed": self.passed,
            "main_sha": self.main_sha,
            "session_id": self.session_id,
            "work_item_id": self.work_item_id,
            "graph": self.graph,
            "event_watermark": self.event_watermark,
            "contextpack": self.contextpack,
            "next_route": self.next_route,
            "assertions": list(self.assertions),
            "authority_advanced": self.authority_advanced,
            "h_id_allocations": self.h_id_allocations,
            "outbound_opened": self.outbound_opened,
            "send_allowed": self.send_allowed,
        }


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"NEXT payload requires non-empty {key}")
    return value.strip()


def _nested_string(payload: Mapping[str, Any], path: tuple[str, ...]) -> str:
    current: Any = payload
    for key in path:
        if not isinstance(current, Mapping):
            return ""
        current = current.get(key)
    return current.strip() if isinstance(current, str) else ""


def execute_read_only_next_shadow(
    next_payload: Mapping[str, Any],
    *,
    main_sha: str,
    generated_at: str | None = None,
) -> ShadowExecutionResult:
    """Traverse one real public-safe NEXT work item through V2 read-only semantics.

    The bridge validates that the work item is already fail-closed and then emits
    a Session/Claim, causal events, a small operational/meta hypergraph projection,
    ContextPack and NEXT. It cannot allocate IDs or promote authority.
    """

    if not isinstance(next_payload, Mapping):
        raise ValueError("NEXT payload must be a mapping")
    if not isinstance(main_sha, str) or len(main_sha) != 40:
        raise ValueError("main_sha must contain 40 characters")
    project = _required_string(next_payload, "project")
    if project != "SWITZERLAND_JOB_OS":
        raise ValueError("NEXT payload belongs to another project")
    if next_payload.get("authority_advance_allowed") is not False:
        raise ValueError("shadow input must not authorize authority advancement")
    if next_payload.get("canonical_id_allocation_allowed") is not False:
        raise ValueError("shadow input must not authorize H-ID allocation")
    if next_payload.get("outbound_allowed") is not False:
        raise ValueError("shadow input must not authorize outbound")

    timestamp = generated_at or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    cycle_id = _required_string(next_payload, "cycle_id")
    checkpoint_id = _required_string(next_payload, "checkpoint_id")
    selected_route = _required_string(next_payload, "selected_route")
    next_route = _required_string(next_payload, "next_route")
    authority_epoch = _required_string(next_payload, "authority_epoch")
    authority_parent = _nested_string(
        next_payload,
        ("authority_parent_materialized_sha256",),
    ) or _required_string(next_payload, "authority_parent")
    snapshot_id = _nested_string(next_payload, ("source_universe", "snapshot_id"))
    if not snapshot_id:
        snapshot_id = "SOURCE-SNAPSHOT:UNKNOWN-PUBLIC-POINTER"

    safe_input = sanitize_public_payload(dict(next_payload))
    session_id = f"SESSION:V2-SHADOW:{stable_digest([main_sha, cycle_id])[:20]}"
    claim_id = f"CLAIM:V2-SHADOW:{stable_digest([session_id, checkpoint_id])[:20]}"
    work_item_id = f"WORKITEM:{stable_digest([cycle_id, selected_route, next_route])[:24]}"

    coordination = ThreadSafeCoordinationRegistry()
    coordination.open_session(
        Session(
            session_id=session_id,
            project_id="PROJECT:SWITZERLAND_JOB_OS",
            agent_id="AGENT:V2-SHADOW-BRIDGE",
            workstream_id="WORKSTREAM:GRAPH-REFACTOR-V2",
            objective_id="OBJECTIVE:CRM-NEXT-SHADOW",
            correlation_id=f"CORRELATION:{stable_digest(cycle_id)[:20]}",
            state=SessionState.ACTIVE,
            opened_at=timestamp,
            heartbeat_at=timestamp,
        )
    )
    coordination.acquire_claim(
        ScopeClaim(
            claim_id=claim_id,
            session_id=session_id,
            access_mode=AccessMode.READ,
            resource_scopes=("state:crm-next", "source:public-safe-pointer"),
            semantic_scopes=("crm:shadow", "architecture:v2-e2e"),
            state=ClaimState.ACTIVE,
            acquired_at=timestamp,
        )
    )

    ledger = EventLedger()
    events = (
        ("EVENT:V2-SHADOW:0001", "HELLO", {"cycle_id": cycle_id}),
        (
            "EVENT:V2-SHADOW:0002",
            "WORK_STARTED",
            {"work_item_id": work_item_id, "selected_route": selected_route},
        ),
        (
            "EVENT:V2-SHADOW:0003",
            "STATE_OBSERVED",
            {
                "authority_epoch": authority_epoch,
                "authority_parent": authority_parent,
                "snapshot_id": snapshot_id,
            },
        ),
        (
            "EVENT:V2-SHADOW:0004",
            "EVIDENCE_SCOPED",
            {"input_digest": stable_digest(safe_input)},
        ),
        (
            "EVENT:V2-SHADOW:0005",
            "PROJECTION_REBUILT",
            {"projection": "CRM_NEXT_SHADOW"},
        ),
        (
            "EVENT:V2-SHADOW:0006",
            "ASSURANCE_VERIFIED",
            {
                "authority_advanced": False,
                "h_id_allocations": 0,
                "outbound_opened": False,
                "send_allowed": 0,
            },
        ),
        (
            "EVENT:V2-SHADOW:0007",
            "NEXT_EMITTED",
            {"next_route": next_route},
        ),
    )
    previous: str | None = None
    for event_id, event_type, payload in events:
        event = ledger.new_event(
            event_id=event_id,
            project_id="PROJECT:SWITZERLAND_JOB_OS",
            agent_id="AGENT:V2-SHADOW-BRIDGE",
            session_id=session_id,
            workstream_id="WORKSTREAM:GRAPH-REFACTOR-V2",
            objective_id="OBJECTIVE:CRM-NEXT-SHADOW",
            correlation_id=f"CORRELATION:{stable_digest(cycle_id)[:20]}",
            event_type=event_type,
            occurred_at=timestamp,
            main_sha=main_sha,
            base_sha=main_sha,
            branch="runtime-drill",
            authority_ceiling="READ_ONLY_RESEARCH",
            resource_scopes=("state:crm-next",),
            semantic_scopes=("crm:shadow",),
            payload=payload,
            causation_id=previous,
        )
        ledger.append(event)
        previous = event_id

    graph = TemporalHyperGraph()
    graph_nodes = (
        GraphNode(
            "PROJECT:SWITZERLAND_JOB_OS",
            "PROJECT",
            {"owner": "MISSION_COMMANDER"},
            authority=AuthorityStatus.VERIFIED,
        ),
        GraphNode(
            "G-0001",
            "NORTHSTAR",
            {"owner": "MISSION_COMMANDER"},
            authority=AuthorityStatus.VERIFIED,
        ),
        GraphNode(
            checkpoint_id,
            "CHECKPOINT",
            {"state": "OBSERVED", "owner": "MISSION_COMMANDER"},
            authority=AuthorityStatus.VERIFIED,
        ),
        GraphNode(
            work_item_id,
            "TASK",
            {
                "selected_route": selected_route,
                "next_route": next_route,
                "owner": "WAVE_TRANSACTION_ENGINE",
            },
            source_event="EVENT:V2-SHADOW:0002",
            source_commit=main_sha,
            authority=AuthorityStatus.EXECUTED,
        ),
        GraphNode(
            snapshot_id,
            "SOURCE_SNAPSHOT",
            {"authority_epoch": authority_epoch, "owner": "EVIDENCE_ENGINE"},
            source_event="EVENT:V2-SHADOW:0003",
            authority=AuthorityStatus.VERIFIED,
        ),
        GraphNode(
            session_id,
            "SESSION",
            {"state": "ACTIVE", "owner": "AGENT:V2-SHADOW-BRIDGE"},
            source_event="EVENT:V2-SHADOW:0001",
            authority=AuthorityStatus.EXECUTED,
        ),
        GraphNode(
            claim_id,
            "CLAIM",
            {"mode": "READ", "owner": session_id},
            source_event="EVENT:V2-SHADOW:0001",
            authority=AuthorityStatus.EXECUTED,
        ),
        GraphNode(
            "EVIDENCE:V2-SHADOW-INPUT",
            "EVIDENCE",
            {"digest": stable_digest(safe_input), "owner": "EVIDENCE_ENGINE"},
            source_event="EVENT:V2-SHADOW:0004",
            authority=AuthorityStatus.VERIFIED,
        ),
        GraphNode(
            "NEXT:V2-SHADOW",
            "OUTCOME",
            {"route": next_route, "owner": "MISSION_COMMANDER"},
            source_event="EVENT:V2-SHADOW:0007",
            authority=AuthorityStatus.EXECUTED,
        ),
    )
    for item in graph_nodes:
        graph.add_node(item)
    graph_edges = (
        GraphEdge(
            "EDGE:V2-SHADOW:01",
            "CONTAINS",
            "PROJECT:SWITZERLAND_JOB_OS",
            "G-0001",
            authority=AuthorityStatus.VERIFIED,
        ),
        GraphEdge(
            "EDGE:V2-SHADOW:02",
            "CONTAINS",
            "PROJECT:SWITZERLAND_JOB_OS",
            checkpoint_id,
            authority=AuthorityStatus.VERIFIED,
        ),
        GraphEdge(
            "EDGE:V2-SHADOW:03",
            "REQUIRES",
            checkpoint_id,
            work_item_id,
            authority=AuthorityStatus.EXECUTED,
        ),
        GraphEdge(
            "EDGE:V2-SHADOW:04",
            "EXECUTED_BY",
            work_item_id,
            session_id,
            authority=AuthorityStatus.EXECUTED,
        ),
        GraphEdge(
            "EDGE:V2-SHADOW:05",
            "CLAIMED_BY",
            work_item_id,
            claim_id,
            authority=AuthorityStatus.EXECUTED,
        ),
        GraphEdge(
            "EDGE:V2-SHADOW:06",
            "READS",
            work_item_id,
            snapshot_id,
            authority=AuthorityStatus.EXECUTED,
        ),
        GraphEdge(
            "EDGE:V2-SHADOW:07",
            "SUPPORTED_BY",
            work_item_id,
            "EVIDENCE:V2-SHADOW-INPUT",
            authority=AuthorityStatus.VERIFIED,
        ),
        GraphEdge(
            "EDGE:V2-SHADOW:08",
            "PRODUCES",
            work_item_id,
            "NEXT:V2-SHADOW",
            authority=AuthorityStatus.EXECUTED,
        ),
    )
    for item in graph_edges:
        graph.add_edge(item)
    graph.add_hyperedge(
        HyperEdge(
            "HYPEREDGE:V2-SHADOW:01",
            "SHADOW_EXECUTION",
            (
                HyperParticipant(work_item_id, "WORK_ITEM"),
                HyperParticipant(session_id, "EXECUTOR_SESSION"),
                HyperParticipant(snapshot_id, "SOURCE_SNAPSHOT"),
                HyperParticipant("EVIDENCE:V2-SHADOW-INPUT", "EVIDENCE"),
                HyperParticipant("NEXT:V2-SHADOW", "OUTCOME"),
            ),
            {
                "authority_ceiling": "READ_ONLY_RESEARCH",
                "authority_advanced": False,
            },
            source_event="EVENT:V2-SHADOW:0007",
            authority=AuthorityStatus.EXECUTED,
        )
    )
    graph_errors = graph.validate()
    if graph_errors:
        raise ValueError("shadow graph invalid: " + "; ".join(graph_errors))

    graph_payload = graph.to_dict()
    context = ContextPack(
        schema_version="CONTEXTPACK-V2-SHADOW",
        project_id="PROJECT:SWITZERLAND_JOB_OS",
        revision=f"SHADOW-{stable_digest([main_sha, cycle_id])[:16]}",
        generated_at=timestamp,
        main_sha=main_sha,
        authority_epoch=authority_epoch,
        authority_manifest=authority_parent,
        event_watermark=ledger.watermark,
        projection_revision=graph_payload["graph_digest"],
        contract_versions={"MEP": "2.0", "WOP": "1.1", "HGA": "2.0"},
        active_barriers=tuple(str(item) for item in next_payload.get("hard_blockers", ())),
        active_claims=(
            {
                "claim_id": claim_id,
                "session_id": session_id,
                "mode": "READ",
            },
        ),
        verified_work=("read-only CRM NEXT shadow execution",),
        unverified_work=("operational authority migration",),
        next_safe_actions=(next_route,),
        source_digests={
            "input": stable_digest(safe_input),
            "graph": graph_payload["graph_digest"],
            "ledger": stable_digest(
                [event.to_dict() for event in ledger.events]
            ),
        },
        payload={
            "cycle_id": cycle_id,
            "checkpoint_id": checkpoint_id,
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
        },
    ).signed()

    return ShadowExecutionResult(
        schema_version="GRAPH_V2_CRM_SHADOW_1",
        state="PASS",
        main_sha=main_sha,
        session_id=session_id,
        work_item_id=work_item_id,
        graph=graph_payload,
        event_ledger_jsonl=ledger.to_jsonl(),
        event_watermark=ledger.watermark,
        contextpack=context.to_dict(),
        next_route=next_route,
        assertions=(
            "real public-safe NEXT input consumed",
            "unique session and read-only claim created",
            "causal event ledger verifies",
            "typed graph and hyperedge validate",
            "ContextPack binds main SHA watermark and projection revision",
            "authority and H-ID allocation remain forbidden",
            "outbound remains closed",
        ),
    )

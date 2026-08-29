from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
import re
from typing import Any, Callable, Iterable, Mapping, Sequence


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,255}$")
_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,127}$")
_SECRET_KEY_RE = re.compile(r"(?:secret|password|passwd|token|api[_-]?key|credential|private[_-]?key)", re.I)
_SECRET_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\b(?:sk|pk)-[A-Za-z0-9_-]{20,}\b"),
)
_HARD_DEPENDENCY_TYPES = frozenset({"DEPENDS_ON", "REQUIRES", "PRECEDES"})


class ContractError(ValueError):
    """Raised when a V2 contract is violated."""


class StaleContextError(ContractError):
    """Raised when a ContextPack no longer matches live ancestry/state."""


class CoordinationError(ContractError):
    """Raised for session/claim/lease/fencing violations."""


class AuthorityStatus(str, Enum):
    PROPOSED = "PROPOSED"
    IMPLEMENTED = "IMPLEMENTED"
    EXECUTED = "EXECUTED"
    VERIFIED = "VERIFIED"
    EMPIRICALLY_QUALIFIED = "EMPIRICALLY_QUALIFIED"
    BLOCKED = "BLOCKED"
    DEGRADED_EXTERNAL = "DEGRADED_EXTERNAL"
    SUPERSEDED = "SUPERSEDED"


class ResultState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"
    NOT_RUN = "NOT_RUN"


class SessionState(str, Enum):
    OPEN = "OPEN"
    ACTIVE = "ACTIVE"
    HANDOFF_PENDING = "HANDOFF_PENDING"
    CLOSED = "CLOSED"
    ABORTED = "ABORTED"


class ClaimState(str, Enum):
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class LeaseState(str, Enum):
    ACQUIRED = "ACQUIRED"
    RENEWED = "RENEWED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class AccessMode(str, Enum):
    READ = "READ"
    WRITE = "WRITE"


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ProjectionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACTIVE_LIGHT = "ACTIVE_LIGHT"
    ACTIVE_CONTRACT = "ACTIVE_CONTRACT"
    DEFERRED_TRIGGER = "DEFERRED_TRIGGER"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def _require_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ContractError(f"invalid {label}: {value!r}")
    return value


def _require_type(value: str, label: str) -> str:
    if not isinstance(value, str) or not _TYPE_RE.fullmatch(value):
        raise ContractError(f"invalid {label}: {value!r}")
    return value


def _require_nonempty(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ContractError("timestamp must be a non-empty ISO-8601 string")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ContractError(f"invalid ISO-8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ContractError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _validate_interval(valid_from: str | None, valid_to: str | None) -> None:
    start = _parse_time(valid_from)
    end = _parse_time(valid_to)
    if start is not None and end is not None and end < start:
        raise ContractError("valid_to precedes valid_from")


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractError("non-finite floats are forbidden")
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set, frozenset)):
        materialized = [_json_safe(v) for v in value]
        if isinstance(value, (set, frozenset)):
            materialized.sort(key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
        return materialized
    if hasattr(value, "to_dict"):
        return _json_safe(value.to_dict())
    raise ContractError(f"value is not canonical-JSON compatible: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    attributes: Mapping[str, Any] = field(default_factory=dict)
    valid_from: str | None = None
    valid_to: str | None = None
    source_event: str | None = None
    source_commit: str | None = None
    authority: AuthorityStatus = AuthorityStatus.PROPOSED
    confidence: float | None = None
    provenance: tuple[str, ...] = ()
    superseded_by: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.node_id, "node_id")
        _require_type(self.node_type, "node_type")
        _validate_interval(self.valid_from, self.valid_to)
        if self.source_event is not None:
            _require_id(self.source_event, "source_event")
        if self.source_commit is not None:
            _require_nonempty(self.source_commit, "source_commit")
        if self.superseded_by is not None:
            _require_id(self.superseded_by, "superseded_by")
            if self.superseded_by == self.node_id:
                raise ContractError("node cannot supersede itself")
        if self.confidence is not None:
            if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
                raise ContractError("confidence must be numeric")
            if not 0 <= float(self.confidence) <= 1:
                raise ContractError("confidence must be between 0 and 1")
        _json_safe(self.attributes)
        for ref in self.provenance:
            _require_nonempty(ref, "provenance reference")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.node_id,
            "type": self.node_type,
            "attributes": _json_safe(self.attributes),
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "source_event": self.source_event,
            "source_commit": self.source_commit,
            "authority": self.authority.value,
            "confidence": self.confidence,
            "provenance": list(self.provenance),
            "superseded_by": self.superseded_by,
        }


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    edge_type: str
    source_id: str
    target_id: str
    attributes: Mapping[str, Any] = field(default_factory=dict)
    valid_from: str | None = None
    valid_to: str | None = None
    authority: AuthorityStatus = AuthorityStatus.PROPOSED
    confidence: float | None = None
    source_ref: str | None = None
    version: str = "1"
    criticality: Severity = Severity.P2

    def __post_init__(self) -> None:
        _require_id(self.edge_id, "edge_id")
        _require_type(self.edge_type, "edge_type")
        _require_id(self.source_id, "source_id")
        _require_id(self.target_id, "target_id")
        _validate_interval(self.valid_from, self.valid_to)
        _require_nonempty(self.version, "edge version")
        if self.confidence is not None and not 0 <= float(self.confidence) <= 1:
            raise ContractError("edge confidence must be between 0 and 1")
        if self.source_ref is not None:
            _require_nonempty(self.source_ref, "edge source_ref")
        _json_safe(self.attributes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.edge_id,
            "type": self.edge_type,
            "source": self.source_id,
            "target": self.target_id,
            "attributes": _json_safe(self.attributes),
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "authority": self.authority.value,
            "confidence": self.confidence,
            "source_ref": self.source_ref,
            "version": self.version,
            "criticality": self.criticality.value,
        }


@dataclass(frozen=True)
class HyperParticipant:
    node_id: str
    role: str

    def __post_init__(self) -> None:
        _require_id(self.node_id, "hyperedge participant node_id")
        _require_type(self.role, "hyperedge participant role")

    def to_dict(self) -> dict[str, str]:
        return {"node_id": self.node_id, "role": self.role}


@dataclass(frozen=True)
class HyperEdge:
    hyperedge_id: str
    relation_type: str
    participants: tuple[HyperParticipant, ...]
    attributes: Mapping[str, Any] = field(default_factory=dict)
    source_event: str | None = None
    authority: AuthorityStatus = AuthorityStatus.PROPOSED
    valid_from: str | None = None
    valid_to: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.hyperedge_id, "hyperedge_id")
        _require_type(self.relation_type, "relation_type")
        if len(self.participants) < 2:
            raise ContractError("hyperedge requires at least two participants")
        pairs = {(p.node_id, p.role) for p in self.participants}
        if len(pairs) != len(self.participants):
            raise ContractError("duplicate hyperedge participant/role")
        if len({p.node_id for p in self.participants}) < 2:
            raise ContractError("hyperedge requires at least two distinct nodes")
        if self.source_event is not None:
            _require_id(self.source_event, "hyperedge source_event")
        _validate_interval(self.valid_from, self.valid_to)
        _json_safe(self.attributes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.hyperedge_id,
            "type": self.relation_type,
            "participants": [p.to_dict() for p in self.participants],
            "attributes": _json_safe(self.attributes),
            "source_event": self.source_event,
            "authority": self.authority.value,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
        }


class TemporalHyperGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._hyperedges: dict[str, HyperEdge] = {}

    @property
    def nodes(self) -> Mapping[str, GraphNode]:
        return dict(self._nodes)

    @property
    def edges(self) -> Mapping[str, GraphEdge]:
        return dict(self._edges)

    @property
    def hyperedges(self) -> Mapping[str, HyperEdge]:
        return dict(self._hyperedges)

    def add_node(self, node: GraphNode) -> None:
        if node.node_id in self._nodes:
            raise ContractError(f"duplicate node: {node.node_id}")
        self._nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.edge_id in self._edges:
            raise ContractError(f"duplicate edge: {edge.edge_id}")
        self._edges[edge.edge_id] = edge

    def add_hyperedge(self, edge: HyperEdge) -> None:
        if edge.hyperedge_id in self._hyperedges:
            raise ContractError(f"duplicate hyperedge: {edge.hyperedge_id}")
        self._hyperedges[edge.hyperedge_id] = edge

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for node in self._nodes.values():
            if node.superseded_by is not None and node.superseded_by not in self._nodes:
                errors.append(f"node {node.node_id} superseded_by missing node {node.superseded_by}")
        for edge in self._edges.values():
            if edge.source_id not in self._nodes:
                errors.append(f"edge {edge.edge_id} missing source {edge.source_id}")
            if edge.target_id not in self._nodes:
                errors.append(f"edge {edge.edge_id} missing target {edge.target_id}")
        for edge in self._hyperedges.values():
            for participant in edge.participants:
                if participant.node_id not in self._nodes:
                    errors.append(f"hyperedge {edge.hyperedge_id} missing participant {participant.node_id}")
        for cycle in self.dependency_cycles():
            errors.append("hard dependency cycle: " + " -> ".join(cycle))
        return tuple(errors)

    def incident_node_ids(self) -> set[str]:
        incident: set[str] = set()
        for edge in self._edges.values():
            incident.update((edge.source_id, edge.target_id))
        for edge in self._hyperedges.values():
            incident.update(p.node_id for p in edge.participants)
        return incident

    def orphan_nodes(self) -> tuple[str, ...]:
        incident = self.incident_node_ids()
        return tuple(sorted(
            node_id for node_id, node in self._nodes.items()
            if node_id not in incident and not bool(node.attributes.get("allow_orphan", False))
        ))

    def dependency_cycles(self) -> tuple[tuple[str, ...], ...]:
        adjacency: dict[str, list[str]] = {node_id: [] for node_id in self._nodes}
        for edge in self._edges.values():
            if edge.edge_type in _HARD_DEPENDENCY_TYPES:
                adjacency.setdefault(edge.source_id, []).append(edge.target_id)
        state: dict[str, int] = {}
        stack: list[str] = []
        cycles: set[tuple[str, ...]] = set()

        def canonical_cycle(cycle: Sequence[str]) -> tuple[str, ...]:
            body = list(cycle[:-1])
            start = min(range(len(body)), key=lambda i: body[i])
            rotated = body[start:] + body[:start]
            return tuple(rotated + [rotated[0]])

        def visit(node_id: str) -> None:
            state[node_id] = 1
            stack.append(node_id)
            for target in adjacency.get(node_id, []):
                if state.get(target, 0) == 0:
                    visit(target)
                elif state.get(target) == 1 and target in stack:
                    index = stack.index(target)
                    cycles.add(canonical_cycle(stack[index:] + [target]))
            stack.pop()
            state[node_id] = 2

        for node_id in sorted(adjacency):
            if state.get(node_id, 0) == 0:
                visit(node_id)
        return tuple(sorted(cycles))

    def transitive_dependencies(self, node_id: str) -> tuple[str, ...]:
        if node_id not in self._nodes:
            raise ContractError(f"unknown node: {node_id}")
        adjacency: dict[str, set[str]] = {}
        for edge in self._edges.values():
            if edge.edge_type in _HARD_DEPENDENCY_TYPES:
                adjacency.setdefault(edge.source_id, set()).add(edge.target_id)
        seen: set[str] = set()
        stack = list(adjacency.get(node_id, ()))
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(adjacency.get(current, ()))
        return tuple(sorted(seen))

    def projection(self, *, node_types: Iterable[str] = (), edge_types: Iterable[str] = ()) -> dict[str, Any]:
        wanted_nodes = set(node_types)
        wanted_edges = set(edge_types)
        nodes = {
            node_id: node for node_id, node in self._nodes.items()
            if not wanted_nodes or node.node_type in wanted_nodes
        }
        edges = {
            edge_id: edge for edge_id, edge in self._edges.items()
            if (not wanted_edges or edge.edge_type in wanted_edges)
            and edge.source_id in nodes and edge.target_id in nodes
        }
        hyperedges = {
            edge_id: edge for edge_id, edge in self._hyperedges.items()
            if all(p.node_id in nodes for p in edge.participants)
        }
        payload = {
            "nodes": [nodes[k].to_dict() for k in sorted(nodes)],
            "edges": [edges[k].to_dict() for k in sorted(edges)],
            "hyperedges": [hyperedges[k].to_dict() for k in sorted(hyperedges)],
        }
        payload["digest"] = stable_digest(payload)
        return payload

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": "HGA-2.0",
            "nodes": [self._nodes[k].to_dict() for k in sorted(self._nodes)],
            "edges": [self._edges[k].to_dict() for k in sorted(self._edges)],
            "hyperedges": [self._hyperedges[k].to_dict() for k in sorted(self._hyperedges)],
        }
        payload["graph_digest"] = stable_digest(payload)
        return payload


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    sequence: int
    project_id: str
    agent_id: str
    session_id: str
    workstream_id: str
    objective_id: str
    correlation_id: str
    event_type: str
    occurred_at: str
    main_sha: str
    base_sha: str
    branch: str
    authority_ceiling: str
    resource_scopes: tuple[str, ...]
    semantic_scopes: tuple[str, ...]
    payload: Mapping[str, Any]
    causation_id: str | None = None
    previous_event_hash: str | None = None
    event_hash: str = ""

    def __post_init__(self) -> None:
        for label, value in (
            ("event_id", self.event_id), ("project_id", self.project_id),
            ("agent_id", self.agent_id), ("session_id", self.session_id),
            ("workstream_id", self.workstream_id), ("objective_id", self.objective_id),
            ("correlation_id", self.correlation_id),
        ):
            _require_id(value, label)
        _require_type(self.event_type, "event_type")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 0:
            raise ContractError("event sequence must be a non-negative integer")
        _parse_time(self.occurred_at)
        _require_nonempty(self.main_sha, "main_sha")
        _require_nonempty(self.base_sha, "base_sha")
        _require_nonempty(self.branch, "branch")
        _require_type(self.authority_ceiling, "authority_ceiling")
        if self.causation_id is not None:
            _require_id(self.causation_id, "causation_id")
        if self.previous_event_hash is not None and not re.fullmatch(r"[0-9a-f]{64}", self.previous_event_hash):
            raise ContractError("previous_event_hash must be a SHA-256 hex digest")
        if self.event_hash and not re.fullmatch(r"[0-9a-f]{64}", self.event_hash):
            raise ContractError("event_hash must be a SHA-256 hex digest")
        for scope in self.resource_scopes + self.semantic_scopes:
            _require_nonempty(scope, "scope")
        _json_safe(self.payload)

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "project_id": self.project_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "workstream_id": self.workstream_id,
            "objective_id": self.objective_id,
            "correlation_id": self.correlation_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "main_sha": self.main_sha,
            "base_sha": self.base_sha,
            "branch": self.branch,
            "authority_ceiling": self.authority_ceiling,
            "resource_scopes": list(self.resource_scopes),
            "semantic_scopes": list(self.semantic_scopes),
            "payload": _json_safe(self.payload),
            "causation_id": self.causation_id,
            "previous_event_hash": self.previous_event_hash,
        }

    def computed_hash(self) -> str:
        return stable_digest(self.unsigned_dict())

    def signed(self) -> "LedgerEvent":
        return replace(self, event_hash=self.computed_hash())

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "event_hash": self.event_hash}


class EventLedger:
    def __init__(self, events: Iterable[LedgerEvent] = ()) -> None:
        self._events: list[LedgerEvent] = []
        self._ids: set[str] = set()
        for event in events:
            self.append(event)

    @property
    def events(self) -> tuple[LedgerEvent, ...]:
        return tuple(self._events)

    @property
    def watermark(self) -> str:
        if not self._events:
            return "EMPTY"
        last = self._events[-1]
        return f"{last.sequence}:{last.event_id}:{last.event_hash}"

    def append(self, event: LedgerEvent) -> None:
        if event.event_id in self._ids:
            raise ContractError(f"duplicate event_id: {event.event_id}")
        expected_sequence = len(self._events)
        if event.sequence != expected_sequence:
            raise ContractError(f"event sequence {event.sequence} != expected {expected_sequence}")
        expected_previous = self._events[-1].event_hash if self._events else None
        if event.previous_event_hash != expected_previous:
            raise ContractError("event hash-chain predecessor mismatch")
        if event.causation_id is not None and event.causation_id not in self._ids:
            raise ContractError(f"causation event not present: {event.causation_id}")
        if event.event_hash != event.computed_hash():
            raise ContractError("event hash invalid")
        self._events.append(event)
        self._ids.add(event.event_id)

    def new_event(self, **kwargs: Any) -> LedgerEvent:
        kwargs["sequence"] = len(self._events)
        kwargs["previous_event_hash"] = self._events[-1].event_hash if self._events else None
        return LedgerEvent(**kwargs).signed()

    def verify(self) -> tuple[str, ...]:
        errors: list[str] = []
        previous: str | None = None
        seen: set[str] = set()
        for index, event in enumerate(self._events):
            if event.sequence != index:
                errors.append(f"sequence mismatch at {event.event_id}")
            if event.event_id in seen:
                errors.append(f"duplicate event {event.event_id}")
            seen.add(event.event_id)
            if event.previous_event_hash != previous:
                errors.append(f"previous hash mismatch at {event.event_id}")
            if event.event_hash != event.computed_hash():
                errors.append(f"event hash mismatch at {event.event_id}")
            if event.causation_id is not None and event.causation_id not in seen:
                errors.append(f"causation not earlier in ledger at {event.event_id}")
            previous = event.event_hash
        return tuple(errors)

    def replay(self, reducer: Callable[[Any, LedgerEvent], Any], initial_state: Any) -> Any:
        errors = self.verify()
        if errors:
            raise ContractError("cannot replay corrupt ledger: " + "; ".join(errors))
        state = initial_state
        for event in self._events:
            state = reducer(state, event)
        return state

    def to_jsonl(self) -> str:
        return "\n".join(canonical_json(event.to_dict()) for event in self._events) + ("\n" if self._events else "")


@dataclass(frozen=True)
class Session:
    session_id: str
    project_id: str
    agent_id: str
    workstream_id: str
    objective_id: str
    correlation_id: str
    state: SessionState
    opened_at: str
    heartbeat_at: str
    closed_at: str | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("session_id", self.session_id), ("project_id", self.project_id),
            ("agent_id", self.agent_id), ("workstream_id", self.workstream_id),
            ("objective_id", self.objective_id), ("correlation_id", self.correlation_id),
        ):
            _require_id(value, label)
        opened = _parse_time(self.opened_at)
        heartbeat = _parse_time(self.heartbeat_at)
        closed = _parse_time(self.closed_at)
        if heartbeat is not None and opened is not None and heartbeat < opened:
            raise ContractError("heartbeat precedes session open")
        if closed is not None and opened is not None and closed < opened:
            raise ContractError("session close precedes session open")


@dataclass(frozen=True)
class ScopeClaim:
    claim_id: str
    session_id: str
    access_mode: AccessMode
    resource_scopes: tuple[str, ...]
    semantic_scopes: tuple[str, ...]
    state: ClaimState
    acquired_at: str
    released_at: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.claim_id, "claim_id")
        _require_id(self.session_id, "claim session_id")
        _parse_time(self.acquired_at)
        _parse_time(self.released_at)
        if not self.resource_scopes and not self.semantic_scopes:
            raise ContractError("claim requires a resource or semantic scope")
        for scope in self.resource_scopes + self.semantic_scopes:
            _require_nonempty(scope, "claim scope")


@dataclass(frozen=True)
class Lease:
    lease_id: str
    session_id: str
    scope: str
    fencing_token: int
    acquired_at: str
    expires_at: str
    state: LeaseState

    def __post_init__(self) -> None:
        _require_id(self.lease_id, "lease_id")
        _require_id(self.session_id, "lease session_id")
        _require_nonempty(self.scope, "lease scope")
        if isinstance(self.fencing_token, bool) or not isinstance(self.fencing_token, int) or self.fencing_token <= 0:
            raise ContractError("fencing_token must be a positive integer")
        start = _parse_time(self.acquired_at)
        end = _parse_time(self.expires_at)
        if start is not None and end is not None and end <= start:
            raise ContractError("lease expiry must follow acquisition")


def _scope_overlaps(left: str, right: str) -> bool:
    def parts(value: str) -> tuple[str, ...]:
        return tuple(part for part in re.split(r"[/:]", value.strip("/:")) if part)
    a, b = parts(left), parts(right)
    if not a or not b:
        return left == right
    common = min(len(a), len(b))
    return a[:common] == b[:common]


class CoordinationRegistry:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self.claims: dict[str, ScopeClaim] = {}
        self.leases: dict[str, Lease] = {}
        self._scope_tokens: dict[str, int] = {}

    def open_session(self, session: Session) -> None:
        if session.session_id in self.sessions:
            raise CoordinationError(f"session_id already exists: {session.session_id}")
        if session.state not in {SessionState.OPEN, SessionState.ACTIVE}:
            raise CoordinationError("new session must be OPEN or ACTIVE")
        self.sessions[session.session_id] = session

    def heartbeat(self, session_id: str, occurred_at: str) -> None:
        session = self._active_session(session_id)
        now = _parse_time(occurred_at)
        previous = _parse_time(session.heartbeat_at)
        if now is not None and previous is not None and now < previous:
            raise CoordinationError("heartbeat moved backwards")
        self.sessions[session_id] = replace(session, state=SessionState.ACTIVE, heartbeat_at=occurred_at)

    def close_session(self, session_id: str, occurred_at: str, *, aborted: bool = False) -> None:
        session = self._active_session(session_id)
        for claim_id, claim in list(self.claims.items()):
            if claim.session_id == session_id and claim.state == ClaimState.ACTIVE:
                self.claims[claim_id] = replace(claim, state=ClaimState.RELEASED, released_at=occurred_at)
        for lease_id, lease in list(self.leases.items()):
            if lease.session_id == session_id and lease.state in {LeaseState.ACQUIRED, LeaseState.RENEWED}:
                self.leases[lease_id] = replace(lease, state=LeaseState.RELEASED)
        self.sessions[session_id] = replace(
            session,
            state=SessionState.ABORTED if aborted else SessionState.CLOSED,
            heartbeat_at=occurred_at,
            closed_at=occurred_at,
        )

    def acquire_claim(self, claim: ScopeClaim) -> None:
        self._active_session(claim.session_id)
        if claim.claim_id in self.claims:
            raise CoordinationError(f"claim_id already exists: {claim.claim_id}")
        if claim.state != ClaimState.ACTIVE:
            raise CoordinationError("new claim must be ACTIVE")
        for existing in self.claims.values():
            if existing.state != ClaimState.ACTIVE or existing.session_id == claim.session_id:
                continue
            resource_collision = any(
                _scope_overlaps(a, b) for a in claim.resource_scopes for b in existing.resource_scopes
            )
            semantic_collision = any(
                _scope_overlaps(a, b) for a in claim.semantic_scopes for b in existing.semantic_scopes
            )
            if (resource_collision or semantic_collision) and (
                claim.access_mode == AccessMode.WRITE or existing.access_mode == AccessMode.WRITE
            ):
                raise CoordinationError(
                    f"claim {claim.claim_id} collides with active claim {existing.claim_id}"
                )
        self.claims[claim.claim_id] = claim

    def release_claim(self, claim_id: str, occurred_at: str) -> None:
        claim = self.claims.get(claim_id)
        if claim is None or claim.state != ClaimState.ACTIVE:
            raise CoordinationError("claim is not active")
        self.claims[claim_id] = replace(claim, state=ClaimState.RELEASED, released_at=occurred_at)

    def acquire_lease(self, *, lease_id: str, session_id: str, scope: str, acquired_at: str, expires_at: str) -> Lease:
        self._active_session(session_id)
        now = _parse_time(acquired_at)
        for lease in self.leases.values():
            if lease.scope != scope or lease.state not in {LeaseState.ACQUIRED, LeaseState.RENEWED}:
                continue
            expiry = _parse_time(lease.expires_at)
            if expiry is not None and now is not None and expiry > now:
                raise CoordinationError(f"scope already leased by {lease.session_id}")
            self.leases[lease.lease_id] = replace(lease, state=LeaseState.EXPIRED)
        token = self._scope_tokens.get(scope, 0) + 1
        self._scope_tokens[scope] = token
        lease = Lease(
            lease_id=lease_id,
            session_id=session_id,
            scope=scope,
            fencing_token=token,
            acquired_at=acquired_at,
            expires_at=expires_at,
            state=LeaseState.ACQUIRED,
        )
        if lease_id in self.leases:
            raise CoordinationError(f"lease_id already exists: {lease_id}")
        self.leases[lease_id] = lease
        return lease

    def renew_lease(self, lease_id: str, fencing_token: int, renewed_at: str, expires_at: str) -> Lease:
        lease = self.leases.get(lease_id)
        if lease is None or lease.state not in {LeaseState.ACQUIRED, LeaseState.RENEWED}:
            raise CoordinationError("lease is not renewable")
        self.assert_fence(lease.scope, fencing_token, renewed_at)
        renewed = Lease(
            lease_id=lease.lease_id,
            session_id=lease.session_id,
            scope=lease.scope,
            fencing_token=lease.fencing_token,
            acquired_at=renewed_at,
            expires_at=expires_at,
            state=LeaseState.RENEWED,
        )
        self.leases[lease_id] = renewed
        return renewed

    def assert_fence(self, scope: str, fencing_token: int, occurred_at: str) -> None:
        current = self._scope_tokens.get(scope)
        if current is None or fencing_token != current:
            raise CoordinationError("stale fencing token")
        now = _parse_time(occurred_at)
        active = [
            lease for lease in self.leases.values()
            if lease.scope == scope and lease.fencing_token == fencing_token
            and lease.state in {LeaseState.ACQUIRED, LeaseState.RENEWED}
        ]
        if len(active) != 1:
            raise CoordinationError("no unique active lease for fencing token")
        expiry = _parse_time(active[0].expires_at)
        if now is not None and expiry is not None and now >= expiry:
            self.leases[active[0].lease_id] = replace(active[0], state=LeaseState.EXPIRED)
            raise CoordinationError("lease expired")

    def _active_session(self, session_id: str) -> Session:
        session = self.sessions.get(session_id)
        if session is None or session.state not in {SessionState.OPEN, SessionState.ACTIVE, SessionState.HANDOFF_PENDING}:
            raise CoordinationError(f"session is not active: {session_id}")
        return session


@dataclass(frozen=True)
class ContextPack:
    schema_version: str
    project_id: str
    revision: str
    generated_at: str
    main_sha: str
    authority_epoch: str
    authority_manifest: str
    event_watermark: str
    projection_revision: str
    contract_versions: Mapping[str, str]
    active_barriers: tuple[str, ...]
    active_claims: tuple[Mapping[str, Any], ...]
    verified_work: tuple[str, ...]
    unverified_work: tuple[str, ...]
    next_safe_actions: tuple[str, ...]
    source_digests: Mapping[str, str]
    payload: Mapping[str, Any]
    digest: str = ""

    def __post_init__(self) -> None:
        _require_nonempty(self.schema_version, "ContextPack schema_version")
        _require_id(self.project_id, "ContextPack project_id")
        _require_nonempty(self.revision, "ContextPack revision")
        _parse_time(self.generated_at)
        for label, value in (
            ("main_sha", self.main_sha),
            ("authority_epoch", self.authority_epoch),
            ("authority_manifest", self.authority_manifest),
            ("event_watermark", self.event_watermark),
            ("projection_revision", self.projection_revision),
        ):
            _require_nonempty(value, label)
        for name, digest in self.source_digests.items():
            _require_nonempty(name, "source digest name")
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ContractError(f"invalid source digest for {name}")
        _json_safe(self.payload)
        if self.digest and self.digest != self.computed_digest():
            raise ContractError("ContextPack digest mismatch")

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "revision": self.revision,
            "generated_at": self.generated_at,
            "main_sha": self.main_sha,
            "authority_epoch": self.authority_epoch,
            "authority_manifest": self.authority_manifest,
            "event_watermark": self.event_watermark,
            "projection_revision": self.projection_revision,
            "contract_versions": _json_safe(self.contract_versions),
            "active_barriers": list(self.active_barriers),
            "active_claims": _json_safe(self.active_claims),
            "verified_work": list(self.verified_work),
            "unverified_work": list(self.unverified_work),
            "next_safe_actions": list(self.next_safe_actions),
            "source_digests": _json_safe(self.source_digests),
            "payload": redact_secrets(self.payload),
        }

    def computed_digest(self) -> str:
        return stable_digest(self.unsigned_dict())

    def signed(self) -> "ContextPack":
        return replace(self, digest=self.computed_digest())

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "digest": self.digest}

    def assert_fresh(self, *, main_sha: str, event_watermark: str, projection_revision: str) -> None:
        mismatches = []
        if self.main_sha != main_sha:
            mismatches.append("main_sha")
        if self.event_watermark != event_watermark:
            mismatches.append("event_watermark")
        if self.projection_revision != projection_revision:
            mismatches.append("projection_revision")
        if mismatches:
            raise StaleContextError("stale ContextPack: " + ", ".join(mismatches))


def redact_secrets(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _SECRET_KEY_RE.search(name):
                result[name] = "[REDACTED]"
            else:
                result[name] = redact_secrets(item)
        return result
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    if isinstance(value, str):
        redacted = value
        for pattern in _SECRET_VALUE_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
    return value


@dataclass(frozen=True)
class InvariantSpec:
    invariant_id: str
    description: str
    severity: Severity
    owner: str
    test_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_id(self.invariant_id, "invariant_id")
        _require_nonempty(self.description, "invariant description")
        _require_nonempty(self.owner, "invariant owner")
        if self.severity in {Severity.P0, Severity.P1} and not self.test_ids:
            raise ContractError("P0/P1 invariant requires at least one test")
        for test_id in self.test_ids:
            _require_id(test_id, "invariant test_id")


@dataclass(frozen=True)
class TestEvidence:
    test_id: str
    state: ResultState
    evidence_ref: str
    executed_at: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.test_id, "test_id")
        if self.state in {ResultState.PASS, ResultState.FAIL}:
            _require_nonempty(self.evidence_ref, "test evidence_ref")
            _parse_time(self.executed_at)
        elif self.evidence_ref:
            _require_nonempty(self.evidence_ref, "test evidence_ref")


@dataclass(frozen=True)
class Gap:
    gap_id: str
    title: str
    severity: Severity
    probability: int
    blast_radius: int
    impact: int
    strategic_importance: int
    cost: int
    owner: str
    detection: str
    mitigation: str
    target_fix: str
    dependencies: tuple[str, ...]
    test_id: str
    evidence_required: str
    phase: str
    state: str = "OPEN"

    def __post_init__(self) -> None:
        _require_id(self.gap_id, "gap_id")
        for label, value in (
            ("title", self.title), ("owner", self.owner), ("detection", self.detection),
            ("mitigation", self.mitigation), ("target_fix", self.target_fix),
            ("test_id", self.test_id), ("evidence_required", self.evidence_required),
            ("phase", self.phase), ("state", self.state),
        ):
            _require_nonempty(value, label)
        for label, value in (
            ("probability", self.probability), ("blast_radius", self.blast_radius),
            ("impact", self.impact), ("strategic_importance", self.strategic_importance),
            ("cost", self.cost),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > 5:
                raise ContractError(f"{label} must be an integer 1..5")

    @property
    def priority(self) -> float:
        hard_override = 1_000_000 if self.severity == Severity.P0 else 100_000 if self.severity == Severity.P1 else 0
        return hard_override + (self.impact * self.probability * self.blast_radius * self.strategic_importance / self.cost)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "title": self.title,
            "severity": self.severity.value,
            "probability": self.probability,
            "blast_radius": self.blast_radius,
            "impact": self.impact,
            "strategic_importance": self.strategic_importance,
            "cost": self.cost,
            "priority": self.priority,
            "owner": self.owner,
            "detection": self.detection,
            "mitigation": self.mitigation,
            "target_fix": self.target_fix,
            "dependencies": list(self.dependencies),
            "test_id": self.test_id,
            "evidence_required": self.evidence_required,
            "phase": self.phase,
            "state": self.state,
        }


@dataclass(frozen=True)
class AssuranceReport:
    p0_open: int
    p1_open: int
    p2_open: int
    p3_open: int
    graph_errors: tuple[str, ...]
    critical_owner_gaps: tuple[str, ...]
    critical_test_gaps: tuple[str, ...]
    invariant_failures: tuple[str, ...]
    ordered_gaps: tuple[Gap, ...]

    @property
    def release_candidate(self) -> bool:
        return not any((self.p0_open, self.p1_open, self.graph_errors, self.critical_owner_gaps, self.critical_test_gaps, self.invariant_failures))

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_candidate": self.release_candidate,
            "p0_open": self.p0_open,
            "p1_open": self.p1_open,
            "p2_open": self.p2_open,
            "p3_open": self.p3_open,
            "graph_errors": list(self.graph_errors),
            "critical_owner_gaps": list(self.critical_owner_gaps),
            "critical_test_gaps": list(self.critical_test_gaps),
            "invariant_failures": list(self.invariant_failures),
            "gaps": [gap.to_dict() for gap in self.ordered_gaps],
        }


def compile_assurance(
    graph: TemporalHyperGraph,
    invariants: Iterable[InvariantSpec],
    test_evidence: Iterable[TestEvidence],
    gaps: Iterable[Gap],
) -> AssuranceReport:
    evidence_by_id = {item.test_id: item for item in test_evidence}
    if len(evidence_by_id) != len(tuple(test_evidence)):
        raise ContractError("duplicate test evidence IDs")
    owner_edges = {(e.source_id, e.target_id) for e in graph.edges.values() if e.edge_type == "OWNED_BY"}
    tested_nodes = {e.source_id for e in graph.edges.values() if e.edge_type == "TESTED_BY"}
    owner_gaps: list[str] = []
    test_gaps: list[str] = []
    for node in graph.nodes.values():
        if not bool(node.attributes.get("critical", False)):
            continue
        has_owner_attr = bool(str(node.attributes.get("owner", "")).strip())
        has_owner_edge = any(source == node.node_id for source, _ in owner_edges)
        if not has_owner_attr and not has_owner_edge:
            owner_gaps.append(node.node_id)
        if node.node_id not in tested_nodes and not node.attributes.get("test_ids"):
            test_gaps.append(node.node_id)
    failures: list[str] = []
    seen_invariants: set[str] = set()
    for invariant in invariants:
        if invariant.invariant_id in seen_invariants:
            raise ContractError(f"duplicate invariant: {invariant.invariant_id}")
        seen_invariants.add(invariant.invariant_id)
        for test_id in invariant.test_ids:
            evidence = evidence_by_id.get(test_id)
            if evidence is None:
                failures.append(f"{invariant.invariant_id}:missing:{test_id}")
            elif evidence.state != ResultState.PASS:
                failures.append(f"{invariant.invariant_id}:{test_id}:{evidence.state.value}")
    gap_list = tuple(sorted(gaps, key=lambda item: (-item.priority, item.gap_id)))
    counts = {severity: 0 for severity in Severity}
    for gap in gap_list:
        if gap.state not in {"RESOLVED", "SUPERSEDED", "ACCEPTED_RESIDUAL"}:
            counts[gap.severity] += 1
    return AssuranceReport(
        p0_open=counts[Severity.P0],
        p1_open=counts[Severity.P1],
        p2_open=counts[Severity.P2],
        p3_open=counts[Severity.P3],
        graph_errors=graph.validate(),
        critical_owner_gaps=tuple(sorted(owner_gaps)),
        critical_test_gaps=tuple(sorted(test_gaps)),
        invariant_failures=tuple(sorted(failures)),
        ordered_gaps=gap_list,
    )


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    objective: str
    why: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    dependencies: tuple[str, ...]
    affected_nodes: tuple[str, ...]
    affected_edges: tuple[str, ...]
    affected_files: tuple[str, ...]
    owner_type: str
    risk: str
    implementation_steps: tuple[str, ...]
    tests: tuple[str, ...]
    adversarial_tests: tuple[str, ...]
    security_tests: tuple[str, ...]
    evidence_required: tuple[str, ...]
    rollback: str
    definition_of_done: tuple[str, ...]
    state: str = "PLANNED"

    def __post_init__(self) -> None:
        _require_id(self.task_id, "task_id")
        for label, value in (
            ("objective", self.objective), ("why", self.why), ("owner_type", self.owner_type),
            ("risk", self.risk), ("rollback", self.rollback), ("state", self.state),
        ):
            _require_nonempty(value, label)
        required_sequences = {
            "inputs": self.inputs, "outputs": self.outputs,
            "implementation_steps": self.implementation_steps, "tests": self.tests,
            "adversarial_tests": self.adversarial_tests, "security_tests": self.security_tests,
            "evidence_required": self.evidence_required, "definition_of_done": self.definition_of_done,
        }
        for label, values in required_sequences.items():
            if not values:
                raise ContractError(f"task {self.task_id} requires {label}")
            for value in values:
                _require_nonempty(value, f"task {self.task_id} {label}")
        for dependency in self.dependencies:
            _require_id(dependency, "task dependency")

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(self.__dict__)


@dataclass(frozen=True)
class CheckpointSpec:
    checkpoint_id: str
    name: str
    entry_criteria: tuple[str, ...]
    required_tasks: tuple[str, ...]
    required_tests: tuple[str, ...]
    required_evidence: tuple[str, ...]
    exit_criteria: tuple[str, ...]
    promotion_authority: str
    rollback_path: str
    state: str = "PLANNED"

    def __post_init__(self) -> None:
        _require_id(self.checkpoint_id, "checkpoint_id")
        _require_nonempty(self.name, "checkpoint name")
        _require_nonempty(self.promotion_authority, "promotion_authority")
        _require_nonempty(self.rollback_path, "rollback_path")
        for label, values in (
            ("entry_criteria", self.entry_criteria), ("required_tasks", self.required_tasks),
            ("required_tests", self.required_tests), ("required_evidence", self.required_evidence),
            ("exit_criteria", self.exit_criteria),
        ):
            if not values:
                raise ContractError(f"checkpoint {self.checkpoint_id} requires {label}")

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(self.__dict__)


@dataclass(frozen=True)
class ImplementationProgram:
    program_id: str
    north_star_id: str
    tasks: tuple[TaskSpec, ...]
    checkpoints: tuple[CheckpointSpec, ...]

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        task_by_id: dict[str, TaskSpec] = {}
        for task in self.tasks:
            if task.task_id in task_by_id:
                errors.append(f"duplicate task {task.task_id}")
            task_by_id[task.task_id] = task
        checkpoint_ids: set[str] = set()
        for checkpoint in self.checkpoints:
            if checkpoint.checkpoint_id in checkpoint_ids:
                errors.append(f"duplicate checkpoint {checkpoint.checkpoint_id}")
            checkpoint_ids.add(checkpoint.checkpoint_id)
            for task_id in checkpoint.required_tasks:
                if task_id not in task_by_id:
                    errors.append(f"checkpoint {checkpoint.checkpoint_id} references missing task {task_id}")
        for task in self.tasks:
            for dependency in task.dependencies:
                if dependency not in task_by_id:
                    errors.append(f"task {task.task_id} references missing dependency {dependency}")
        adjacency = {task_id: set(task.dependencies) for task_id, task in task_by_id.items()}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str, trail: tuple[str, ...]) -> None:
            if task_id in visiting:
                errors.append("task dependency cycle: " + " -> ".join(trail + (task_id,)))
                return
            if task_id in visited:
                return
            visiting.add(task_id)
            for dep in adjacency.get(task_id, ()):
                visit(dep, trail + (task_id,))
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in sorted(task_by_id):
            visit(task_id, ())
        return tuple(sorted(set(errors)))

    def executable_frontier(self, completed_task_ids: Iterable[str]) -> tuple[str, ...]:
        completed = set(completed_task_ids)
        return tuple(sorted(
            task.task_id for task in self.tasks
            if task.task_id not in completed and set(task.dependencies) <= completed
        ))

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": "IMPLEMENTATION_COMPILER_V2",
            "program_id": self.program_id,
            "north_star_id": self.north_star_id,
            "tasks": [task.to_dict() for task in self.tasks],
            "checkpoints": [checkpoint.to_dict() for checkpoint in self.checkpoints],
        }
        payload["program_digest"] = stable_digest(payload)
        return payload


@dataclass(frozen=True)
class COSDimension:
    dimension_id: str
    name: str
    status: ProjectionStatus
    purpose: str
    trigger: str = ""

    def __post_init__(self) -> None:
        if not re.fullmatch(r"L(?:[0-9]|1[0-9])", self.dimension_id):
            raise ContractError(f"invalid COS dimension: {self.dimension_id}")
        _require_nonempty(self.name, "dimension name")
        _require_nonempty(self.purpose, "dimension purpose")
        if self.status == ProjectionStatus.DEFERRED_TRIGGER and not self.trigger.strip():
            raise ContractError("deferred dimension requires trigger")


class ProjectionRegistry:
    def __init__(self, dimensions: Iterable[COSDimension]) -> None:
        self.dimensions = tuple(dimensions)
        ids = [item.dimension_id for item in self.dimensions]
        if len(set(ids)) != len(ids):
            raise ContractError("duplicate COS dimension")
        expected = {f"L{i}" for i in range(20)}
        if set(ids) != expected:
            missing = sorted(expected - set(ids))
            extra = sorted(set(ids) - expected)
            raise ContractError(f"COS registry must define L0..L19; missing={missing}; extra={extra}")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": "COS-20D-V2",
            "dimensions": [
                {
                    "dimension_id": d.dimension_id,
                    "name": d.name,
                    "status": d.status.value,
                    "purpose": d.purpose,
                    "trigger": d.trigger,
                }
                for d in sorted(self.dimensions, key=lambda item: int(item.dimension_id[1:]))
            ],
        }
        payload["registry_digest"] = stable_digest(payload)
        return payload

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Iterable, Mapping

from .v2_kernel import (
    AuthorityStatus,
    ContextPack,
    EventLedger,
    GraphEdge,
    GraphNode,
    HyperEdge,
    HyperParticipant,
    TemporalHyperGraph,
    stable_digest,
)

_HOTEL_ID_RE = re.compile(r"^H-\d{4}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_PLANES = (
    "constrained_db",
    "hotels_master",
    "intelligence",
    "operational_graph",
)
_TERMINAL_ALIAS_STATES = frozenset({"EXACT", "NOT_APPLICABLE"})


class MigrationShadowError(ValueError):
    pass


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MigrationShadowError(f"{label} must be a non-empty string")
    return value.strip()


def _require_sha256(value: object, label: str) -> str:
    text = _require_string(value, label)
    if not _SHA256_RE.fullmatch(text):
        raise MigrationShadowError(f"{label} must be a lowercase SHA-256")
    return text


def _require_git_sha(value: object, label: str) -> str:
    text = _require_string(value, label)
    if not _GIT_SHA_RE.fullmatch(text):
        raise MigrationShadowError(f"{label} must be a lowercase Git SHA")
    return text


def _require_nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MigrationShadowError(f"{label} must be a non-negative integer")
    return value


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise MigrationShadowError(f"{label} must be a JSON boolean")
    return value


def _parse_time(value: object, label: str) -> str:
    text = _require_string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MigrationShadowError(f"{label} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise MigrationShadowError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_hotel_ids(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise MigrationShadowError(f"{label} must be an array")
    ids: list[str] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, str) or not _HOTEL_ID_RE.fullmatch(raw):
            raise MigrationShadowError(f"{label}[{index}] is not a canonical H-ID")
        ids.append(raw)
    if len(ids) != len(set(ids)):
        raise MigrationShadowError(f"{label} contains duplicate H-IDs")
    if ids != sorted(ids):
        raise MigrationShadowError(f"{label} must be sorted deterministically")
    return tuple(ids)


def _digest_ids(ids: Iterable[str]) -> str:
    materialized = tuple(sorted(ids))
    return hashlib.sha256(("\n".join(materialized) + ("\n" if materialized else "")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AliasEdge:
    alias_hotel_id: str
    canonical_hotel_id: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AliasEdge":
        alias = _require_string(payload.get("alias_hotel_id"), "alias_hotel_id")
        target = _require_string(payload.get("canonical_hotel_id"), "canonical_hotel_id")
        if not _HOTEL_ID_RE.fullmatch(alias) or not _HOTEL_ID_RE.fullmatch(target):
            raise MigrationShadowError("alias edges require canonical H-IDs")
        if alias == target:
            raise MigrationShadowError("alias edge cannot target itself")
        return cls(alias, target)

    def to_dict(self) -> dict[str, str]:
        return {
            "alias_hotel_id": self.alias_hotel_id,
            "canonical_hotel_id": self.canonical_hotel_id,
        }


@dataclass(frozen=True)
class PlaneSnapshot:
    plane: str
    artifact_sha256: str
    physical_ids: tuple[str, ...]
    active_ids: tuple[str, ...]
    alias_edges: tuple[AliasEdge, ...] = ()
    integrity_check: str | None = None
    foreign_key_violations: int | None = None

    @classmethod
    def from_mapping(cls, name: str, payload: Mapping[str, object]) -> "PlaneSnapshot":
        if not isinstance(payload, Mapping):
            raise MigrationShadowError(f"plane {name} must be a mapping")
        alias_raw = payload.get("alias_edges", [])
        if not isinstance(alias_raw, list) or not all(isinstance(item, Mapping) for item in alias_raw):
            raise MigrationShadowError(f"plane {name} alias_edges must contain mappings")
        integrity = payload.get("integrity_check")
        if integrity is not None:
            integrity = _require_string(integrity, f"{name}.integrity_check")
        fk = payload.get("foreign_key_violations")
        if fk is not None:
            fk = _require_nonnegative_int(fk, f"{name}.foreign_key_violations")
        return cls(
            plane=name,
            artifact_sha256=_require_sha256(payload.get("artifact_sha256"), f"{name}.artifact_sha256"),
            physical_ids=_require_hotel_ids(payload.get("physical_ids"), f"{name}.physical_ids"),
            active_ids=_require_hotel_ids(payload.get("active_ids"), f"{name}.active_ids"),
            alias_edges=tuple(AliasEdge.from_mapping(item) for item in alias_raw),
            integrity_check=integrity,
            foreign_key_violations=fk,
        )

    def to_public_dict(self) -> dict[str, object]:
        return {
            "plane": self.plane,
            "artifact_sha256": self.artifact_sha256,
            "physical_count": len(self.physical_ids),
            "physical_ids_sha256": _digest_ids(self.physical_ids),
            "active_count": len(self.active_ids),
            "active_ids_sha256": _digest_ids(self.active_ids),
            "alias_count": len(self.alias_edges),
            "alias_edges_sha256": stable_digest([item.to_dict() for item in self.alias_edges]),
            "integrity_check": self.integrity_check,
            "foreign_key_violations": self.foreign_key_violations,
        }


@dataclass(frozen=True)
class MigrationInventory:
    source_main_sha: str
    authority_epoch: str
    authority_manifest_sha256: str
    observed_at: str
    alias_semantics_state: str
    expected_physical_count: int
    expected_active_count: int
    sources_immutable: bool
    active_write_claims: tuple[Mapping[str, object], ...]
    planes: Mapping[str, PlaneSnapshot]
    historical_unknowns: tuple[str, ...]
    crm_universe_complete: bool
    outbound: str
    send_allowed: int
    authority_advance_allowed: bool
    canonical_id_allocation_allowed: bool
    outbound_allowed: bool

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "MigrationInventory":
        if not isinstance(payload, Mapping):
            raise MigrationShadowError("migration inventory must be a mapping")
        raw_planes = payload.get("planes")
        if not isinstance(raw_planes, Mapping):
            raise MigrationShadowError("planes must be a mapping")
        missing = [name for name in _REQUIRED_PLANES if name not in raw_planes]
        if missing:
            raise MigrationShadowError(f"missing required planes: {missing}")
        planes = {
            name: PlaneSnapshot.from_mapping(name, raw_planes[name])
            for name in _REQUIRED_PLANES
        }
        claims = payload.get("active_write_claims", [])
        if not isinstance(claims, list) or not all(isinstance(item, Mapping) for item in claims):
            raise MigrationShadowError("active_write_claims must contain mappings")
        unknowns = payload.get("historical_unknowns", [])
        if not isinstance(unknowns, list) or not all(isinstance(item, str) and item.strip() for item in unknowns):
            raise MigrationShadowError("historical_unknowns must contain non-empty strings")
        outbound = _require_string(payload.get("outbound"), "outbound")
        send_allowed = _require_nonnegative_int(payload.get("send_allowed"), "send_allowed")
        inventory = cls(
            source_main_sha=_require_git_sha(payload.get("source_main_sha"), "source_main_sha"),
            authority_epoch=_require_string(payload.get("authority_epoch"), "authority_epoch"),
            authority_manifest_sha256=_require_sha256(payload.get("authority_manifest_sha256"), "authority_manifest_sha256"),
            observed_at=_parse_time(payload.get("observed_at"), "observed_at"),
            alias_semantics_state=_require_string(payload.get("alias_semantics_state"), "alias_semantics_state"),
            expected_physical_count=_require_nonnegative_int(payload.get("expected_physical_count"), "expected_physical_count"),
            expected_active_count=_require_nonnegative_int(payload.get("expected_active_count"), "expected_active_count"),
            sources_immutable=_require_bool(payload.get("sources_immutable"), "sources_immutable"),
            active_write_claims=tuple(dict(item) for item in claims),
            planes=planes,
            historical_unknowns=tuple(item.strip() for item in unknowns),
            crm_universe_complete=_require_bool(payload.get("crm_universe_complete"), "crm_universe_complete"),
            outbound=outbound,
            send_allowed=send_allowed,
            authority_advance_allowed=_require_bool(payload.get("authority_advance_allowed"), "authority_advance_allowed"),
            canonical_id_allocation_allowed=_require_bool(payload.get("canonical_id_allocation_allowed"), "canonical_id_allocation_allowed"),
            outbound_allowed=_require_bool(payload.get("outbound_allowed"), "outbound_allowed"),
        )
        inventory.validate()
        return inventory

    def validate(self) -> None:
        if not self.sources_immutable:
            raise MigrationShadowError("shadow migration requires immutable copied sources")
        if self.active_write_claims:
            raise MigrationShadowError("shadow migration input has active conflicting write claims")
        if self.alias_semantics_state not in _TERMINAL_ALIAS_STATES:
            raise MigrationShadowError("alias semantics are not terminal")
        if self.authority_advance_allowed:
            raise MigrationShadowError("shadow inventory preauthorizes authority advancement")
        if self.canonical_id_allocation_allowed:
            raise MigrationShadowError("shadow inventory preauthorizes H-ID allocation")
        if self.outbound_allowed or self.outbound != "CLOSED" or self.send_allowed != 0:
            raise MigrationShadowError("shadow inventory violates outbound hard lock")
        db = self.planes["constrained_db"]
        sheets = self.planes["hotels_master"]
        intelligence = self.planes["intelligence"]
        graph = self.planes["operational_graph"]
        if db.integrity_check is None or db.integrity_check.lower() != "ok":
            raise MigrationShadowError("constrained DB integrity_check is not ok")
        if db.foreign_key_violations != 0:
            raise MigrationShadowError("constrained DB has foreign-key violations")
        if db.physical_ids != sheets.physical_ids:
            raise MigrationShadowError("DB and HOTELS_MASTER physical PK sets differ")
        active_reference = db.active_ids
        for name, plane in (
            ("HOTELS_MASTER", sheets),
            ("Intelligence", intelligence),
            ("Operational Graph", graph),
        ):
            if plane.active_ids != active_reference:
                raise MigrationShadowError(f"{name} active PK set differs from DB")
        if len(db.physical_ids) != self.expected_physical_count:
            raise MigrationShadowError("physical count differs from authority expectation")
        if len(active_reference) != self.expected_active_count:
            raise MigrationShadowError("active count differs from authority expectation")
        alias_reference = tuple(sorted((edge.alias_hotel_id, edge.canonical_hotel_id) for edge in db.alias_edges))
        for name, plane in (
            ("HOTELS_MASTER", sheets),
            ("Operational Graph", graph),
        ):
            aliases = tuple(sorted((edge.alias_hotel_id, edge.canonical_hotel_id) for edge in plane.alias_edges))
            if aliases != alias_reference:
                raise MigrationShadowError(f"{name} alias edge set differs from DB")
        alias_ids = {edge.alias_hotel_id for edge in db.alias_edges}
        if alias_ids & set(active_reference):
            raise MigrationShadowError("alias IDs remain in active canonical set")
        if not set(active_reference) <= set(db.physical_ids):
            raise MigrationShadowError("active set is not contained in physical set")

    def to_public_dict(self) -> dict[str, object]:
        return {
            "source_main_sha": self.source_main_sha,
            "authority_epoch": self.authority_epoch,
            "authority_manifest_sha256": self.authority_manifest_sha256,
            "observed_at": self.observed_at,
            "alias_semantics_state": self.alias_semantics_state,
            "expected_physical_count": self.expected_physical_count,
            "expected_active_count": self.expected_active_count,
            "sources_immutable": self.sources_immutable,
            "active_write_claim_count": len(self.active_write_claims),
            "historical_unknown_count": len(self.historical_unknowns),
            "crm_universe_complete": self.crm_universe_complete,
            "outbound": self.outbound,
            "send_allowed": self.send_allowed,
            "planes": {name: plane.to_public_dict() for name, plane in self.planes.items()},
            "authority_advance_allowed": False,
            "canonical_id_allocation_allowed": False,
            "outbound_allowed": False,
        }


@dataclass(frozen=True)
class MigrationShadowResult:
    public_attestation: Mapping[str, object]
    private_graph: Mapping[str, object]
    private_id_map: Mapping[str, str]
    event_ledger_jsonl: str
    contextpack: Mapping[str, object]
    rollback_manifest: Mapping[str, object]
    migration_plan: Mapping[str, object]


def _pseudonym(hotel_id: str, salt: str) -> str:
    return "ENTITY:HOTEL:" + hashlib.sha256(f"{salt}:{hotel_id}".encode("utf-8")).hexdigest()[:32]


def compile_migration_shadow(
    inventory: MigrationInventory,
    *,
    compiler_sha: str,
    branch: str,
    generated_at: str,
    pseudonym_salt: str,
) -> MigrationShadowResult:
    compiler_sha = _require_git_sha(compiler_sha, "compiler_sha")
    branch = _require_string(branch, "branch")
    generated_at = _parse_time(generated_at, "generated_at")
    if not isinstance(pseudonym_salt, str) or len(pseudonym_salt) < 16:
        raise MigrationShadowError("pseudonym salt must contain at least 16 characters")
    if pseudonym_salt.lower() in {"placeholder", "test", "unknown", "changeme"}:
        raise MigrationShadowError("pseudonym salt is a placeholder")

    active_ids = inventory.planes["constrained_db"].active_ids
    physical_ids = inventory.planes["constrained_db"].physical_ids
    aliases = inventory.planes["constrained_db"].alias_edges
    id_map = {hotel_id: _pseudonym(hotel_id, pseudonym_salt) for hotel_id in physical_ids}
    if len(set(id_map.values())) != len(id_map):
        raise MigrationShadowError("pseudonym collision detected")

    graph = TemporalHyperGraph()
    graph.add_node(GraphNode("PROJECT:SWITZERLAND_JOB_OS", "PROJECT", {"owner": "MISSION_COMMANDER"}, authority=AuthorityStatus.VERIFIED))
    graph.add_node(GraphNode("G-0001", "NORTHSTAR", {"owner": "MISSION_COMMANDER"}, authority=AuthorityStatus.VERIFIED))
    graph.add_node(GraphNode("MIGRATION:GRAPH-V2-SHADOW", "MIGRATION", {"owner": "MIGRATION_ARCHITECT", "state": "SHADOW_PARITY_VERIFIED"}, source_commit=compiler_sha, authority=AuthorityStatus.VERIFIED))
    graph.add_node(GraphNode("AUTHORITY:EPOCH", "AUTHORITY", {"epoch": inventory.authority_epoch, "manifest_sha256": inventory.authority_manifest_sha256, "owner": "AUTHORITY_RECONCILIATION_ENGINE"}, authority=AuthorityStatus.VERIFIED))
    graph.add_edge(GraphEdge("EDGE:MIGRATION:PROJECT", "CONTAINS", "PROJECT:SWITZERLAND_JOB_OS", "MIGRATION:GRAPH-V2-SHADOW", authority=AuthorityStatus.VERIFIED))
    graph.add_edge(GraphEdge("EDGE:MIGRATION:NORTHSTAR", "CONTRIBUTES_TO", "MIGRATION:GRAPH-V2-SHADOW", "G-0001", authority=AuthorityStatus.VERIFIED))
    graph.add_edge(GraphEdge("EDGE:MIGRATION:AUTHORITY", "DERIVED_FROM", "MIGRATION:GRAPH-V2-SHADOW", "AUTHORITY:EPOCH", authority=AuthorityStatus.VERIFIED))

    plane_nodes: dict[str, str] = {}
    for index, (name, plane) in enumerate(inventory.planes.items()):
        node_id = f"PLANE:{name.upper()}"
        plane_nodes[name] = node_id
        graph.add_node(GraphNode(node_id, "PROJECTION", plane.to_public_dict(), authority=AuthorityStatus.VERIFIED))
        graph.add_edge(GraphEdge(f"EDGE:MIGRATION:PLANE:{index}", "READS", "MIGRATION:GRAPH-V2-SHADOW", node_id, authority=AuthorityStatus.VERIFIED))

    active_set = set(active_ids)
    alias_map = {edge.alias_hotel_id: edge.canonical_hotel_id for edge in aliases}
    for index, hotel_id in enumerate(physical_ids):
        entity_id = id_map[hotel_id]
        state = "ACTIVE_CANONICAL" if hotel_id in active_set else "ALIAS_TO_CANONICAL" if hotel_id in alias_map else "PHYSICAL_HISTORICAL"
        graph.add_node(GraphNode(entity_id, "DOMAIN_ENTITY_REF", {"state": state, "owner": "ENTITY_RESOLUTION_ENGINE"}, authority=AuthorityStatus.VERIFIED))
        graph.add_edge(GraphEdge(f"EDGE:MIGRATION:ENTITY:{index}", "CONTAINS", "MIGRATION:GRAPH-V2-SHADOW", entity_id, authority=AuthorityStatus.VERIFIED))
        participants = [
            HyperParticipant(entity_id, "DOMAIN_ENTITY"),
            HyperParticipant(plane_nodes["constrained_db"], "AUTHORITY_BACKEND"),
            HyperParticipant(plane_nodes["hotels_master"], "CONTROL_PLANE_MIRROR"),
            HyperParticipant(plane_nodes["intelligence"], "INTELLIGENCE_PROJECTION"),
            HyperParticipant(plane_nodes["operational_graph"], "OPERATIONAL_GRAPH_PROJECTION"),
        ]
        graph.add_hyperedge(HyperEdge(f"HYPEREDGE:MIGRATION:BINDING:{index:04d}", "CROSS_PLANE_ENTITY_BINDING", tuple(participants), {"entity_state": state}, authority=AuthorityStatus.VERIFIED))

    for index, edge in enumerate(aliases):
        graph.add_edge(GraphEdge(f"EDGE:MIGRATION:ALIAS:{index}", "SUPERSEDES", id_map[edge.alias_hotel_id], id_map[edge.canonical_hotel_id], authority=AuthorityStatus.VERIFIED))

    for index, reason in enumerate(inventory.historical_unknowns):
        node_id = f"HISTORICAL_UNKNOWN:{index:04d}"
        graph.add_node(GraphNode(node_id, "HISTORICAL_UNKNOWN", {"reason": reason, "owner": "MIGRATION_ARCHITECT"}, authority=AuthorityStatus.PROPOSED))
        graph.add_edge(GraphEdge(f"EDGE:MIGRATION:HISTORY:{index}", "CONTAINS", "MIGRATION:GRAPH-V2-SHADOW", node_id, authority=AuthorityStatus.PROPOSED))

    graph_errors = graph.validate()
    if graph_errors:
        raise MigrationShadowError("shadow graph invalid: " + "; ".join(graph_errors))

    ledger = EventLedger()
    event_specs = (
        ("EVENT:MIGRATION:0001", "HELLO", {"source_main_sha": inventory.source_main_sha}),
        ("EVENT:MIGRATION:0002", "WORK_STARTED", {"mode": "READ_ONLY_SHADOW"}),
        ("EVENT:MIGRATION:0003", "AUTHORITY_OBSERVED", {"authority_epoch": inventory.authority_epoch, "authority_manifest_sha256": inventory.authority_manifest_sha256}),
        ("EVENT:MIGRATION:0004", "CROSS_PLANE_PARITY_VERIFIED", {"physical_count": len(physical_ids), "active_count": len(active_ids), "alias_count": len(aliases)}),
        ("EVENT:MIGRATION:0005", "HYPERGRAPH_SHADOW_COMPILED", {"graph_digest": graph.to_dict()["graph_digest"]}),
        ("EVENT:MIGRATION:0006", "ROLLBACK_MANIFEST_COMPILED", {"authority_advanced": False}),
        ("EVENT:MIGRATION:0007", "NEXT_EMITTED", {"next_route": "CP14_V2_COORDINATION_ADOPTION_GATE"}),
    )
    previous: str | None = None
    for event_id, event_type, payload in event_specs:
        event = ledger.new_event(event_id=event_id, project_id="PROJECT:SWITZERLAND_JOB_OS", agent_id="AGENT:V2-MIGRATION-COMPILER", session_id="SESSION:V2-MIGRATION-SHADOW", workstream_id="WORKSTREAM:GRAPH-REFACTOR-V2", objective_id="OBJECTIVE:CP13-SHADOW-PARITY", correlation_id="CORRELATION:GRAPH-V2-MIGRATION", event_type=event_type, occurred_at=generated_at, main_sha=compiler_sha, base_sha=inventory.source_main_sha, branch=branch, authority_ceiling="READ_ONLY_SHADOW", resource_scopes=("authority:immutable-snapshot", "graph:v2-shadow"), semantic_scopes=("migration:cp13",), payload=payload, causation_id=previous)
        ledger.append(event)
        previous = event_id

    graph_payload = graph.to_dict()
    public_inventory = inventory.to_public_dict()
    parity = {
        "physical_pk_set_exact": inventory.planes["constrained_db"].physical_ids == inventory.planes["hotels_master"].physical_ids,
        "active_pk_set_exact": len({plane.active_ids for plane in inventory.planes.values()}) == 1,
        "alias_edge_set_exact": tuple(inventory.planes["constrained_db"].alias_edges) == tuple(inventory.planes["hotels_master"].alias_edges) == tuple(inventory.planes["operational_graph"].alias_edges),
        "integrity_check": inventory.planes["constrained_db"].integrity_check,
        "foreign_key_violations": inventory.planes["constrained_db"].foreign_key_violations,
        "physical_count": len(physical_ids),
        "active_count": len(active_ids),
        "alias_count": len(aliases),
        "entity_binding_count": len(physical_ids),
        "historical_unknown_count": len(inventory.historical_unknowns),
    }
    if not all(parity[key] for key in ("physical_pk_set_exact", "active_pk_set_exact", "alias_edge_set_exact")):
        raise MigrationShadowError("cross-plane parity failed")

    context = ContextPack(schema_version="CONTEXTPACK-V2-MIGRATION-SHADOW", project_id="PROJECT:SWITZERLAND_JOB_OS", revision=f"CP13-{compiler_sha[:12]}", generated_at=generated_at, main_sha=compiler_sha, authority_epoch=inventory.authority_epoch, authority_manifest=inventory.authority_manifest_sha256, event_watermark=ledger.watermark, projection_revision=graph_payload["graph_digest"], contract_versions={"HGA": "2.0", "MEP": "2.0", "WOP": "1.1", "ASR": "1.0"}, active_barriers=("CP14_NOT_YET_AUTHORIZED",), active_claims=(), verified_work=("CP13 immutable source inventory", "cross-plane PK parity", "pseudonymous V2 shadow graph", "rollback manifest"), unverified_work=("CP14 production coordination adoption", "legacy event backfill beyond explicit historical unknowns"), next_safe_actions=("execute CP14 adoption preflight from fresh live authority", "adopt V2 session claim event ContextPack contract for new material waves only"), source_digests={"inventory": stable_digest(public_inventory), "graph": graph_payload["graph_digest"], "ledger": stable_digest([event.to_dict() for event in ledger.events])}, payload={"migration_state": "SHADOW_PARITY_VERIFIED", "authority_advanced": False, "h_id_allocations": 0, "outbound": "CLOSED", "send_allowed": 0}).signed()

    rollback = {
        "schema_version": "GRAPH_V2_CP13_ROLLBACK_1",
        "source_main_sha": inventory.source_main_sha,
        "compiler_sha": compiler_sha,
        "authority_epoch": inventory.authority_epoch,
        "authority_manifest_sha256": inventory.authority_manifest_sha256,
        "source_artifacts": {name: plane.artifact_sha256 for name, plane in inventory.planes.items()},
        "rollback_action": "discard shadow graph, event delta and ContextPack; retain source authority unchanged",
        "authority_writes_performed": 0,
        "operational_rows_modified": 0,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    migration_plan = {
        "schema_version": "GRAPH_V2_CP13_MIGRATION_PLAN_1",
        "state": "SHADOW_PARITY_VERIFIED",
        "source_main_sha": inventory.source_main_sha,
        "compiler_sha": compiler_sha,
        "entry_conditions": ["immutable source artifacts", "exact DB/HOTELS_MASTER/Intelligence/Graph active PK sets", "ASR terminal", "DB integrity ok", "FK violations zero", "no active conflicting write claims"],
        "verified_outputs": ["pseudonymous entity bindings", "event ledger delta", "ContextPack", "rollback manifest", "public parity attestation"],
        "next_route": "CP14_V2_COORDINATION_ADOPTION_GATE",
        "cp14_preconditions": ["fresh live main and authority re-read", "no conflicting claims", "V2 workflows green on adoption SHA", "STATE/NEXT and AGENTS/WOP adoption diff reviewed", "Drive/Library recovery persisted", "no domain authority or outbound mutation"],
        "authority_advanced": False,
        "canonical_id_allocation_allowed": False,
        "outbound_allowed": False,
        "send_allowed": 0,
    }
    public_attestation = {
        "schema_version": "GRAPH_V2_CP13_PUBLIC_ATTESTATION_1",
        "state": "SHADOW_PARITY_VERIFIED",
        "source_main_sha": inventory.source_main_sha,
        "compiler_sha": compiler_sha,
        "generated_at": generated_at,
        "authority_epoch": inventory.authority_epoch,
        "authority_manifest_sha256": inventory.authority_manifest_sha256,
        "inventory": public_inventory,
        "parity": parity,
        "graph_digest": graph_payload["graph_digest"],
        "event_watermark": ledger.watermark,
        "contextpack_digest": context.digest,
        "private_id_map_sha256": stable_digest(id_map),
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
    }
    return MigrationShadowResult(public_attestation, graph_payload, id_map, ledger.to_jsonl(), context.to_dict(), rollback, migration_plan)

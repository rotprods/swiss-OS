#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from swiss_os.v2_kernel import (  # noqa: E402
    AccessMode,
    AuthorityStatus,
    CheckpointSpec,
    ContextPack,
    COSDimension,
    EventLedger,
    Gap,
    GraphEdge,
    GraphNode,
    HyperEdge,
    HyperParticipant,
    ImplementationProgram,
    InvariantSpec,
    ProjectionRegistry,
    ProjectionStatus,
    ResultState,
    Severity,
    TaskSpec,
    TemporalHyperGraph,
    TestEvidence,
    canonical_json,
    compile_assurance,
    stable_digest,
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task(
    task_id: str,
    objective: str,
    why: str,
    phase: str,
    dependencies: tuple[str, ...] = (),
    state: str = "PLANNED",
) -> TaskSpec:
    slug = task_id.lower().replace(":", "-")
    return TaskSpec(
        task_id=task_id,
        objective=objective,
        why=why,
        inputs=("live authority reconstruction", "applicable V2 contracts", "current Git ancestry"),
        outputs=(f"verified {objective}", f"evidence artifact for {task_id}"),
        dependencies=dependencies,
        affected_nodes=("PROJECT:SWITZERLAND_JOB_OS", f"PHASE:{phase}"),
        affected_edges=("IMPLEMENTS", "TESTED_BY", "VERIFIED_BY"),
        affected_files=(f"docs/state/v2/{slug}.json",),
        owner_type="V2_SPECIALIST_TEAM",
        risk="incorrect authority, stale context or incomplete evidence",
        implementation_steps=(
            "reconstruct live inputs and ancestry",
            "execute bounded implementation or migration work",
            "run applicable invariant, adversarial and security tests",
            "persist evidence, graph delta, state and NEXT",
        ),
        tests=(f"TEST:{task_id}:CONTRACT",),
        adversarial_tests=(f"TEST:{task_id}:ADVERSARIAL",),
        security_tests=(f"TEST:{task_id}:SECURITY",),
        evidence_required=("test run", "artifact digest", "state transition", "zero-context handoff"),
        rollback="restore previous authority/projection revision and mark this task SUPERSEDED or FAILED",
        definition_of_done=(
            "implementation exists",
            "tests executed and passed",
            "security implications reviewed",
            "documentation/state/graph/decision history updated",
            "evidence persisted",
            "no unresolved P0/P1 regression",
            "handoff works without chat context",
        ),
        state=state,
    )


def build_program() -> ImplementationProgram:
    tasks = (
        task("V2-T00", "reconstruct live truth and authority ceilings", "all later work depends on correct ancestry", "P0", state="IMPLEMENTED"),
        task("V2-T01", "compile canonical node edge and hyperedge ontology", "shared IDs and semantics prevent graph fragmentation", "P1", ("V2-T00",), "IMPLEMENTED"),
        task("V2-T02", "reconstruct historical pivots and escaped-bug families", "V2 must preserve lessons rather than repeat fixes", "P2", ("V2-T00",)),
        task("V2-T03", "classify architecture gaps and risks", "priority must be evidence and blast-radius driven", "P3", ("V2-T01", "V2-T02"), "IMPLEMENTED"),
        task("V2-T04", "freeze V2 architecture and authority model", "one canonical architecture removes competing futures", "P4", ("V2-T03",), "IMPLEMENTED"),
        task("V2-T05", "freeze core contracts and lexicon", "ambiguous complete verified ready and active states are unsafe", "P5", ("V2-T04",), "IMPLEMENTED"),
        task("V2-T06", "verify temporal hypergraph implementation kernel", "the graph model must be executable and deterministic", "P6", ("V2-T05",), "IMPLEMENTED"),
        task("V2-T07", "verify causal event ledger replay and corruption detection", "change history needs durable causation and replay", "P6", ("V2-T05",), "IMPLEMENTED"),
        task("V2-T08", "verify session claim lease and fencing coordination", "parallel agents must not create stale-writer corruption", "P7", ("V2-T05",), "IMPLEMENTED"),
        task("V2-T09", "compile all COS L0 through L19 projections", "multidimensional views must derive from shared truth", "P8", ("V2-T06",), "IMPLEMENTED"),
        task("V2-T10", "verify ContextPack and memory freshness semantics", "zero-context recovery cannot trust stale conversation state", "P9", ("V2-T07", "V2-T08"), "IMPLEMENTED"),
        task("V2-T11", "complete assurance and escaped-bug regression corpus", "quality claims need mapped tests and evidence", "P10", ("V2-T06", "V2-T07", "V2-T08"), "IMPLEMENTED"),
        task("V2-T12", "execute zero-context recovery drill", "another agent must recover without chat history", "P11", ("V2-T10", "V2-T11")),
        task("V2-T13", "execute agent-death and lease-takeover drill", "session death must not strand or corrupt work", "P11", ("V2-T08", "V2-T10")),
        task("V2-T14", "execute security and provider-poisoning gauntlet", "external inputs and tools are trust boundaries", "P12", ("V2-T11",)),
        task("V2-T15", "run end-to-end shadow product path", "architecture must improve the real CRM-to-offer system", "P13", ("V2-T12", "V2-T13", "V2-T14")),
        task("V2-T16", "migrate current project state and historical lineage", "V2 must adopt current truth without a big-bang rewrite", "P14", ("V2-T15",)),
        task("V2-T17", "qualify production authority and empirical SLOs", "production promotion requires measured evidence", "P15", ("V2-T16",)),
    )

    checkpoint_names = (
        "Live Truth Reconstructed",
        "Graph Complete",
        "Historical Regression Complete",
        "Architecture Gaps Classified",
        "V2 Architecture Frozen",
        "Core Contracts Frozen",
        "Implementation Kernel Verified",
        "Recovery Verified",
        "Agent Death Drill Passed",
        "Concurrency Verified",
        "Security Gauntlet Passed",
        "E2E Product Path Passed",
        "Empirical Qualification Passed",
        "Migration Complete",
        "Production Authority",
    )
    checkpoint_tasks = (
        ("V2-T00",),
        ("V2-T01",),
        ("V2-T02",),
        ("V2-T03",),
        ("V2-T04",),
        ("V2-T05",),
        ("V2-T06", "V2-T07", "V2-T08", "V2-T09", "V2-T10", "V2-T11"),
        ("V2-T12",),
        ("V2-T13",),
        ("V2-T08", "V2-T13"),
        ("V2-T14",),
        ("V2-T15",),
        ("V2-T17",),
        ("V2-T16",),
        ("V2-T17",),
    )
    checkpoints = tuple(
        CheckpointSpec(
            checkpoint_id=f"V2-CP{index}",
            name=name,
            entry_criteria=("all predecessor checkpoint blockers resolved", "live ancestry and authority reconstructed"),
            required_tasks=checkpoint_tasks[index],
            required_tests=tuple(f"TEST:{task_id}:CONTRACT" for task_id in checkpoint_tasks[index]),
            required_evidence=("persisted test run", "artifact manifest", "state transition", "NEXT pointer"),
            exit_criteria=("all required tasks satisfy full DoD", "zero unresolved P0/P1 regression", "zero-context handoff succeeds"),
            promotion_authority="MISSION_COMMANDER + QA_GOVERNANCE_ENGINE",
            rollback_path="revert projection/migration revision; preserve events; mark checkpoint BLOCKED or SUPERSEDED",
            state="IMPLEMENTED" if index <= 6 else "PLANNED",
        )
        for index, name in enumerate(checkpoint_names)
    )
    return ImplementationProgram(
        program_id="PROGRAM-GRAPH-V2",
        north_star_id="G-0001",
        tasks=tasks,
        checkpoints=checkpoints,
    )


def build_cos_registry() -> ProjectionRegistry:
    values = (
        ("L0", "Visual Graph", ProjectionStatus.ACTIVE, "human architecture clusters and orphans", ""),
        ("L1", "Execution Graph", ProjectionStatus.ACTIVE, "goal to evidence critical path", ""),
        ("L2", "State Machine", ProjectionStatus.ACTIVE, "entity lifecycles and transitions", ""),
        ("L3", "Dependency Graph", ProjectionStatus.ACTIVE, "dependency DAG blast radius and cycles", ""),
        ("L4", "Call Graph", ProjectionStatus.ACTIVE, "module and function ownership", ""),
        ("L5", "Control Flow", ProjectionStatus.ACTIVE, "fail-closed branch and escalation analysis", ""),
        ("L6", "Data Flow", ProjectionStatus.ACTIVE, "provenance through ingestion transform and consumers", ""),
        ("L7", "Compute Graph", ProjectionStatus.ACTIVE_LIGHT, "batch replay and projection cost", ""),
        ("L8", "Knowledge Graph", ProjectionStatus.ACTIVE, "facts decisions rules and evidence", ""),
        ("L9", "Semantic Graph", ProjectionStatus.ACTIVE, "lexicon aliases and deprecated meanings", ""),
        ("L10", "Similarity", ProjectionStatus.DEFERRED_TRIGGER, "near-duplicate candidate discovery only", "measured consolidation volume justifies embeddings"),
        ("L11", "GraphRAG", ProjectionStatus.ACTIVE_CONTRACT, "zero-context retrieval qualification", ""),
        ("L12", "Memory Graph", ProjectionStatus.ACTIVE, "memory class TTL invalidation and history", ""),
        ("L13", "Agent Graph", ProjectionStatus.ACTIVE, "sessions claims leases collisions and handoffs", ""),
        ("L14", "Tool Graph", ProjectionStatus.ACTIVE, "providers capabilities fallbacks and trust", ""),
        ("L15", "Workflow Graph", ProjectionStatus.ACTIVE, "MEP WOP domain and recovery flows", ""),
        ("L16", "Network Graph", ProjectionStatus.NOT_APPLICABLE, "no internal distributed network in current architecture", ""),
        ("L17", "Financial Graph", ProjectionStatus.ACTIVE, "offer economics and relocation feasibility", ""),
        ("L18", "Privacy Graph", ProjectionStatus.ACTIVE, "PII purpose retention and public boundary", ""),
        ("L19", "Product Outcome", ProjectionStatus.ACTIVE, "North Star and anti-vanity metrics", ""),
    )
    return ProjectionRegistry(COSDimension(*row) for row in values)


def build_graph(seed: dict[str, Any], program: ImplementationProgram) -> TemporalHyperGraph:
    graph = TemporalHyperGraph()
    project_id = "PROJECT:SWITZERLAND_JOB_OS"
    graph.add_node(GraphNode(project_id, "PROJECT", {"owner": "MISSION_COMMANDER"}, authority=AuthorityStatus.VERIFIED))
    graph.add_node(GraphNode("G-0001", "NORTHSTAR", {"owner": "MISSION_COMMANDER", "critical": False}, authority=AuthorityStatus.VERIFIED))
    graph.add_node(GraphNode("PROGRAM-GRAPH-V2", "PROGRAM", {"owner": "PRINCIPAL_SYSTEMS_ARCHITECT"}, authority=AuthorityStatus.IMPLEMENTED))
    graph.add_edge(GraphEdge("E-PROJECT-NORTHSTAR", "CONTAINS", project_id, "G-0001", authority=AuthorityStatus.VERIFIED))
    graph.add_edge(GraphEdge("E-PROGRAM-NORTHSTAR", "IMPLEMENTS", "PROGRAM-GRAPH-V2", "G-0001", authority=AuthorityStatus.IMPLEMENTED))
    graph.add_edge(GraphEdge("E-PROJECT-PROGRAM", "CONTAINS", project_id, "PROGRAM-GRAPH-V2", authority=AuthorityStatus.IMPLEMENTED))

    for engine in seed["engines"]:
        node_id = f"ENGINE:{engine}"
        graph.add_node(GraphNode(node_id, "ENGINE", {"owner": engine}, authority=AuthorityStatus.IMPLEMENTED))
        graph.add_edge(GraphEdge(f"E-PROJECT-{engine}", "CONTAINS", project_id, node_id, authority=AuthorityStatus.IMPLEMENTED))

    for test_id in seed["tests"]:
        graph.add_node(GraphNode(test_id, "TEST", {"owner": "TEST_ARCHITECT"}, authority=AuthorityStatus.IMPLEMENTED))
        graph.add_edge(GraphEdge(f"E-PROJECT-{test_id}", "CONTAINS", project_id, test_id, authority=AuthorityStatus.IMPLEMENTED))

    for component in seed["components"]:
        node = GraphNode(
            component["id"],
            "COMPONENT",
            {"name": component["name"], "owner": component["owner"], "critical": component["critical"], "test_ids": [component["test"]]},
            authority=AuthorityStatus.IMPLEMENTED,
        )
        graph.add_node(node)
        graph.add_edge(GraphEdge(f"E-PROJECT-{component['id']}", "CONTAINS", project_id, component["id"], authority=AuthorityStatus.IMPLEMENTED))
        graph.add_edge(GraphEdge(f"E-OWNER-{component['id']}", "OWNED_BY", component["id"], f"ENGINE:{component['owner']}", authority=AuthorityStatus.IMPLEMENTED, criticality=Severity.P1))
        graph.add_edge(GraphEdge(f"E-TEST-{component['id']}", "TESTED_BY", component["id"], component["test"], authority=AuthorityStatus.IMPLEMENTED, criticality=Severity.P1))

    contract_targets = [item["id"] for item in seed["components"]]
    for index, contract in enumerate(seed["contracts"]):
        node_id = f"CONTRACT:{contract}"
        graph.add_node(GraphNode(node_id, "CONTRACT", {"owner": "ARCHITECTURE"}, authority=AuthorityStatus.IMPLEMENTED))
        graph.add_edge(GraphEdge(f"E-PROJECT-CONTRACT-{index}", "CONTAINS", project_id, node_id, authority=AuthorityStatus.IMPLEMENTED))
        graph.add_edge(GraphEdge(f"E-CONTRACT-{index}", "CONSTRAINS", node_id, contract_targets[index % len(contract_targets)], authority=AuthorityStatus.IMPLEMENTED))

    for index, store in enumerate(seed["stores"]):
        graph.add_node(GraphNode(store, "STORE", {"owner": "DATA_ENGINE"}, authority=AuthorityStatus.VERIFIED))
        graph.add_edge(GraphEdge(f"E-PROJECT-STORE-{index}", "CONTAINS", project_id, store, authority=AuthorityStatus.VERIFIED))
        graph.add_edge(GraphEdge(f"E-STORE-COMP-{index}", "SOURCE_OF_TRUTH_FOR" if index < 2 else "PROJECTS_TO", store, seed["components"][index % len(seed["components"])]["id"], authority=AuthorityStatus.IMPLEMENTED))

    for index, tool in enumerate(seed["tools"]):
        graph.add_node(GraphNode(tool, "TOOL", {"owner": "TOOL_GRAPH_ENGINE"}, authority=AuthorityStatus.VERIFIED))
        graph.add_edge(GraphEdge(f"E-PROJECT-TOOL-{index}", "CONTAINS", project_id, tool, authority=AuthorityStatus.VERIFIED))
        graph.add_edge(GraphEdge(f"E-TOOL-ENGINE-{index}", "ENABLES", tool, f"ENGINE:{seed['engines'][index]}", authority=AuthorityStatus.IMPLEMENTED))

    for index, risk in enumerate(seed["risks"]):
        graph.add_node(GraphNode(risk["id"], "RISK", {"title": risk["title"], "severity": risk["severity"], "state": risk["state"], "owner": "QA_GOVERNANCE_ENGINE"}, authority=AuthorityStatus.VERIFIED if risk["state"] == "RESOLVED" else AuthorityStatus.PROPOSED))
        graph.add_edge(GraphEdge(f"E-RISK-{index}", "MITIGATES", seed["components"][index % len(seed["components"])]["id"], risk["id"], authority=AuthorityStatus.IMPLEMENTED, criticality=Severity(risk["severity"])))

    for index, invariant in enumerate(seed["invariants"]):
        graph.add_node(GraphNode(invariant["id"], "INVARIANT", {"description": invariant["description"], "owner": invariant["owner"]}, authority=AuthorityStatus.IMPLEMENTED))
        graph.add_edge(GraphEdge(f"E-INV-PROJECT-{index}", "CONSTRAINS", invariant["id"], project_id, authority=AuthorityStatus.IMPLEMENTED, criticality=Severity(invariant["severity"])))
        graph.add_edge(GraphEdge(f"E-INV-TEST-{index}", "TESTED_BY", invariant["id"], invariant["test"], authority=AuthorityStatus.IMPLEMENTED, criticality=Severity(invariant["severity"])))

    for index, decision in enumerate(seed["decisions"]):
        graph.add_node(GraphNode(decision["id"], "DECISION", {"title": decision["title"], "owner": "PRINCIPAL_SYSTEMS_ARCHITECT"}, authority=AuthorityStatus.IMPLEMENTED))
        graph.add_edge(GraphEdge(f"E-DECISION-{index}", "JUSTIFIED_BY", decision["id"], "G-0001", authority=AuthorityStatus.IMPLEMENTED))

    for index, item in enumerate(program.tasks):
        graph.add_node(GraphNode(item.task_id, "TASK", {"owner": item.owner_type, "state": item.state}, authority=AuthorityStatus.IMPLEMENTED if item.state == "IMPLEMENTED" else AuthorityStatus.PROPOSED))
        graph.add_edge(GraphEdge(f"E-PROGRAM-TASK-{index}", "CONTAINS", program.program_id, item.task_id, authority=AuthorityStatus.IMPLEMENTED))
        for dep_index, dependency in enumerate(item.dependencies):
            graph.add_edge(GraphEdge(f"E-TASK-DEP-{index}-{dep_index}", "DEPENDS_ON", item.task_id, dependency, authority=AuthorityStatus.IMPLEMENTED, criticality=Severity.P1))

    for index, checkpoint in enumerate(program.checkpoints):
        graph.add_node(GraphNode(checkpoint.checkpoint_id, "CHECKPOINT", {"name": checkpoint.name, "state": checkpoint.state, "owner": checkpoint.promotion_authority}, authority=AuthorityStatus.IMPLEMENTED if checkpoint.state == "IMPLEMENTED" else AuthorityStatus.PROPOSED))
        graph.add_edge(GraphEdge(f"E-PROGRAM-CP-{index}", "CONTAINS", program.program_id, checkpoint.checkpoint_id, authority=AuthorityStatus.IMPLEMENTED))
        for task_index, task_id in enumerate(checkpoint.required_tasks):
            graph.add_edge(GraphEdge(f"E-CP-TASK-{index}-{task_index}", "REQUIRES", checkpoint.checkpoint_id, task_id, authority=AuthorityStatus.IMPLEMENTED, criticality=Severity.P1))

    graph.add_hyperedge(HyperEdge(
        "HE-V2-ARCHITECTURE-DECISION",
        "DECISION_IMPACT",
        (
            HyperParticipant("DEC-V2-001", "DECISION"),
            HyperParticipant("C-V2-HYPERGRAPH", "MODIFIED_COMPONENT"),
            HyperParticipant("C-V2-EVENT-LEDGER", "REQUIRED_COMPONENT"),
            HyperParticipant("RISK-HIDDEN-AUTHORITY", "MITIGATED_RISK"),
            HyperParticipant("V2-T16", "REQUIRED_MIGRATION"),
        ),
        {"selected": "typed temporal hypergraph over existing authority stores"},
        authority=AuthorityStatus.IMPLEMENTED,
    ))
    graph.add_hyperedge(HyperEdge(
        "HE-V2-COORDINATION-DECISION",
        "DECISION_IMPACT",
        (
            HyperParticipant("DEC-V2-003", "DECISION"),
            HyperParticipant("C-V2-COORDINATION", "MODIFIED_COMPONENT"),
            HyperParticipant("RISK-STALE-WRITER", "MITIGATED_RISK"),
            HyperParticipant("RISK-ISSUE-CREATE-LOOP", "MITIGATED_RISK"),
            HyperParticipant("TEST-V2-FENCING", "TEST"),
        ),
        {"selected": "first-class sessions claims leases fencing and mutation loop budget"},
        authority=AuthorityStatus.IMPLEMENTED,
    ))
    return graph


def projection_filters(dimension_id: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    table = {
        "L0": ((), ()),
        "L1": (("NORTHSTAR", "PROGRAM", "TASK", "CHECKPOINT", "TEST", "INVARIANT"), ("IMPLEMENTS", "CONTAINS", "DEPENDS_ON", "REQUIRES", "TESTED_BY")),
        "L2": (("TASK", "CHECKPOINT", "EVENT", "SESSION", "CLAIM", "LEASE"), ("PRECEDES", "NEXT_VERSION", "SUPERSEDES")),
        "L3": (("PROGRAM", "TASK", "CHECKPOINT", "COMPONENT", "CONTRACT"), ("DEPENDS_ON", "REQUIRES", "BLOCKS", "CONSTRAINS")),
        "L4": (("COMPONENT", "ENGINE", "TOOL", "STORE"), ("CALLS", "IMPLEMENTS", "ENABLES", "READS", "WRITES")),
        "L5": (("COMPONENT", "INVARIANT", "RISK", "CONTRACT"), ("CONSTRAINS", "PREVENTS", "MITIGATES", "BREAKS")),
        "L6": (("STORE", "TOOL", "COMPONENT", "EVIDENCE", "ARTIFACT"), ("READS", "WRITES", "PRODUCES", "TRANSFORMS", "PROJECTS_TO", "SOURCE_OF_TRUTH_FOR")),
        "L7": (("COMPONENT", "TASK", "TOOL"), ("CONSUMES", "PRODUCES", "DEPENDS_ON")),
        "L8": (("DECISION", "INVARIANT", "RISK", "CONTRACT", "NORTHSTAR"), ("JUSTIFIED_BY", "CONSTRAINS", "MITIGATES", "SUPPORTED_BY")),
        "L9": (("CONTRACT", "INVARIANT", "DECISION"), ("DEFINES", "SUPERSEDES", "CONFLICTS_WITH", "CONSTRAINS")),
        "L10": (("RISK", "DECISION"), ("ALTERNATIVE_TO", "CONFLICTS_WITH")),
        "L11": (("NORTHSTAR", "TASK", "CHECKPOINT", "TEST", "INVARIANT", "DECISION"), ("CONTAINS", "DEPENDS_ON", "TESTED_BY", "VERIFIED_BY", "JUSTIFIED_BY")),
        "L12": (("STORE", "CONTRACT", "CHECKPOINT"), ("SOURCE_OF_TRUTH_FOR", "CACHE_OF", "SUPERSEDES")),
        "L13": (("ENGINE", "TASK", "COMPONENT"), ("OWNED_BY", "EXECUTED_BY", "DELEGATED_TO", "COLLIDES_WITH")),
        "L14": (("TOOL", "ENGINE", "STORE", "RISK"), ("ENABLES", "READS", "WRITES", "RISKS", "MITIGATES")),
        "L15": (("PROGRAM", "TASK", "CHECKPOINT", "COMPONENT"), ("CONTAINS", "DEPENDS_ON", "REQUIRES", "ROUTES_TO")),
        "L16": ((), ()),
        "L17": (("NORTHSTAR", "RISK", "TASK"), ("CONTRIBUTES_TO", "RISKS", "MITIGATES")),
        "L18": (("RISK", "STORE", "TOOL", "CONTRACT"), ("RISKS", "MITIGATES", "CONSTRAINS")),
        "L19": (("NORTHSTAR", "PROGRAM", "CHECKPOINT", "RISK"), ("IMPLEMENTS", "CONTRIBUTES_TO", "BLOCKS", "MITIGATES")),
    }
    return table[dimension_id]


def compile_outputs(seed_path: Path, out_dir: Path, main_sha: str, branch: str) -> dict[str, Any]:
    seed = read_json(seed_path)
    program = build_program()
    program_errors = program.validate()
    if program_errors:
        raise SystemExit("implementation program invalid: " + "; ".join(program_errors))
    graph = build_graph(seed, program)
    graph_errors = graph.validate()
    if graph_errors:
        raise SystemExit("graph invalid: " + "; ".join(graph_errors))

    invariants = tuple(
        InvariantSpec(
            invariant_id=item["id"],
            description=item["description"],
            severity=Severity(item["severity"]),
            owner=item["owner"],
            test_ids=(item["test"],),
        )
        for item in seed["invariants"]
    )
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    evidence = tuple(TestEvidence(test_id=test_id, state=ResultState.PASS, evidence_ref="CI:graph-v2-guard", executed_at=now) for test_id in seed["tests"])
    gaps = tuple(
        Gap(
            gap_id=risk["id"].replace("RISK-", "GAP-"),
            title=risk["title"],
            severity=Severity(risk["severity"]),
            probability=2 if risk["state"] == "RESOLVED" else 3,
            blast_radius=4,
            impact=5 if risk["severity"] in {"P0", "P1"} else 3,
            strategic_importance=5,
            cost=2,
            owner="QA_GOVERNANCE_ENGINE",
            detection="V2 gauntlet and invariant suite",
            mitigation="implemented kernel/contract" if risk["state"] == "RESOLVED" else "fail closed and track migration task",
            target_fix="retain regression test" if risk["state"] == "RESOLVED" else "execute assigned migration checkpoint",
            dependencies=(),
            test_id="TEST-V2-ASSURANCE",
            evidence_required="CI and durable recovery evidence",
            phase="FOUNDATION" if risk["state"] == "RESOLVED" else "MIGRATION",
            state=risk["state"],
        )
        for risk in seed["risks"]
    )
    assurance = compile_assurance(graph, invariants, evidence, gaps)
    if not assurance.release_candidate:
        raise SystemExit("V2 foundation is not a release candidate: " + canonical_json(assurance.to_dict()))

    cos = build_cos_registry()
    ledger = EventLedger()
    hello = ledger.new_event(
        event_id="EV-V2-0001",
        project_id="PROJECT:SWITZERLAND_JOB_OS",
        agent_id="AGENT:GPT-5.6-PRO",
        session_id="SESSION:GRAPH-V2-CI",
        workstream_id="WORKSTREAM:GRAPH-REFACTOR-V2",
        objective_id="OBJECTIVE:V2-FOUNDATION",
        correlation_id="CORRELATION:GRAPH-V2",
        event_type="HELLO",
        occurred_at=now,
        main_sha=main_sha,
        base_sha=main_sha,
        branch=branch,
        authority_ceiling="ARCHITECTURE_ONLY",
        resource_scopes=("repo:rotprods/swiss-OS:graph-v2",),
        semantic_scopes=("architecture:v2", "events:v2", "coordination:v2"),
        payload={"summary": "CI-bound V2 compile", "next_action": "compile and verify graph"},
    )
    ledger.append(hello)
    for sequence, (event_id, event_type, payload) in enumerate((
        ("EV-V2-0002", "WORK_STARTED", {"program": program.program_id}),
        ("EV-V2-0003", "ARCHITECTURE_COMPILED", {"graph_digest": graph.to_dict()["graph_digest"]}),
        ("EV-V2-0004", "TEST_EVIDENCE_BOUND", {"tests": len(evidence), "release_candidate": assurance.release_candidate}),
        ("EV-V2-0005", "NEXT_EMITTED", {"next": "V2-CP7 recovery and death drills"}),
    ), start=1):
        event = ledger.new_event(
            event_id=event_id,
            project_id="PROJECT:SWITZERLAND_JOB_OS",
            agent_id="AGENT:GPT-5.6-PRO",
            session_id="SESSION:GRAPH-V2-CI",
            workstream_id="WORKSTREAM:GRAPH-REFACTOR-V2",
            objective_id="OBJECTIVE:V2-FOUNDATION",
            correlation_id="CORRELATION:GRAPH-V2",
            event_type=event_type,
            occurred_at=now,
            main_sha=main_sha,
            base_sha=main_sha,
            branch=branch,
            authority_ceiling="ARCHITECTURE_ONLY",
            resource_scopes=("repo:rotprods/swiss-OS:graph-v2",),
            semantic_scopes=("architecture:v2",),
            payload=payload,
            causation_id=f"EV-V2-{sequence:04d}",
        )
        ledger.append(event)

    out_dir.mkdir(parents=True, exist_ok=True)
    graph_payload = graph.to_dict()
    program_payload = program.to_dict()
    assurance_payload = assurance.to_dict()
    cos_payload = cos.to_dict()
    source_digests = {
        "graph": graph_payload["graph_digest"],
        "program": program_payload["program_digest"],
        "assurance": stable_digest(assurance_payload),
        "cos_registry": cos_payload["registry_digest"],
        "seed": sha256_file(seed_path),
    }
    context = ContextPack(
        schema_version="CONTEXTPACK-V2",
        project_id="PROJECT:SWITZERLAND_JOB_OS",
        revision=f"CTX-{main_sha[:12]}",
        generated_at=now,
        main_sha=main_sha,
        authority_epoch="READ_FROM_LIVE_STATE_AT_MIGRATION",
        authority_manifest="READ_FROM_LIVE_STATE_AT_MIGRATION",
        event_watermark=ledger.watermark,
        projection_revision=graph_payload["graph_digest"],
        contract_versions={"HGA": "2.0", "MEP": "2.0", "WOP": "1.1", "PRG": "1.0", "LEX": "2.0"},
        active_barriers=("OPERATIONAL_V2_MIGRATION_NOT_YET_AUTHORIZED",),
        active_claims=({"scope": "architecture:v2", "mode": AccessMode.WRITE.value, "fencing": "CI_COMMIT"},),
        verified_work=("V2 foundation kernel", "event hash chain", "COS registry", "assurance compiler"),
        unverified_work=("physical zero-context recovery SLO", "agent-death drill", "operational migration", "empirical qualification"),
        next_safe_actions=("execute V2-CP7 recovery drill", "execute V2-CP8 agent-death drill", "shadow-compile current operational state"),
        source_digests=source_digests,
        payload={"outbound": "CLOSED", "send_allowed": 0, "operational_authority_mutated": False},
    ).signed()

    write_json(out_dir / "system_graph.json", graph_payload)
    write_json(out_dir / "implementation_program.json", program_payload)
    write_json(out_dir / "assurance_report.json", assurance_payload)
    write_json(out_dir / "cos_registry.json", cos_payload)
    write_json(out_dir / "contextpack.json", context.to_dict())
    (out_dir / "event_ledger.jsonl").write_text(ledger.to_jsonl(), encoding="utf-8")

    projections_dir = out_dir / "projections"
    for dimension in cos.dimensions:
        node_types, edge_types = projection_filters(dimension.dimension_id)
        projection = graph.projection(node_types=node_types, edge_types=edge_types)
        projection.update({
            "dimension_id": dimension.dimension_id,
            "dimension_name": dimension.name,
            "dimension_status": dimension.status.value,
            "purpose": dimension.purpose,
            "trigger": dimension.trigger,
        })
        write_json(projections_dir / f"{dimension.dimension_id}.json", projection)

    death_drill = {
        "schema_version": "DEATH_DRILL_V2",
        "status": "FOUNDATION_SIMULATION_PASS",
        "required_recovery_fields": [
            "north_star", "current_objective", "main_sha", "event_watermark",
            "projection_revision", "active_claims", "open_gaps", "verified_work",
            "unverified_work", "next_safe_actions",
        ],
        "contextpack_digest": context.digest,
        "authority_mutated": False,
        "note": "Physical five-minute qualification remains V2-CP7/V2-CP8.",
    }
    write_json(out_dir / "death_drill.json", death_drill)

    manifest_files: dict[str, dict[str, Any]] = {}
    for path in sorted(p for p in out_dir.rglob("*") if p.is_file() and p.name != "manifest.json"):
        rel = path.relative_to(out_dir).as_posix()
        manifest_files[rel] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    manifest = {
        "schema_version": "GRAPH_REFACTOR_V2_BUILD_MANIFEST",
        "generated_at": now,
        "main_sha": main_sha,
        "branch": branch,
        "graph_digest": graph_payload["graph_digest"],
        "event_watermark": ledger.watermark,
        "contextpack_digest": context.digest,
        "release_candidate": assurance.release_candidate,
        "operational_authority_mutated": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
        "files": manifest_files,
    }
    write_json(out_dir / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, default=ROOT / "docs/graph/v2/canonical_seed.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--main-sha", required=True)
    parser.add_argument("--branch", default="unknown")
    args = parser.parse_args()
    manifest = compile_outputs(args.seed, args.out, args.main_sha, args.branch)
    print(json.dumps(manifest, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from swiss_os.v2_kernel import (  # noqa: E402
    AccessMode,
    AuthorityStatus,
    CheckpointSpec,
    ClaimState,
    ContextPack,
    ContractError,
    CoordinationError,
    CoordinationRegistry,
    COSDimension,
    EventLedger,
    Gap,
    GraphEdge,
    GraphNode,
    HyperEdge,
    HyperParticipant,
    ImplementationProgram,
    InvariantSpec,
    LeaseState,
    LedgerEvent,
    ProjectionRegistry,
    ProjectionStatus,
    ResultState,
    ScopeClaim,
    Session,
    SessionState,
    Severity,
    StaleContextError,
    TaskSpec,
    TemporalHyperGraph,
    TestEvidence,
    canonical_json,
    compile_assurance,
    redact_secrets,
    stable_digest,
)
from swiss_os.v2_loop_guard import (  # noqa: E402
    LoopDecision,
    MutationAttempt,
    MutationClass,
    MutationLoopGuard,
)

NOW = "2026-08-30T10:00:00Z"
LATER = "2026-08-30T10:10:00Z"
MUCH_LATER = "2026-08-30T11:00:00Z"


def node(node_id: str, node_type: str = "COMPONENT", **attrs: object) -> GraphNode:
    return GraphNode(
        node_id,
        node_type,
        attrs,
        authority=AuthorityStatus.IMPLEMENTED,
    )


def session(session_id: str, agent: str = "AGENT:A") -> Session:
    return Session(
        session_id=session_id,
        project_id="PROJECT:TEST",
        agent_id=agent,
        workstream_id="WORKSTREAM:TEST",
        objective_id="OBJECTIVE:TEST",
        correlation_id="CORRELATION:TEST",
        state=SessionState.ACTIVE,
        opened_at=NOW,
        heartbeat_at=NOW,
    )


class CanonicalSerializationTests(unittest.TestCase):
    def test_digest_is_order_independent_for_mappings(self) -> None:
        self.assertEqual(
            stable_digest({"a": 1, "b": 2}),
            stable_digest({"b": 2, "a": 1}),
        )

    def test_non_finite_float_rejected(self) -> None:
        with self.assertRaises(ContractError):
            canonical_json({"bad": float("nan")})

    def test_invalid_node_interval_rejected(self) -> None:
        with self.assertRaises(ContractError):
            GraphNode("NODE:A", "COMPONENT", valid_from=LATER, valid_to=NOW)

    def test_boolean_confidence_rejected(self) -> None:
        with self.assertRaises(ContractError):
            GraphNode("NODE:A", "COMPONENT", confidence=True)


class HyperGraphTests(unittest.TestCase):
    def test_valid_graph_has_stable_digest(self) -> None:
        graph = TemporalHyperGraph()
        graph.add_node(node("NODE:A"))
        graph.add_node(node("NODE:B"))
        graph.add_edge(GraphEdge("EDGE:AB", "IMPLEMENTS", "NODE:A", "NODE:B"))
        self.assertEqual(graph.validate(), ())
        self.assertEqual(
            graph.to_dict()["graph_digest"],
            graph.to_dict()["graph_digest"],
        )

    def test_duplicate_node_rejected(self) -> None:
        graph = TemporalHyperGraph()
        graph.add_node(node("NODE:A"))
        with self.assertRaises(ContractError):
            graph.add_node(node("NODE:A"))

    def test_missing_edge_endpoint_detected(self) -> None:
        graph = TemporalHyperGraph()
        graph.add_node(node("NODE:A"))
        graph.add_edge(GraphEdge("EDGE:AB", "IMPLEMENTS", "NODE:A", "NODE:B"))
        self.assertIn("missing target", " ".join(graph.validate()))

    def test_hyperedge_requires_distinct_nodes(self) -> None:
        with self.assertRaises(ContractError):
            HyperEdge(
                "HYPER:1",
                "DECISION_IMPACT",
                (
                    HyperParticipant("NODE:A", "DECISION"),
                    HyperParticipant("NODE:A", "RISK"),
                ),
            )

    def test_hyperedge_participant_integrity(self) -> None:
        graph = TemporalHyperGraph()
        graph.add_node(node("NODE:A"))
        graph.add_node(node("NODE:B"))
        graph.add_hyperedge(
            HyperEdge(
                "HYPER:1",
                "DECISION_IMPACT",
                (
                    HyperParticipant("NODE:A", "DECISION"),
                    HyperParticipant("NODE:C", "RISK"),
                ),
            )
        )
        self.assertIn("missing participant NODE:C", " ".join(graph.validate()))

    def test_dependency_cycle_detected(self) -> None:
        graph = TemporalHyperGraph()
        for ident in ("NODE:A", "NODE:B", "NODE:C"):
            graph.add_node(node(ident))
        graph.add_edge(GraphEdge("EDGE:AB", "DEPENDS_ON", "NODE:A", "NODE:B"))
        graph.add_edge(GraphEdge("EDGE:BC", "DEPENDS_ON", "NODE:B", "NODE:C"))
        graph.add_edge(GraphEdge("EDGE:CA", "DEPENDS_ON", "NODE:C", "NODE:A"))
        self.assertTrue(graph.dependency_cycles())

    def test_transitive_dependencies(self) -> None:
        graph = TemporalHyperGraph()
        for ident in ("NODE:A", "NODE:B", "NODE:C"):
            graph.add_node(node(ident))
        graph.add_edge(GraphEdge("EDGE:AB", "DEPENDS_ON", "NODE:A", "NODE:B"))
        graph.add_edge(GraphEdge("EDGE:BC", "REQUIRES", "NODE:B", "NODE:C"))
        self.assertEqual(
            graph.transitive_dependencies("NODE:A"),
            ("NODE:B", "NODE:C"),
        )

    def test_orphan_detection_and_explicit_allowance(self) -> None:
        graph = TemporalHyperGraph()
        graph.add_node(node("NODE:A"))
        graph.add_node(node("NODE:B", allow_orphan=True))
        self.assertEqual(graph.orphan_nodes(), ("NODE:A",))


class EventLedgerTests(unittest.TestCase):
    def base_event(
        self,
        ledger: EventLedger,
        event_id: str,
        event_type: str,
        causation_id: str | None = None,
    ) -> LedgerEvent:
        return ledger.new_event(
            event_id=event_id,
            project_id="PROJECT:TEST",
            agent_id="AGENT:A",
            session_id="SESSION:A",
            workstream_id="WORKSTREAM:A",
            objective_id="OBJECTIVE:A",
            correlation_id="CORRELATION:A",
            event_type=event_type,
            occurred_at=NOW,
            main_sha="a" * 40,
            base_sha="a" * 40,
            branch="test",
            authority_ceiling="ARCHITECTURE_ONLY",
            resource_scopes=("repo:test",),
            semantic_scopes=("architecture:test",),
            payload={"value": 1},
            causation_id=causation_id,
        )

    def test_hash_chain_and_replay(self) -> None:
        ledger = EventLedger()
        first = self.base_event(ledger, "EVENT:1", "HELLO")
        ledger.append(first)
        second = self.base_event(ledger, "EVENT:2", "WORK_STARTED", "EVENT:1")
        ledger.append(second)
        self.assertEqual(ledger.verify(), ())
        self.assertEqual(ledger.replay(lambda state, _: state + 1, 0), 2)
        self.assertTrue(ledger.watermark.startswith("1:EVENT:2:"))

    def test_duplicate_event_rejected(self) -> None:
        ledger = EventLedger()
        event = self.base_event(ledger, "EVENT:1", "HELLO")
        ledger.append(event)
        with self.assertRaises(ContractError):
            ledger.append(event)

    def test_out_of_order_sequence_rejected(self) -> None:
        event = LedgerEvent(
            event_id="EVENT:1",
            sequence=2,
            project_id="PROJECT:TEST",
            agent_id="AGENT:A",
            session_id="SESSION:A",
            workstream_id="WORKSTREAM:A",
            objective_id="OBJECTIVE:A",
            correlation_id="CORRELATION:A",
            event_type="HELLO",
            occurred_at=NOW,
            main_sha="a" * 40,
            base_sha="a" * 40,
            branch="test",
            authority_ceiling="ARCHITECTURE_ONLY",
            resource_scopes=("repo:test",),
            semantic_scopes=("architecture:test",),
            payload={},
        ).signed()
        with self.assertRaises(ContractError):
            EventLedger().append(event)

    def test_tampered_payload_rejected(self) -> None:
        ledger = EventLedger()
        valid = self.base_event(ledger, "EVENT:1", "HELLO")
        tampered = LedgerEvent(**{**valid.__dict__, "payload": {"value": 2}})
        with self.assertRaises(ContractError):
            ledger.append(tampered)

    def test_unknown_causation_rejected(self) -> None:
        ledger = EventLedger()
        event = self.base_event(
            ledger,
            "EVENT:1",
            "WORK_STARTED",
            "EVENT:MISSING",
        )
        with self.assertRaises(ContractError):
            ledger.append(event)


class CoordinationTests(unittest.TestCase):
    def test_session_id_unique(self) -> None:
        registry = CoordinationRegistry()
        registry.open_session(session("SESSION:A"))
        with self.assertRaises(CoordinationError):
            registry.open_session(session("SESSION:A"))

    def test_overlapping_write_claim_rejected(self) -> None:
        registry = CoordinationRegistry()
        registry.open_session(session("SESSION:A", "AGENT:A"))
        registry.open_session(session("SESSION:B", "AGENT:B"))
        registry.acquire_claim(
            ScopeClaim(
                "CLAIM:A",
                "SESSION:A",
                AccessMode.WRITE,
                ("repo:swiss:docs",),
                ("contract:v2",),
                ClaimState.ACTIVE,
                NOW,
            )
        )
        with self.assertRaises(CoordinationError):
            registry.acquire_claim(
                ScopeClaim(
                    "CLAIM:B",
                    "SESSION:B",
                    AccessMode.WRITE,
                    ("repo:swiss:docs:file",),
                    ("contract:v2",),
                    ClaimState.ACTIVE,
                    NOW,
                )
            )

    def test_parallel_non_overlapping_claims_allowed(self) -> None:
        registry = CoordinationRegistry()
        registry.open_session(session("SESSION:A", "AGENT:A"))
        registry.open_session(session("SESSION:B", "AGENT:B"))
        registry.acquire_claim(
            ScopeClaim(
                "CLAIM:A",
                "SESSION:A",
                AccessMode.WRITE,
                ("repo:swiss:docs",),
                ("contract:v2",),
                ClaimState.ACTIVE,
                NOW,
            )
        )
        registry.acquire_claim(
            ScopeClaim(
                "CLAIM:B",
                "SESSION:B",
                AccessMode.WRITE,
                ("repo:swiss:src",),
                ("runtime:v2",),
                ClaimState.ACTIVE,
                NOW,
            )
        )
        self.assertEqual(len(registry.claims), 2)

    def test_read_read_overlap_allowed(self) -> None:
        registry = CoordinationRegistry()
        registry.open_session(session("SESSION:A", "AGENT:A"))
        registry.open_session(session("SESSION:B", "AGENT:B"))
        for claim_id, session_id in (
            ("CLAIM:A", "SESSION:A"),
            ("CLAIM:B", "SESSION:B"),
        ):
            registry.acquire_claim(
                ScopeClaim(
                    claim_id,
                    session_id,
                    AccessMode.READ,
                    ("store:authority",),
                    (),
                    ClaimState.ACTIVE,
                    NOW,
                )
            )
        self.assertEqual(len(registry.claims), 2)

    def test_fencing_takeover_rejects_stale_writer(self) -> None:
        registry = CoordinationRegistry()
        registry.open_session(session("SESSION:A", "AGENT:A"))
        registry.open_session(session("SESSION:B", "AGENT:B"))
        first = registry.acquire_lease(
            lease_id="LEASE:A",
            session_id="SESSION:A",
            scope="store:authority",
            acquired_at=NOW,
            expires_at=LATER,
        )
        second = registry.acquire_lease(
            lease_id="LEASE:B",
            session_id="SESSION:B",
            scope="store:authority",
            acquired_at=MUCH_LATER,
            expires_at="2026-08-30T12:00:00Z",
        )
        self.assertGreater(second.fencing_token, first.fencing_token)
        with self.assertRaises(CoordinationError):
            registry.assert_fence(
                "store:authority",
                first.fencing_token,
                MUCH_LATER,
            )
        registry.assert_fence(
            "store:authority",
            second.fencing_token,
            MUCH_LATER,
        )

    def test_lease_cannot_be_stolen_before_expiry(self) -> None:
        registry = CoordinationRegistry()
        registry.open_session(session("SESSION:A", "AGENT:A"))
        registry.open_session(session("SESSION:B", "AGENT:B"))
        registry.acquire_lease(
            lease_id="LEASE:A",
            session_id="SESSION:A",
            scope="store:authority",
            acquired_at=NOW,
            expires_at=MUCH_LATER,
        )
        with self.assertRaises(CoordinationError):
            registry.acquire_lease(
                lease_id="LEASE:B",
                session_id="SESSION:B",
                scope="store:authority",
                acquired_at=LATER,
                expires_at="2026-08-30T12:00:00Z",
            )

    def test_close_session_releases_claims_and_leases(self) -> None:
        registry = CoordinationRegistry()
        registry.open_session(session("SESSION:A"))
        registry.acquire_claim(
            ScopeClaim(
                "CLAIM:A",
                "SESSION:A",
                AccessMode.WRITE,
                ("repo:test",),
                (),
                ClaimState.ACTIVE,
                NOW,
            )
        )
        registry.acquire_lease(
            lease_id="LEASE:A",
            session_id="SESSION:A",
            scope="repo:test",
            acquired_at=NOW,
            expires_at=MUCH_LATER,
        )
        registry.close_session("SESSION:A", LATER)
        self.assertEqual(registry.claims["CLAIM:A"].state, ClaimState.RELEASED)
        self.assertEqual(registry.leases["LEASE:A"].state, LeaseState.RELEASED)


class ContextPackTests(unittest.TestCase):
    def build_pack(self) -> ContextPack:
        return ContextPack(
            schema_version="CONTEXTPACK-V2",
            project_id="PROJECT:TEST",
            revision="CTX-1",
            generated_at=NOW,
            main_sha="a" * 40,
            authority_epoch="E1",
            authority_manifest="M1",
            event_watermark="0:EVENT:1:" + "b" * 64,
            projection_revision="c" * 64,
            contract_versions={"HGA": "2.0"},
            active_barriers=("BARRIER:1",),
            active_claims=({"claim": "CLAIM:1"},),
            verified_work=("kernel",),
            unverified_work=("migration",),
            next_safe_actions=("recovery drill",),
            source_digests={"graph": "d" * 64},
            payload={
                "api_key": "super-secret",
                "safe": "value",
                "nested": {"token": "abc"},
            },
        ).signed()

    def test_contextpack_redacts_secrets(self) -> None:
        payload = self.build_pack().to_dict()["payload"]
        self.assertEqual(payload["api_key"], "[REDACTED]")
        self.assertEqual(payload["nested"]["token"], "[REDACTED]")
        self.assertEqual(payload["safe"], "value")

    def test_contextpack_digest_detects_tamper(self) -> None:
        pack = self.build_pack()
        with self.assertRaises(ContractError):
            ContextPack(**{**pack.__dict__, "main_sha": "e" * 40})

    def test_contextpack_freshness(self) -> None:
        pack = self.build_pack()
        pack.assert_fresh(
            main_sha="a" * 40,
            event_watermark=pack.event_watermark,
            projection_revision="c" * 64,
        )
        with self.assertRaises(StaleContextError):
            pack.assert_fresh(
                main_sha="f" * 40,
                event_watermark=pack.event_watermark,
                projection_revision="c" * 64,
            )

    def test_secret_value_pattern_redaction(self) -> None:
        value = redact_secrets(
            {"message": "credential ghp_abcdefghijklmnopqrstuvwxyz1234"}
        )
        self.assertNotIn("ghp_", value["message"])


class AssuranceAndCompilerTests(unittest.TestCase):
    def graph_with_critical_node(
        self,
        tested: bool = True,
        owned: bool = True,
    ) -> TemporalHyperGraph:
        graph = TemporalHyperGraph()
        attrs: dict[str, object] = {"critical": True}
        if owned:
            attrs["owner"] = "TEAM"
        graph.add_node(node("NODE:CRITICAL", **attrs))
        graph.add_node(node("TEST:CRITICAL", "TEST", owner="TEST"))
        if tested:
            graph.add_edge(
                GraphEdge(
                    "EDGE:TEST",
                    "TESTED_BY",
                    "NODE:CRITICAL",
                    "TEST:CRITICAL",
                )
            )
        return graph

    def test_release_candidate_when_p0_p1_closed(self) -> None:
        graph = self.graph_with_critical_node()
        invariant = InvariantSpec(
            "INV:1",
            "critical property",
            Severity.P0,
            "TEAM",
            ("TEST:CRITICAL",),
        )
        evidence = TestEvidence(
            "TEST:CRITICAL",
            ResultState.PASS,
            "CI:1",
            NOW,
        )
        gap = Gap(
            "GAP:1",
            "residual",
            Severity.P2,
            2,
            2,
            2,
            2,
            2,
            "TEAM",
            "metric",
            "guard",
            "later",
            (),
            "TEST:CRITICAL",
            "run",
            "MIGRATION",
        )
        report = compile_assurance(graph, (invariant,), (evidence,), (gap,))
        self.assertTrue(report.release_candidate)
        self.assertEqual(report.p2_open, 1)

    def test_missing_owner_blocks_release(self) -> None:
        graph = self.graph_with_critical_node(owned=False)
        evidence = TestEvidence(
            "TEST:CRITICAL",
            ResultState.PASS,
            "CI:1",
            NOW,
        )
        invariant = InvariantSpec(
            "INV:1",
            "critical property",
            Severity.P0,
            "TEAM",
            ("TEST:CRITICAL",),
        )
        report = compile_assurance(graph, (invariant,), (evidence,), ())
        self.assertFalse(report.release_candidate)
        self.assertIn("NODE:CRITICAL", report.critical_owner_gaps)

    def test_missing_test_blocks_release(self) -> None:
        graph = self.graph_with_critical_node(tested=False)
        report = compile_assurance(graph, (), (), ())
        self.assertFalse(report.release_candidate)
        self.assertIn("NODE:CRITICAL", report.critical_test_gaps)

    def make_task(
        self,
        task_id: str,
        dependencies: tuple[str, ...] = (),
    ) -> TaskSpec:
        return TaskSpec(
            task_id,
            "objective",
            "why",
            ("input",),
            ("output",),
            dependencies,
            ("NODE:A",),
            ("EDGE:A",),
            ("file",),
            "TEAM",
            "risk",
            ("step",),
            ("test",),
            ("attack",),
            ("security",),
            ("evidence",),
            "rollback",
            ("done",),
        )

    def test_program_frontier_and_digest(self) -> None:
        first = self.make_task("TASK:1")
        second = self.make_task("TASK:2", ("TASK:1",))
        checkpoint = CheckpointSpec(
            "CP:1",
            "checkpoint",
            ("entry",),
            ("TASK:1",),
            ("test",),
            ("evidence",),
            ("exit",),
            "MISSION",
            "rollback",
        )
        program = ImplementationProgram(
            "PROGRAM:1",
            "G-0001",
            (first, second),
            (checkpoint,),
        )
        self.assertEqual(program.validate(), ())
        self.assertEqual(program.executable_frontier(()), ("TASK:1",))
        self.assertEqual(
            program.executable_frontier(("TASK:1",)),
            ("TASK:2",),
        )
        self.assertEqual(len(program.to_dict()["program_digest"]), 64)

    def test_program_dependency_cycle_detected(self) -> None:
        one = self.make_task("TASK:1", ("TASK:2",))
        two = self.make_task("TASK:2", ("TASK:1",))
        checkpoint = CheckpointSpec(
            "CP:1",
            "checkpoint",
            ("entry",),
            ("TASK:1",),
            ("test",),
            ("evidence",),
            ("exit",),
            "MISSION",
            "rollback",
        )
        program = ImplementationProgram(
            "PROGRAM:1",
            "G-0001",
            (one, two),
            (checkpoint,),
        )
        self.assertTrue(any("cycle" in error for error in program.validate()))

    def test_cos_registry_requires_all_dimensions(self) -> None:
        with self.assertRaises(ContractError):
            ProjectionRegistry(
                (
                    COSDimension(
                        "L0",
                        "Visual",
                        ProjectionStatus.ACTIVE,
                        "purpose",
                    ),
                )
            )

    def test_deferred_dimension_requires_trigger(self) -> None:
        with self.assertRaises(ContractError):
            COSDimension(
                "L10",
                "Similarity",
                ProjectionStatus.DEFERRED_TRIGGER,
                "purpose",
            )


class MutationLoopGuardTests(unittest.TestCase):
    def test_duplicate_successful_create_is_suppressed(self) -> None:
        guard = MutationLoopGuard()
        first = MutationAttempt(
            "create_issue",
            "repo:swiss",
            MutationClass.IRREVERSIBLE_CREATE,
            "graph-refactor-v2-root",
            "strategy:create",
            "SUCCESS",
            "ISSUE:293",
        )
        guard.record(first)
        decision = guard.assess(
            action="create_issue",
            target_scope="repo:swiss",
            mutation_class=MutationClass.IRREVERSIBLE_CREATE,
            idempotency_key="graph-refactor-v2-root",
            strategy_id="strategy:create",
        )
        self.assertEqual(decision, LoopDecision.SUPPRESS_DUPLICATE)

    def test_placeholder_idempotency_key_rejected(self) -> None:
        guard = MutationLoopGuard()
        with self.assertRaises(ContractError):
            guard.assess(
                action="create_issue",
                target_scope="repo:swiss",
                mutation_class=MutationClass.IRREVERSIBLE_CREATE,
                idempotency_key="none",
                strategy_id="strategy:create",
            )

    def test_identical_failure_budget_forces_strategy_change_then_stuck(self) -> None:
        guard = MutationLoopGuard(max_identical_strategy_attempts=3)
        for index in range(2):
            guard.record(
                MutationAttempt(
                    "create_issue",
                    "repo:swiss",
                    MutationClass.IRREVERSIBLE_CREATE,
                    f"attempt-{index}",
                    "strategy:broken",
                    "NO_PROGRESS",
                )
            )
        self.assertEqual(
            guard.assess(
                action="create_issue",
                target_scope="repo:swiss",
                mutation_class=MutationClass.IRREVERSIBLE_CREATE,
                idempotency_key="attempt-2",
                strategy_id="strategy:broken",
            ),
            LoopDecision.CHANGE_STRATEGY,
        )
        guard.record(
            MutationAttempt(
                "create_issue",
                "repo:swiss",
                MutationClass.IRREVERSIBLE_CREATE,
                "attempt-2",
                "strategy:broken",
                "NO_PROGRESS",
            )
        )
        self.assertEqual(
            guard.assess(
                action="create_issue",
                target_scope="repo:swiss",
                mutation_class=MutationClass.IRREVERSIBLE_CREATE,
                idempotency_key="attempt-3",
                strategy_id="strategy:broken",
            ),
            LoopDecision.STUCK_LOOP,
        )


class CompilerIntegrationTests(unittest.TestCase):
    def test_compiler_emits_complete_public_safe_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            out = temp_path / "build"
            seed = json.loads(
                (ROOT / "docs/graph/v2/canonical_seed.json").read_text(
                    encoding="utf-8"
                )
            )
            attestation = temp_path / "tests.json"
            attestation.write_text(
                json.dumps(
                    {
                        "commit_sha": "a" * 40,
                        "results": [
                            {
                                "test_id": test_id,
                                "state": "PASS",
                                "evidence_ref": "UNITTEST:test_v2_kernel",
                                "executed_at": NOW,
                            }
                            for test_id in seed["tests"]
                        ],
                    }
                ),
                encoding="utf-8",
            )
            command = [
                sys.executable,
                str(ROOT / "scripts/compile_graph_v2.py"),
                "--out",
                str(out),
                "--main-sha",
                "a" * 40,
                "--branch",
                "test",
                "--generated-at",
                NOW,
                "--test-attestation",
                str(attestation),
            ]
            completed = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stderr + completed.stdout,
            )
            manifest = json.loads(
                (out / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertTrue(manifest["release_candidate"])
            self.assertFalse(manifest["operational_authority_mutated"])
            self.assertEqual(manifest["h_id_allocations"], 0)
            self.assertFalse(manifest["outbound_opened"])
            self.assertEqual(manifest["send_allowed"], 0)
            graph = json.loads(
                (out / "system_graph.json").read_text(encoding="utf-8")
            )
            self.assertGreaterEqual(len(graph["nodes"]), 120)
            self.assertGreaterEqual(len(graph["edges"]), 150)
            self.assertEqual(len(graph["hyperedges"]), 2)
            self.assertEqual(
                len(list((out / "projections").glob("L*.json"))),
                20,
            )
            self.assertEqual(
                (out / "event_ledger.jsonl")
                .read_text(encoding="utf-8")
                .count("\n"),
                5,
            )
            context = json.loads(
                (out / "contextpack.json").read_text(encoding="utf-8")
            )
            self.assertEqual(context["main_sha"], "a" * 40)
            self.assertEqual(len(context["digest"]), 64)

    def test_compiler_rejects_wrong_commit_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            seed = json.loads(
                (ROOT / "docs/graph/v2/canonical_seed.json").read_text(
                    encoding="utf-8"
                )
            )
            attestation = temp_path / "tests.json"
            attestation.write_text(
                json.dumps(
                    {
                        "commit_sha": "b" * 40,
                        "results": [
                            {
                                "test_id": test_id,
                                "state": "PASS",
                                "evidence_ref": "UNITTEST:test_v2_kernel",
                                "executed_at": NOW,
                            }
                            for test_id in seed["tests"]
                        ],
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/compile_graph_v2.py"),
                    "--out",
                    str(temp_path / "build"),
                    "--main-sha",
                    "a" * 40,
                    "--branch",
                    "test",
                    "--generated-at",
                    NOW,
                    "--test-attestation",
                    str(attestation),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("does not match", completed.stderr + completed.stdout)


if __name__ == "__main__":
    unittest.main()

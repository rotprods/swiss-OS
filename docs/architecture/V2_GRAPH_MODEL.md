# COS 20D V2 GRAPH MODEL

**Authority:** canonical project-memory graph ontology; operational hotel graph remains separate.

## Node ontology

Core: Project, Program, NorthStar, Goal, Objective, Milestone, Phase, Wave, Workstream, Task, Checkpoint, DefinitionOfDone, AcceptanceCriterion, Metric, KPI, SLO.

Engineering: Repository, Branch, Commit, PullRequest, Release, File, Directory, Module, Function, Class, Interface, API, CLI, Workflow, Pipeline, Runtime, Environment, Provider, Tool, Dependency, InfrastructureComponent.

Architecture: Architecture, Subsystem, Component, Boundary, Contract, Schema, Protocol, Event, Command, Outcome, State, Projection, Reducer, Adapter, Gateway, Store, Cache, Index, Graph, GraphProjection, ContextPack.

Knowledge: Fact, Claim, Assumption, Hypothesis, Insight, Concept, Term, Definition, Rule, Pattern, AntiPattern, Decision, Alternative, RejectedAlternative, Tradeoff, Constraint, Requirement.

Reliability/security: Bug, Regression, Failure, FailureMode, Incident, Risk, Threat, AttackSurface, Bottleneck, SinglePointOfFailure, TechnicalDebt, RefactorOpportunity, RecoveryProcedure, Rollback, Invariant.

Testing/evidence: Test, TestSuite, TestRun, Fixture, Benchmark, Experiment, Simulation, Gauntlet, PropertyTest, MutationTest, Evidence, Artifact, Measurement, Observation, Qualification.

Agentic: Agent, Session, Role, Capability, Claim, Lease, FencingToken, Handoff, Memory, Knowledge, ToolInvocation, ContextWindow, EventWatermark, Authority.

Domain nodes remain native: Hotel, SourceRecord, Alias, Group, Vacancy, Person, Channel, Housing, Audit, Opportunity, Proposal, Application, Outcome and their existing PKs.

## Edge ontology

Causality: CAUSES, CAUSED_BY, CONTRIBUTES_TO, TRIGGERS, PREVENTS, ENABLES, DISABLES, AMPLIFIES, REDUCES.

Dependency: DEPENDS_ON, REQUIRED_BY, BLOCKS, BLOCKED_BY, UNBLOCKS, PRECEDES, FOLLOWS, REQUIRES, OPTIONALLY_REQUIRES.

Implementation: IMPLEMENTS, IMPLEMENTED_BY, CALLS, CALLED_BY, READS, WRITES, MODIFIES, GENERATES, CONSUMES, PRODUCES, TRANSFORMS, ROUTES_TO.

Contract: DEFINES, CONSTRAINS, VALIDATES, CONFORMS_TO, BREAKS, EXTENDS, VERSION_OF, SUPERSEDES, DEPRECATED_BY.

Evidence: PROVES, SUPPORTED_BY, MEASURED_BY, OBSERVED_BY, TESTED_BY, FAILED_BY, VERIFIED_BY, QUALIFIED_BY, CONTRADICTED_BY.

Agentic: OWNED_BY, CLAIMED_BY, EXECUTED_BY, DELEGATED_TO, HANDOFF_TO, RESUMES_FROM, COLLIDES_WITH, SHARES_SCOPE_WITH, WAITS_FOR.

Architecture: CONTAINS, PART_OF, CONNECTED_TO, EXPOSES, ISOLATES, BRIDGES, PROJECTS_TO, DERIVED_FROM, SOURCE_OF_TRUTH_FOR, CACHE_OF.

Decision: CHOSEN_OVER, REJECTED_BECAUSE, JUSTIFIED_BY, ASSUMES, RISKS, MITIGATES, CONFLICTS_WITH, ALTERNATIVE_TO.

Temporal: PREVIOUS_VERSION, NEXT_VERSION, VALID_FROM, VALID_UNTIL, SUPERSEDED_AT, EXPIRED_AT, CREATED_AT, VERIFIED_AT.

Improvement: REFACTOR_OF, OPTIMIZES, SIMPLIFIES, GENERALIZES, SPECIALIZES, REMOVES_DUPLICATION_OF, REDUCES_RISK_OF, IMPROVES.

Every significant edge carries type, authority, confidence, validity, source, version, criticality and—when relevant—latency/cost/risk.

## Hyperrelations

Use a first-class hyperrelation when one change simultaneously affects multiple contracts/modules/tests/risks/migrations/goals. Never flatten a many-party authority transaction into misleading pairwise causality.

## Required graph projections

System, Architecture, Dependency, Execution, Agent, Session, Knowledge, Decision, Risk, Test, Evidence, Artifact, Workflow, State, Recovery, Security, Historical and Roadmap graphs all derive from shared IDs. `docs/state/v2/graph-snapshot.json` is a bootstrap projection, not operational hotel authority.

## COS dimensions

| Layer | V2 projection / decision |
|---|---|
| L0 Visual | Mermaid/text projections generated from canonical IDs; overloaded hubs/orphans are audit targets. |
| L1 Execution | Goal→Objective→Task→Test→Evidence→Checkpoint DAG. |
| L2 State | Session/Claim/Task/Release/Authority state machines. |
| L3 Dependency | task/module/contract transitive blast radius; cycles require justification. |
| L4 Call | Python module/function call graph; domain code retained unless coupling defect measured. |
| L5 Control | fail-closed branches, authority ceilings, error paths, state transitions. |
| L6 DataFlow | source→evidence→decision→authority plus event→projection→ContextPack. |
| L7 Compute | event replay linear; active-claim collision small-set; no distributed compute justified. |
| L8 Knowledge | decisions/rules/evidence/domain facts connected to provenance. |
| L9 Semantic | canonical `LEXICON.md`; readiness/verification terms de-overloaded. |
| L10 Similarity | evidence triage only; similarity never identity authority. |
| L11 GraphRAG | zero-context retrieval questions define acceptance tests; implementation can reuse graph exports before adding a vector store. |
| L12 Memory | ephemeral/working/project/procedural/historical/long-lived/deprecated classes with revision invalidation. |
| L13 Agent | Agent→Session→Claim→Task→Handoff/collision. |
| L14 Tool | tool capability/trust/fallback/permission graph. |
| L15 Workflow | COLETTE/WOP + compensation/idempotency/retry semantics. |
| L16 Network | NOT_APPLICABLE at current deployment scale beyond external provider boundaries. |
| L17 | NOT_APPLICABLE until a domain-specific additional dimension is justified. |
| L18 | NOT_APPLICABLE until a domain-specific additional dimension is justified. |
| L19 | NOT_APPLICABLE until a domain-specific additional dimension is justified. |

## Current critical topology

```text
G-0001
 ├─ G-0500 ─BLOCKED_BY→ CRM universe incomplete
 │              ├─ requires terminal source mappings
 │              ├─ requires reverse-gap closure
 │              └─ provider structured SSR remains external-blocked
 ├─ G-0600
 ├─ G-0700
 └─ G-0800
       ↑
OBJ-GRAPH-REFACTOR-V2
 ├─ REDUCES_RISK_OF duplicate/stale agent coordination
 ├─ ISOLATES hotel authority
 └─ ENABLES zero-context continuation
```

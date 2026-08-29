# HYPERGRAPH ARCHITECTURE V2 — SWITZERLAND_JOB_OS

Version: **HGA-2.0**  
Status: **CANONICAL V2 ARCHITECTURE CANDIDATE**  
Authority: architecture contract; operational authority is unchanged until migration checkpoints pass  
Owner: Principal Systems Architect  
Last updated: 2026-08-30  
Supersedes: fragmented future-state proposals; historical facts remain immutable

## 1. North Star

```text
P(verified viable Swiss offer × Roberto accepts × relocation succeeds)
```

Hotel counts, source mappings, graph density, CI runs, PRs and automation volume are supporting signals, never final success.

## 2. Reconstructed current system

The refactor preserves the current durable system:

- constrained SQLite plus HOTELS_MASTER control-plane mirror;
- Operational Graph and Intelligence projections;
- frozen/member-directory source records and terminal-mapping pipeline;
- MEP-2.0 chained execution and WOP-1.1 transactional waves;
- source acquisition, exact-current validation, source reconciliation and alias semantics contracts;
- GitHub as public-safe code/contracts/CI authority;
- Drive and Library as operational/recovery surfaces under declared roles;
- independently closed outbound.

The current implementation is strong on domain integrity but lacks one universal executable model for causal history, first-class sessions/claims, stale-writer fencing, deterministic ContextPack freshness and architecture-wide assurance. V2 closes those gaps without replacing functioning domain engines.

## 3. Principles

1. Truth before convenience.
2. Append history; supersede semantics.
3. One concept, one authority.
4. Events explain change; state serves reads.
5. Material decisions use queryable hyperrelations.
6. Sessions and claims are durable data.
7. Fencing rejects stale writers.
8. Context is compiled, not remembered.
9. Tests prove named properties only.
10. No infrastructure without a measured trigger.
11. Confidence/similarity cannot grant authority.
12. Recovery is a product feature.

## 4. Planes and boundaries

### Authority plane

```text
PHYSICAL + CONSTRAINED AUTHORITY-ELIGIBLE STATE
> LIVE CONTROL PLANE
> VALIDATED AUTHORITY MANIFEST
> VERIFIED GRAPH / INTELLIGENCE PROJECTIONS
> GITHUB LIVE STATE POINTER
> HISTORICAL PROSE
```

Every event, session, claim, projection and artifact carries an `authority_ceiling` or equivalent boundary.

### Coordination plane

```text
Agent → Session → Claim → Lease → FencingToken → Heartbeat/Handoff
```

This plane controls who may mutate which scope and when. It is not hotel/domain truth.

### Event plane

The append-only causal envelope contains:

```text
event_id, sequence, project_id, agent_id, session_id,
workstream_id, objective_id, correlation_id, event_type,
occurred_at, main_sha, base_sha, branch, authority_ceiling,
resource_scopes, semantic_scopes, causation_id,
previous_event_hash, payload, event_hash
```

Events are canonical-JSON serialized, SHA-256 chained, schema-validated and replayable. Broken sequence, predecessor, causation or hash fails closed.

### Graph plane

- **PROJECT_MEMORY_META_GRAPH:** goals, checkpoints, waves, sessions, agents, claims, decisions, releases, contracts, risks, tests and artifacts.
- **OPERATIONAL_GRAPH:** hotels, source records, mappings, evidence, groups, vacancies, housing, people, channels, tasks, applications and outcomes.

The two scopes share IDs where they intersect. Meta Graph never impersonates Operational Graph.

### Projection plane

Read models are deterministic projections from declared sources and reducer versions:

```text
StateProjection, ExecutionProjection, DependencyProjection,
RiskProjection, AssuranceProjection, AgentProjection, ContextPack
```

Every projection records source watermark, revision and digest.

### Tool/provider plane

Tools and providers carry capability, permissions, trust boundary, availability, fallback, cost and failure modes. Capability outages change route selection, never historical truth.

## 5. Components

### C01 Domain Authority Stores

Existing constrained DB, HOTELS_MASTER and synchronized operational projections remain. V2 does not replace them.

### C02 Causal Event Ledger

Append-only JSONL plus deterministic verification API at foundation stage. It may later be mirrored into constrained tables without changing the contract.

### C03 Temporal Hypergraph Kernel

Typed nodes, directed edges and role-bearing hyperedges with:

```text
id/type, attributes, valid_from/valid_to, source_event/source_commit,
authority, confidence, provenance, superseded_by
```

### C04 Session / Claim / Lease Registry

- globally unique sessions;
- resource and semantic claims;
- overlap/collision policy;
- lease expiry and takeover;
- monotonic fencing tokens;
- stale-writer rejection.

### C05 ContextPack Compiler

Compiles a bounded zero-context packet from Git ancestry, authority, event watermark, projection revision, contract versions, barriers, claims, work/evidence and NEXT. It redacts secrets and rejects stale ancestry/watermarks.

### C06 Assurance Kernel

Rejects critical nodes without owner/test, critical invariants without PASS evidence, P0/P1 gaps without resolution and graph-integrity violations.

### C07 Implementation Compiler

Compiles:

```text
NorthStar → Program → Milestone → Phase → Wave → Task → Test → Evidence → Checkpoint
```

Every generated task includes objective, why, inputs/outputs, dependencies, affected graph/files, owner, risk, implementation/test/security steps, evidence, rollback and DoD.

### C08 COS Projection Registry

All L0–L19 dimensions are explicit as `ACTIVE`, `ACTIVE_LIGHT`, `ACTIVE_CONTRACT`, `DEFERRED_TRIGGER` or `NOT_APPLICABLE`.

### C09 Recovery Compiler

Builds manifests, source digests, ContextPack, event ledger, projections, implementation program and death-drill packet for GitHub Actions artifacts and durable recovery mirrors.

### C10 MEP/WOP/Domain Bridge

MEP chooses routes; WOP bounds waves; existing engines execute domain work. V2 coordinates and explains them rather than duplicating them.

## 6. Ontology

### Governance/product

```text
Project, Program, NorthStar, Goal, Objective, Milestone, Phase, Wave,
Workstream, Task, Subtask, Checkpoint, DefinitionOfDone,
AcceptanceCriterion, Metric, KPI, SLO, SLA
```

### Engineering

```text
Repository, Branch, Commit, PullRequest, Release, File, Directory,
Module, Package, Service, Function, Class, Interface, API, CLI,
Workflow, Pipeline, Runtime, Environment, Provider, Tool, Dependency,
InfrastructureComponent
```

### Architecture/state

```text
Architecture, Subsystem, Component, Boundary, Contract, Schema,
Protocol, Event, Command, Outcome, State, Projection, Reducer,
Adapter, Gateway, Queue, Store, Cache, Index, Graph,
GraphProjection, ContextPack
```

### Knowledge/decisions

```text
Fact, Claim, Assumption, Hypothesis, Insight, Idea, Concept, Term,
Definition, Rule, Heuristic, Pattern, AntiPattern, Decision,
Alternative, RejectedAlternative, Tradeoff, Constraint, Requirement
```

### Reliability/assurance

```text
Bug, Regression, Failure, FailureMode, Incident, Risk, Threat,
AttackSurface, Bottleneck, SinglePointOfFailure, TechnicalDebt,
RefactorOpportunity, RecoveryProcedure, Rollback, Invariant, Test,
TestSuite, TestRun, Fixture, Benchmark, Experiment, Simulation,
Gauntlet, FuzzCampaign, PropertyTest, MutationTest, Evidence,
Artifact, Measurement, Observation, Qualification
```

### Agentic

```text
Agent, Session, Role, Capability, Claim, Lease, FencingToken,
Handoff, Memory, Knowledge, ToolInvocation, ContextWindow,
EventWatermark, Authority
```

Domain-specific hotel/source/mapping/vacancy/housing/person/channel/application/offer nodes remain specialized.

## 7. Edge ontology

Canonical predicates:

```text
CAUSES, CONTRIBUTES_TO, TRIGGERS, PREVENTS, ENABLES, DISABLES,
AMPLIFIES, REDUCES, DEPENDS_ON, REQUIRED_BY, BLOCKS, BLOCKED_BY,
UNBLOCKS, PRECEDES, FOLLOWS, REQUIRES, OPTIONALLY_REQUIRES,
IMPLEMENTS, IMPLEMENTED_BY, CALLS, CALLED_BY, READS, WRITES,
MODIFIES, GENERATES, CONSUMES, PRODUCES, TRANSFORMS, ROUTES_TO,
DEFINES, CONSTRAINS, VALIDATES, CONFORMS_TO, BREAKS, EXTENDS,
VERSION_OF, SUPERSEDES, DEPRECATED_BY, PROVES, SUPPORTED_BY,
MEASURED_BY, OBSERVED_BY, TESTED_BY, FAILED_BY, VERIFIED_BY,
QUALIFIED_BY, CONTRADICTED_BY, OWNED_BY, CLAIMED_BY, EXECUTED_BY,
DELEGATED_TO, HANDOFF_TO, RESUMES_FROM, COLLIDES_WITH,
SHARES_SCOPE_WITH, WAITS_FOR, CONTAINS, PART_OF, CONNECTED_TO,
EXPOSES, ISOLATES, BRIDGES, PROJECTS_TO, DERIVED_FROM,
SOURCE_OF_TRUTH_FOR, CACHE_OF, CHOSEN_OVER, REJECTED_BECAUSE,
JUSTIFIED_BY, ASSUMES, RISKS, MITIGATES, CONFLICTS_WITH,
ALTERNATIVE_TO, PREVIOUS_VERSION, NEXT_VERSION, VALID_FROM,
VALID_UNTIL, REFACTOR_OF, OPTIMIZES, SIMPLIFIES, GENERALIZES,
SPECIALIZES, REMOVES_DUPLICATION_OF, REDUCES_RISK_OF, IMPROVES
```

Every material edge carries authority, confidence, source, version, criticality, temporal validity and optional latency/cost/risk.

## 8. Hyperrelations

A decision hyperedge can simultaneously connect:

```text
Decision → chosen alternative
         → modified contracts/components
         → invalidated or required tests
         → introduced/mitigated risks
         → migration tasks
         → evidence
```

Participants have explicit roles; hyperrelations cannot be opaque prose.

## 9. State machines

```text
Session: OPEN → ACTIVE → HANDOFF_PENDING → CLOSED | ABORTED
Claim: PROPOSED → ACTIVE → RELEASED | EXPIRED | REVOKED
Lease: ACQUIRED → RENEWED* → RELEASED | EXPIRED → TAKEOVER(new fence)
Event: PROPOSED → APPENDED → VERIFIED | CORRUPT/BLOCKED
Projection: BUILDING → CURRENT → STALE → REBUILDING → CURRENT | BLOCKED
Evidence: DISCOVERED → SCOPED → VERIFIED → EXPIRED | CONTRADICTED
```

Task completion remains evidence-gated; status text alone cannot close a task.

## 10. Data flow

```text
External source (UNTRUSTED)
→ adapter
→ schema/scope validation
→ evidence
→ command/wave/session/claim
→ constrained mutation or staging
→ causal event append
→ reducers
→ graph/state/ContextPack projections
→ invariants/assurance
→ authority eligibility
→ recovery persistence
```

Every transform preserves provenance, input digests and reducer version.

## 11. Single-source-of-truth matrix

| Concept | Authority | Projection/replica | Drift detection |
|---|---|---|---|
| Canonical hotels | constrained DB + synchronized control plane | Graph, Intelligence, STATE | PK/digest reconciliation |
| Frozen source records | frozen source artifact/manifest | staging, Graph | source-record conservation |
| Terminal mappings | constrained mapping state after promotion | Graph/Sheets/report | source-key set + digest |
| Goals/checkpoints | live control plane under authority rules | STATE/Meta Graph | revision/event reconciliation |
| Code/contracts | GitHub main | clone/CI artifact | commit SHA |
| Events | append-only ledger | projections | hash-chain verification |
| Claims/leases | coordination registry | ContextPack/Meta Graph | token/expiry/replay |
| ContextPack | no independent authority | Drive/Library/GitHub artifact | SHA/watermark/revision freshness |
| Recovery bundle | exact artifact manifest | Drive/Library | SHA + logical restore |

A new competing authority is a P0 defect.

## 12. COS 20D mapping

| L | Status | Projection |
|---|---|---|
| L0 | ACTIVE | visual clusters, hubs, orphans |
| L1 | ACTIVE | goal→task→test→evidence critical path |
| L2 | ACTIVE | state machines and transitions |
| L3 | ACTIVE | dependency DAG, cycles and blast radius |
| L4 | ACTIVE | module/function/tool ownership |
| L5 | ACTIVE | control flow, fallback and authority paths |
| L6 | ACTIVE | source→state→consumer provenance |
| L7 | ACTIVE_LIGHT | batch/replay/projection cost |
| L8 | ACTIVE | facts, decisions, rules and evidence |
| L9 | ACTIVE | lexicon and semantic collisions |
| L10 | DEFERRED_TRIGGER | similarity candidate generation only |
| L11 | ACTIVE_CONTRACT | zero-context GraphRAG qualification |
| L12 | ACTIVE | memory class, TTL, invalidation and history |
| L13 | ACTIVE | agents, sessions, claims, leases and handoffs |
| L14 | ACTIVE | tools, permissions, trust and fallback |
| L15 | ACTIVE | complete MEP/WOP/domain/recovery workflows |
| L16 | NOT_APPLICABLE | no internal distributed network today |
| L17 | ACTIVE_DOMAIN | offer economics when offers exist |
| L18 | ACTIVE | privacy, PII purpose and retention |
| L19 | ACTIVE | North Star and anti-vanity outcome graph |

## 13. Security model

### Assets

Candidate-private data, operational evidence, credentials, GitHub/Drive authority, event/recovery lineage and outbound authorization.

### Trust boundaries

External web/API → adapter; public GitHub → private operations; agent runtime → authority; ContextPack → live truth; parallel session → writer lease.

### Controls

- untrusted input schemas/allow-lists;
- secret redaction and repo guard;
- path/URL normalization; no `file://` or credential URLs;
- no shell interpolation from external payloads;
- purpose-limited PII lifecycle;
- explicit irreversible-action authorization;
- shared-write fencing;
- immutable source/evidence digests;
- dependency review triggers.

### Residual risks

Provider availability/identity drift, evidence extraction error, human approval mistakes, incomplete legacy causation and migration mismatch. All remain explicit P2/P3 nodes with owners and checkpoints.

## 14. Recovery model

Recovery order:

1. current GitHub main/contracts;
2. latest authority-eligible DB/manifest;
3. live HOTELS_MASTER/control plane;
4. verified Graph/Intelligence digests;
5. event ledger/snapshots;
6. Drive/Library recovery artifacts;
7. historical handoff prose as non-authoritative evidence.

A zero-context recovery packet must expose North Star, objective, main SHA, authority, event watermark, projection revision, active claims, open gaps, verified/unverified work and NEXT.

## 15. Test architecture

```text
unit, contract, schema, property, mutation, integration, E2E,
physical runtime, security, concurrency, replay, recovery,
performance, benchmark, empirical qualification, death drill
```

Foundation CI implements unit/contract/replay/corruption/cycle/fencing/ContextPack/assurance/compiler tests. Physical death, recovery, security and migration qualification remain CP7–CP14.

## 16. Observability

Every material V2 cycle emits session/correlation/event identity, Git ancestry, authority ceiling, event watermark, projection revision, claims/leases/fences, graph counts/types, critical path, gap counts, test evidence, artifact digests, closure and NEXT.

A projection may display a metric but cannot redefine it.

## 17. Performance/cost

Current scale fits deterministic single-node processing. V2 therefore uses the Python standard library, JSON/JSONL and SQLite-compatible contracts. Specialized graph stores, queues or distributed systems require measured triggers: sustained throughput or rebuild SLO breach, unsolved writer contention, impractical local data volume, or durable distributed provider fan-out.

## 18. Greenfield delta

- **KEEP:** constrained authority, HOTELS_MASTER, Operational Graph/Intelligence, MEP/WOP/PRG, GitHub/Drive/Library boundaries.
- **REFINE:** STATE/NEXT into ContextPack inputs; graph artifacts into versioned projections.
- **REFACTOR:** waves/runs into events; ownership into Session/Claim/Lease/Fence; QA into assurance compiler.
- **ADD:** temporal hypergraph, causal ledger, ContextPack, implementation compiler and recovery/death drills.
- **DEPRECATE:** chat continuity, implicit ownership, prose-only causation and unqualified “verified/complete/ready”.
- **DEFER:** Neo4j, Kafka, Redis, Kubernetes, microservices and embeddings until measured triggers.

## 19. Confidence

**HIGH:** authority boundaries, coordination/fencing need, deterministic digests, fail-closed migration, no-distributed-infrastructure decision.  
**MEDIUM:** JSONL longevity and five-minute recovery SLO pending empirical qualification.  
**UNKNOWN/OWNED:** full legacy causation fidelity, production contention profile and long-term event volume.

## 20. Completion law

This document can become the canonical V2 architecture when kernel, compiler, CI and foundation bundle pass. `V2_FINAL` and production authority require CP0–CP14. Architecture merge alone changes no hotel, mapping, H-ID, application or outbound state.

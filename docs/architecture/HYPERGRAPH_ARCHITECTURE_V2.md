# HYPERGRAPH ARCHITECTURE V2 — SWITZERLAND_JOB_OS

Version: **HGA-2.0**  
Status: **CANONICAL V2 ARCHITECTURE CANDIDATE**  
Authority: architecture contract; operational authority is unchanged until migration checkpoints pass  
Owner: Principal Systems Architect  
Last updated: 2026-08-30  
Source revision: Git commit ancestry + CI-bound runtime artifact  
Supersedes: fragmented future-state proposals; historical facts remain immutable

## 1. North Star

The system exists to maximize:

```text
P(verified viable Swiss offer × Roberto accepts × relocation succeeds)
```

Hotel counts, source mappings, graph density, CI runs, PRs and automation volume are supporting signals, never final success.

## 2. Reconstructed current truth

The refactor starts from the current durable project model:

- a frozen HotellerieSuisse member-directory source universe;
- constrained SQLite plus HOTELS_MASTER human/control-plane mirror;
- Operational Graph and Intelligence projections;
- MEP-2.0 chained execution and WOP-1.1 transactional waves;
- source acquisition, ECV, source-resolution, alias semantics and CRM universe contracts;
- GitHub as public-safe code/contracts/CI authority;
- Drive and Library as operational/recovery surfaces under their declared roles;
- outbound independently closed.

The current implementation is strong on domain-specific integrity but weak on universal causation, first-class sessions/claims, deterministic cross-projection context and queryable architecture lineage. V2 closes those gaps without replacing functioning domain engines.

## 3. Architecture principles

1. **Truth before convenience.** A projection, document or cache cannot outrank constrained authority.
2. **Append history; supersede semantics.** Facts and decisions are never silently rewritten.
3. **One concept, one authority.** Replicas and projections are explicit and reconciled.
4. **Events explain change; state serves reads.** Event history is causal evidence, not a substitute for constrained domain state.
5. **Hyperrelations for material decisions.** One decision may affect contracts, modules, tests, risks and migrations simultaneously.
6. **Sessions and claims are data.** Agent coordination cannot exist only in conversation.
7. **Fencing protects stale writers.** A later lease invalidates earlier mutation authority.
8. **Context is compiled, not remembered.** ContextPack is deterministic, bounded, digested and freshness-checked.
9. **Tests prove named properties only.** PASS, FAIL, SKIPPED, CANCELLED and NOT_RUN remain distinct.
10. **No infrastructure astrology.** Existing SQLite/JSONL/JSON/GitHub/Drive primitives remain until measured scale or reliability triggers justify change.
11. **No authority by inference.** Confidence, similarity and heuristic score do not grant mutation rights.
12. **Recovery is a product feature.** A zero-context operator must recover from durable authority.

## 4. System boundaries

### 4.1 Authority plane

Authoritative operational facts live in constrained state and synchronized control-plane records according to the existing authority hierarchy.

```text
PHYSICAL + CONSTRAINED AUTHORITY-ELIGIBLE STATE
> LIVE CONTROL PLANE
> VALIDATED AUTHORITY MANIFEST
> VERIFIED GRAPH / INTELLIGENCE PROJECTIONS
> GITHUB LIVE STATE POINTER
> HISTORICAL PROSE
```

The V2 ledger, graph and ContextPack carry explicit `authority_ceiling`. None can escalate itself.

### 4.2 Coordination plane

Coordination state consists of:

```text
Agent
Session
Claim
Lease
FencingToken
Heartbeat
Handoff
```

It controls who may mutate which scope and when. It is not hotel/domain truth.

### 4.3 Event plane

The event ledger stores immutable causal envelopes:

```text
event_id
project_id
agent_id
session_id
workstream_id
objective_id
correlation_id
event_type
occurred_at
main_sha / base_sha / branch
resource_scopes / semantic_scopes
authority_ceiling
causation_id
previous_event_hash
payload
event_hash
```

Events are hash-chained, schema-validated and replayable. A corrupt chain fails closed.

### 4.4 Graph plane

Two graph scopes remain explicit:

- **PROJECT_MEMORY_META_GRAPH:** goals, checkpoints, waves, sessions, agents, claims, decisions, releases, contracts, risks, tests and artifacts.
- **OPERATIONAL_GRAPH:** hotels, source records, mappings, evidence, groups, vacancies, housing, people, channels, tasks, applications and outcomes.

Both use shared IDs where they intersect. Meta graph never impersonates Operational Graph.

### 4.5 Projection plane

Read models are deterministic projections from declared sources and reducers:

```text
StateProjection
ExecutionProjection
DependencyProjection
RiskProjection
AssuranceProjection
AgentProjection
ContextPack
```

Every projection records revision, source watermark and digest.

### 4.6 Tool and provider plane

GitHub, Drive, Sheets, Library, web and external APIs are modeled as tools/providers with:

```text
capability
permission
trust_boundary
availability
fallback
cost
rate/latency
failure_mode
```

Availability changes routing, not truth.

## 5. Canonical V2 components

### C01 — Domain Authority Stores

Existing constrained SQLite, HOTELS_MASTER and synchronized operational projections remain. No replacement is introduced by V2.

### C02 — Causal Event Ledger

A local append-only JSONL representation plus deterministic verification library. In production migration it may also be mirrored into constrained tables, but the interface is frozen before storage choice.

Responsibilities:

- causal ordering;
- event watermark;
- hash-chain integrity;
- command/result linkage;
- replay input;
- audit history.

### C03 — Temporal Hypergraph Kernel

Typed nodes, directed edges and hyperedges with:

```text
id / type
attributes
valid_from / valid_to
source_event
source_commit
authority
confidence
provenance
superseded_by
```

It supports deterministic validation, canonical serialization, digesting, projection and dependency-cycle analysis.

### C04 — Session / Claim / Lease Registry

Prevents invisible agent collision.

- Sessions have unique IDs and explicit lifecycle.
- Claims bind resource and semantic scopes.
- Write claims conflict with overlapping write/read scopes according to policy.
- Leases expire and can be taken over.
- Each acquisition increments a fencing token.
- A stale token cannot authorize a write.

### C05 — ContextPack Compiler

Produces a bounded zero-context recovery packet from:

```text
main SHA
authority epoch/manifest
event watermark
projection revision
contract versions
active barriers
active claims
open work
verified evidence
next safe actions
source digests
```

The pack removes secrets and fails freshness checks when ancestry, watermark or projection revision moves.

### C06 — Assurance Kernel

Compiles gaps, invariants, tests and evidence into a machine-readable report. It rejects:

- critical node without owner;
- critical invariant without test;
- named test without evidence/result;
- P0/P1 gap without owner, mitigation or resolution path;
- orphan critical node;
- undocumented authority boundary.

### C07 — Implementation Compiler

Transforms:

```text
NorthStar → Program → Milestone → Phase → Wave → Task → Test → Evidence → Checkpoint
```

Each task requires objective, why, inputs, outputs, dependencies, affected nodes/edges/files, owner type, risk, steps, tests, adversarial/security tests, evidence, rollback and DoD.

### C08 — Projection Registry

COS dimensions are registered rather than hard-coded into separate services. A dimension can be:

```text
ACTIVE
DEFERRED_TRIGGER
NOT_APPLICABLE
```

Unused dimensions do not create infrastructure.

### C09 — Recovery Compiler

Creates public-safe manifests and private recovery bundles with exact source lineage. Recovery drills rebuild the same canonical state and material graph topology within documented tolerance.

### C10 — Existing MEP/WOP/Domain Engines

MEP chooses routes; WOP bounds waves; existing engines execute domain work. V2 adds coordination, causation, graph and assurance beneath/around them rather than duplicating them.

## 6. Canonical node ontology

### Governance and product

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

### Architecture and state

```text
Architecture, Subsystem, Component, Boundary, Contract, Schema,
Protocol, Event, Command, Outcome, State, Projection, Reducer,
Adapter, Gateway, Queue, Store, Cache, Index, Graph,
GraphProjection, ContextPack
```

### Knowledge and decisions

```text
Fact, Claim, Assumption, Hypothesis, Insight, Idea, Concept, Term,
Definition, Rule, Heuristic, Pattern, AntiPattern, Decision,
Alternative, RejectedAlternative, Tradeoff, Constraint, Requirement
```

### Reliability and assurance

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
Handoff, Checkpoint, Memory, Knowledge, ToolInvocation,
ContextWindow, EventWatermark, Authority
```

### Domain

Existing hotel/source/mapping/vacancy/housing/person/channel/application/offer entities remain domain-specific nodes.

## 7. Edge ontology

Canonical predicates include:

```text
CAUSES, CONTRIBUTES_TO, TRIGGERS, PREVENTS, ENABLES, REDUCES,
DEPENDS_ON, BLOCKS, UNBLOCKS, PRECEDES, REQUIRES,
IMPLEMENTS, CALLS, READS, WRITES, MODIFIES, GENERATES, CONSUMES,
PRODUCES, TRANSFORMS, ROUTES_TO,
DEFINES, CONSTRAINS, VALIDATES, CONFORMS_TO, BREAKS, EXTENDS,
VERSION_OF, SUPERSEDES, DEPRECATED_BY,
PROVES, SUPPORTED_BY, MEASURED_BY, TESTED_BY, FAILED_BY,
VERIFIED_BY, QUALIFIED_BY, CONTRADICTED_BY,
OWNED_BY, CLAIMED_BY, EXECUTED_BY, DELEGATED_TO, HANDOFF_TO,
RESUMES_FROM, COLLIDES_WITH, SHARES_SCOPE_WITH, WAITS_FOR,
CONTAINS, PART_OF, CONNECTED_TO, EXPOSES, ISOLATES, BRIDGES,
PROJECTS_TO, DERIVED_FROM, SOURCE_OF_TRUTH_FOR, CACHE_OF,
CHOSEN_OVER, REJECTED_BECAUSE, JUSTIFIED_BY, ASSUMES, RISKS,
MITIGATES, CONFLICTS_WITH, ALTERNATIVE_TO,
PREVIOUS_VERSION, NEXT_VERSION, VALID_FROM, VALID_UNTIL,
REFACTOR_OF, OPTIMIZES, SIMPLIFIES, GENERALIZES, SPECIALIZES,
REMOVES_DUPLICATION_OF, REDUCES_RISK_OF, IMPROVES
```

Every edge carries type, authority, confidence, source, version, criticality, temporal validity and optional cost/latency/risk.

## 8. Hyperedge semantics

A hyperedge represents one material relation involving multiple participants. Example:

```text
Decision: adopt V2 causal kernel
  CHOSEN_OVER: distributed event platform
  MODIFIES: architecture contract, session model, ContextPack
  REQUIRES: migration, CI, recovery drill
  MITIGATES: stale state, hidden authority, agent collision
  TESTED_BY: ledger, fencing, replay and death-drill suites
```

Hyperedges are not stored as opaque prose; participants and roles are queryable.

## 9. State machines

### Session

```text
OPEN → ACTIVE → HANDOFF_PENDING → CLOSED
  └────────────→ ABORTED
```

### Claim

```text
PROPOSED → ACTIVE → RELEASED
             ├────→ EXPIRED
             └────→ REVOKED
```

### Lease

```text
ACQUIRED → RENEWED* → RELEASED
     └──────────────→ EXPIRED → TAKEOVER(new fencing token)
```

### Event

```text
PROPOSED → APPENDED → VERIFIED
                 └──→ CORRUPT/BLOCKED
```

### Projection

```text
BUILDING → CURRENT → STALE → REBUILDING → CURRENT
                   └──────→ BLOCKED
```

### Task

Existing READY/ACTIVE/BLOCKED/COMPLETE/FAILED/CANCELLED semantics remain. Completion requires evidence, not a status string.

### Evidence

```text
DISCOVERED → SCOPED → VERIFIED → EXPIRED
       └────→ CONTRADICTED → RESOLUTION_REQUIRED
```

## 10. Data flow

```text
External source (UNTRUSTED)
→ adapter
→ schema/scope validation
→ evidence record
→ command/wave
→ constrained mutation or staging
→ event append
→ projection reducers
→ graph/state/context outputs
→ invariants
→ authority eligibility
→ recovery persistence
```

Provenance cannot be dropped at a transform boundary. Every derived artifact records source digests and reducer version.

## 11. Single-source-of-truth matrix

| Concept | Authority | Replicas / projections | Drift detection |
|---|---|---|---|
| Canonical hotels | constrained DB + synchronized control plane | Operational Graph, Intelligence, STATE summary | PK/digest reconciliation |
| Frozen source records | frozen source manifest/artifact | staging, graph projection | source-record conservation |
| Source mappings | constrained mapping state after promotion | Graph/Sheets/report | exact source-key set + digest |
| Goals/checkpoints | live control plane under authority rules | GitHub STATE/meta graph | revision/event reconciliation |
| Code/contracts | GitHub main | local clone/CI artifact | commit SHA |
| Events | append-only ledger | event projections | hash-chain verification |
| Active claims/leases | coordination registry | ContextPack/meta graph | fencing token + expiry |
| ContextPack | none; compiled cache | Library/Drive/GitHub artifact | parent SHA/watermark/revision checks |
| Recovery bundles | exact artifact manifest | Library/Drive | SHA + logical restore |

Any new competing authority is a P0 architecture defect.

## 12. COS 20D projection map

| Dimension | V2 status | Primary projection |
|---|---|---|
| L0 Visual | ACTIVE | architecture clusters, hubs, orphans |
| L1 Execution | ACTIVE | goal→checkpoint→task→test→evidence |
| L2 State Machine | ACTIVE | lifecycle transition graph |
| L3 Dependency | ACTIVE | DAG, critical path, blast radius, cycles |
| L4 Call Graph | ACTIVE | package/function ownership and coupling |
| L5 Control Flow | ACTIVE | fail-closed paths and authority escalation |
| L6 Data Flow | ACTIVE | source→evidence→state→consumer provenance |
| L7 Compute | ACTIVE_LIGHT | batch/replay cost; no distributed compute |
| L8 Knowledge | ACTIVE | concepts/facts/decisions/evidence |
| L9 Semantic | ACTIVE | canonical lexicon and deprecated terms |
| L10 Similarity | DEFERRED_TRIGGER | candidate consolidation; never authority |
| L11 GraphRAG | ACTIVE_CONTRACT | zero-context retrieval tests |
| L12 Memory | ACTIVE | ephemeral/working/project/decision/history TTL |
| L13 Agent | ACTIVE | sessions/claims/leases/handoffs |
| L14 Tool | ACTIVE | connectors/providers/trust/fallbacks |
| L15 Workflow | ACTIVE | MEP/WOP/domain/recovery flows |
| L16 Network | NOT_APPLICABLE | no internal distributed network today |
| L17 Financial | ACTIVE_DOMAIN | offer economics when real offers exist |
| L18 Privacy | ACTIVE | PII purpose/retention/public boundary |
| L19 Product Outcome | ACTIVE | North Star and anti-vanity metrics |

## 13. Security model

### Assets

- candidate private facts/assets;
- operational hotel/source/evidence data;
- provider credentials;
- GitHub/Drive authority;
- event and recovery lineage;
- outbound authorization.

### Trust boundaries

- external web/API → adapter;
- public GitHub → private operational state;
- agent runtime → authority stores;
- ContextPack/cache → live authority;
- scheduled/parallel session → active writer lease.

### Mandatory controls

- all external input treated as untrusted;
- strict schemas and allow-lists;
- secret redaction and public-repo guard;
- path normalization; no arbitrary filesystem traversal;
- no shell interpolation from provider/user payloads;
- HTTP(S)-only URL policies where applicable;
- no `file://`, credential embedding or SSRF-capable fetch path;
- purpose-limited PII persistence and lifecycle;
- explicit outbound authorization;
- fencing on shared writes;
- immutable evidence/source digests;
- dependency pin/review triggers.

### Residual risks

- connector behavior and provider availability;
- semantic errors in evidence extraction;
- human approval mistakes;
- legacy records lacking complete event history;
- eventual migration mismatch.

Each residual risk has an owner, detection and recovery task in the implementation program.

## 14. Recovery model

Recovery sources, in order:

1. current GitHub main and contracts;
2. latest authority-eligible constrained DB/manifest;
3. live HOTELS_MASTER/control plane;
4. verified Operational Graph/Intelligence digests;
5. append-only event ledger and snapshots;
6. Drive/Library recovery artifacts;
7. historical handoffs as non-authoritative evidence.

Zero-context recovery must reproduce:

```text
North Star
current objective/checkpoint
main SHA
authority parent/epoch
event watermark
projection revision
active claims/leases
open P0/P1 gaps
verified/unverified work
next safe action
```

within five minutes for a trained operator/agent.

## 15. Test architecture

Required taxonomy:

```text
unit
contract
schema
property
mutation
integration
E2E
physical-runtime
security
concurrency
replay
recovery
performance
benchmark
empirical qualification
death drill
```

V2 foundation implements unit, contract, property-like invariants, concurrency/fencing, replay, recovery/ContextPack and death-drill fixtures. Mutation, physical runtime and empirical qualification remain migration checkpoints with explicit triggers.

Every escaped bug becomes:

```text
Bug → RootCause → BrokenInvariant → MissedBy → RegressionTest
    → AdjacentFailureFamily → Property/Fuzz/Gauntlet
```

## 16. Observability

Every material V2 cycle emits:

```text
session_id / correlation_id / event_id
main_sha / base_sha / branch
authority epoch / ceiling
event watermark / projection revision
claims / leases / fencing tokens
nodes / edges / hyperedges by type
critical path / blocked frontier
P0/P1/P2/P3 gaps
invariant and test results
artifact digests
closure state / NEXT
```

A metric has one canonical live definition. A projection may display it but cannot redefine it.

## 17. Performance and cost

Current scale fits local deterministic processing:

- thousands, not billions, of domain records;
- dozens/hundreds of events per wave;
- single-writer authority transactions;
- bounded CI and recovery artifacts.

Therefore V2 uses Python standard library, JSON/JSONL and SQLite-compatible contracts. Reconsider distributed infrastructure only after measured triggers such as:

- sustained event throughput exceeding single-node SLO;
- projection rebuild breaching recovery SLO;
- multi-writer contention not solved by lease/fencing;
- dataset exceeding practical local memory/storage;
- provider fan-out requiring durable distributed queue semantics.

## 18. Greenfield comparison

### Keep

- constrained DB and PK-first authority;
- HOTELS_MASTER human control plane;
- Operational Graph and Intelligence separation;
- MEP/WOP/PRG and domain-specific contracts;
- GitHub/Drive/Library role boundaries;
- fail-closed outbound.

### Refine

- STATE/NEXT into ContextPack inputs;
- wave/run records into causal events;
- task/decision/evidence relationships into shared graph IDs;
- CI into architecture/assurance compiler verification.

### Add

- temporal hypergraph kernel;
- append-only event ledger;
- session/claim/lease/fencing;
- deterministic ContextPack;
- assurance and implementation compiler;
- zero-context recovery/death drill.

### Deprecate

- chat memory as continuity;
- implicit agent ownership;
- prose-only causation;
- unversioned graph snapshots;
- “verified/complete/ready” without scoped definitions.

### Delete later

- duplicate historical state summaries after lineage banners and redirects exist;
- stale unmerged PRs once supersession evidence is recorded;
- redundant recovery pointers after canonical pointer adoption.

## 19. Architecture confidence

### High confidence

- authority boundaries;
- need for sessions/claims/fencing;
- deterministic event/graph/context digests;
- no-distributed-infrastructure decision;
- fail-closed migration.

### Medium confidence

- JSONL as first event-ledger representation;
- exact projection granularity;
- five-minute recovery SLO until drill data exists.

### Unknown / owned

- full historical event reconstruction fidelity;
- production contention profile;
- long-term event volume;
- provider-side stable identifiers beyond frozen source contracts.

Unknowns are migration tasks, not hidden assumptions.

## 20. V2 completion rule

This architecture document can be frozen when the executable kernel, seed graph, compiler, tests and CI pass. `V2_FINAL` and production authority require the full checkpoint sequence in the implementation program. Architecture merge alone changes no hotel/source mapping, authority count, H-ID, application or outbound state.

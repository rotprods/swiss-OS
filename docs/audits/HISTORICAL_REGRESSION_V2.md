# HISTORICAL REGRESSION V2 — SWITZERLAND_JOB_OS

Version: **HRG-2.0**  
Status: **FOUNDATION RECONSTRUCTION COMPLETE; LEGACY EVENT BACKFILL PENDING**  
Owner: Migration Architect / Failure Analyst  
Last updated: 2026-08-30

This document preserves causal lessons. It does not rewrite historical artifacts or claim complete event-level fidelity for activity that predates the V2 ledger.

## Architecture evolution

```text
Initial job-search spreadsheets
→ hotel-universe CRM/control plane
→ constrained SQLite shadow
→ DB↔Sheets reconciliation and invariants
→ Graph + Intelligence projections
→ QA V3 / scoring / TTL / scheduler
→ MEP chained execution + WOP transactional waves
→ frozen source-record universe and exact-current validation
→ alias semantic repair and cross-plane authority discipline
→ V2 causal hypergraph / sessions / fencing / ContextPack
```

## Major pivots

### PIVOT-01 — Ad hoc job list → hotel-universe operating system

**Why:** isolated vacancies could not systematically map the Swiss hospitality market or support repeatable targeting.  
**Property gained:** persistent entity universe, evidence and scheduler.  
**Debt introduced:** hotel count risked becoming a vanity metric.  
**V2 protection:** L19 Product Outcome keeps the real offer/relocation North Star above market-volume projections.

### PIVOT-02 — Sheets-only operations → constrained SQLite + human mirror

**Why:** spill corruption, shifted schemas, duplicate QA states, stale tasks and count drift could not be structurally prevented in Sheets.  
**Property gained:** PK/FK/UNIQUE/CHECK/idempotency, restore/replay and DB↔Sheets reconciliation.  
**Residual risk:** structural validity can still miss semantic identity corruption.  
**V2 protection:** semantic invariants/evidence remain independent from graph/DB integrity.

### PIVOT-03 — ID frontier/count parity → physical rows, canonical entities and aliases

**Why:** frontier IDs and physical rows were incorrectly used as canonical counts.  
**Property gained:** explicit physical/canonical/superseded semantics.  
**Escaped failure:** four alias edges later proved semantically inconsistent despite valid FK structure.  
**V2 protection:** ASR remains mandatory; relationships carry source/authority and graph assurance cannot substitute identity proof.

### PIVOT-04 — Historical page crawling → frozen source-record identity

**Why:** member-directory page numbers and totals moved across locale/cache epochs.  
**Property gained:** snapshot-scoped provider/source-record identity and conservation.  
**Residual risk:** provider IDs can still change.  
**V2 protection:** provider drift is a P2 risk with source-diff evidence and empirical qualification.

### PIVOT-05 — Preferred-path execution → MEP no-idle fallback

**Why:** unavailable Drive/API/provider capability repeatedly stopped otherwise safe work.  
**Property gained:** deterministic safe fallback routes and durable NEXT.  
**Residual risk:** repeated administrative action or endless fallback loops.  
**V2 protection:** Session/Claim scope, mutation idempotency and strategy-attempt budget.

### PIVOT-06 — Conversational continuity → durable STATE/NEXT/Drive/Library/GitHub

**Why:** chat compaction and agent death could lose current state and rationale.  
**Property gained:** persistent handoffs and recovery bundles.  
**Residual risk:** stale summaries and multiple mutable pointers.  
**V2 protection:** ContextPack with exact SHA, event watermark, projection revision and source digests.

### PIVOT-07 — Serial manual exact-current checks → bounded ECV workflows

**Why:** thousands of source candidates made manual verification the bottleneck.  
**Property gained:** immutable subbatches, CI artifacts, validation and durable frontier.  
**Residual risk:** verification completion can be confused with terminal source mapping.  
**V2 protection:** lexicon/graph distinguish `CURRENT_DETAIL_VERIFIED` from `TERMINAL_MAPPING` and CRM completion.

## Escaped-bug graph

### BUG-HIST-001 — Sheets formula/schema corruption

```text
BUG → spill/shift/duplicate state
ROOT_CAUSE → mutable positional spreadsheet operations
BROKEN_INVARIANT → writes must resolve canonical PK/schema
MISSED_BY → visual/manual validation
REGRESSION → DB constraints + PK reconciliation
ADJACENT_FAMILY → stale scheduler, duplicate QA, metric drift
V2_GENERALIZATION → authority/store boundary + provenance/data-flow projection
```

### BUG-HIST-002 — Missing/incorrect canonical identity count

```text
BUG → frontier/physical count presented as canonical
ROOT_CAUSE → overloaded count semantics
BROKEN_INVARIANT → physical lineage != active canonical
REGRESSION → explicit count classes and exact PK sets
ADJACENT_FAMILY → alias inflation, canary promotion, denominator drift
V2_GENERALIZATION → LEX-2.0 + authority ceiling + assurance gate
```

### BUG-HIST-003 — Semantically wrong alias edges

```text
BUG → valid H-ID edges joined unrelated hotels
ROOT_CAUSE → row/ID drift + FK-only confidence
BROKEN_INVARIANT → alias/target must represent same real entity
MISSED_BY → SQLite integrity and name-independent FK checks
REGRESSION → ASR-1.0 semantic proof
ADJACENT_FAMILY → valid-but-wrong source mapping/graph edge
V2_GENERALIZATION → evidence-bearing edges + independent semantic test nodes
```

### BUG-HIST-004 — Historical index treated as current membership

```text
BUG → cached page could inflate current universe
ROOT_CAUSE → discovery and authority scopes conflated
BROKEN_INVARIANT → historical index is discovery-only until reconciled
REGRESSION → source-scope states and frozen snapshots
ADJACENT_FAMILY → stale vacancy/housing/person/channel claims
V2_GENERALIZATION → temporal validity + source authority/confidence attributes
```

### BUG-HIST-005 — Page number treated as stable record identity

```text
BUG → same page number yielded different properties across epochs/locales
ROOT_CAUSE → pagination position used as identity
BROKEN_INVARIANT → identity requires stable source key or exact scoped evidence
REGRESSION → MDM/SSR/frozen source records
ADJACENT_FAMILY → array offset, Sheets row, API cursor as entity ID
V2_GENERALIZATION → provider/source-record nodes and observation edges
```

### BUG-HIST-006 — Phantom or undiscoverable operational parent

```text
BUG → control plane referenced DB version not physically available
ROOT_CAUSE → manifest/prose advanced ahead of verified artifact persistence
BROKEN_INVARIANT → authority parent must be physically recoverable and hash-bound
REGRESSION → manifest, remote redownload and restore/replay validation
ADJACENT_FAMILY → missing CI artifact, stale Drive pointer, local-only backup
V2_GENERALIZATION → Artifact/Evidence/Recovery graph and ContextPack source digests
```

### BUG-HIST-007 — CI PASS overclaimed runtime synchronization

```text
BUG → repository tests could be read as proof of Drive/DB/Graph convergence
ROOT_CAUSE → test scope not explicit
BROKEN_INVARIANT → tests prove only their declared boundary
REGRESSION → WOP authority chain and precise vocabulary
ADJACENT_FAMILY → fixture called E2E, canary called production
V2_GENERALIZATION → TestEvidence nodes with state/evidence/scope
```

### BUG-HIST-008 — Repeated issue-create loop

```text
BUG → multiple administrative issues created for one semantic root
ROOT_CAUSE → mutation tool selected repeatedly without idempotency lookup/budget
BROKEN_INVARIANT → one idempotency identity may create at most one durable object
MISSED_BY → prose-only “do not repeat” guidance
REGRESSION → MutationLoopGuard
ADJACENT_FAMILY → duplicate PR/file/event/message/application
V2_GENERALIZATION → mutation attempts as replayable events + STUCK_LOOP transition
```

## Rejected approaches and preserved reasons

| Approach | Status | Reason |
|---|---|---|
| Sheets as only operational truth | REJECTED | cannot enforce relational constraints/idempotency safely |
| Direct bulk append then declare success | REJECTED | bypasses dedupe/canary/reconciliation |
| Historical directory pages as current authority | REJECTED | cache/epoch drift |
| One “100%” completeness metric | REJECTED | conflates resolution, known value, evidence and freshness |
| Hiring probability from heuristic score | REJECTED | no calibrated outcome data |
| Graph registry as full operational graph | REJECTED | meta/operational scope collision |
| Public repo with SQLite/PII/raw contacts | REJECTED | privacy/security boundary |
| Neo4j/Kafka/Kubernetes now | DEFERRED | no measured bottleneck justifies operating cost |
| Big-bang V2 rewrite | REJECTED | regression and authority-migration risk |

## Historical debt nodes

| ID | Debt | Severity | Owner | Resolution |
|---|---|---:|---|---|
| HIST-DEBT-001 | pre-V2 actions lack complete causal event history | P2 | Migration Architect | evidence-bounded backfill; unknowns explicit |
| HIST-DEBT-002 | some old docs contain stale operational state | P2 | Documentation Architect | authority banners/redirects and eventual deletion |
| HIST-DEBT-003 | unmerged historical PRs may confuse current topology | P3 | Git/CI Engine | classify merged/superseded/closed |
| HIST-DEBT-004 | recovery SLO not measured across independent agents | P2 | Recovery Engineer | CP7/CP8/CP12 drills |
| HIST-DEBT-005 | provider-ID stability not empirically characterized | P2 | Data Architect | longitudinal diff corpus |

## Root-cause conclusion

Historical failures cluster into five families:

1. **authority ambiguity**;
2. **identity semantics hidden behind structurally valid IDs**;
3. **staging/projection mistaken for promotion**;
4. **continuity and ownership existing only in conversation/prose**;
5. **mutation/retry loops without idempotency and fencing**.

V2 directly implements a permanent invariant/test family for each. Remaining historical uncertainty is explicit, owned and migration-gated rather than silently completed.

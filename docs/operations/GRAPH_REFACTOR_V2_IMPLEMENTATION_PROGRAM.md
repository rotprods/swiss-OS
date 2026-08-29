# GRAPH REFACTOR V2 — IMPLEMENTATION PROGRAM

Version: **GRV2-IP-1.0**  
Status: **EXECUTABLE PROGRAM**  
Owner: Mission Commander + Technical Product Manager  
Authority: planning/execution contract; operational authority remains separately gated  
Last updated: 2026-08-30

## 1. Program objective

Introduce the V2 temporal hypergraph, causal event, session/claim/fencing, ContextPack and assurance architecture without interrupting CRM production or creating a second source of operational truth.

## 2. Definition of Done — program

The program is complete only when:

```text
V2 architecture frozen
+ kernel implemented
+ tests executed/passed
+ critical security and concurrency invariants passed
+ current operational state shadow-migrated
+ deterministic projection parity proved
+ zero-context recovery qualified
+ agent-death/fencing takeover qualified
+ documentation and lexicon adopted
+ event/graph/state/ContextPack artifacts durable
+ no unresolved P0/P1 regression
+ authority migration accepted through a named checkpoint
```

A merged architecture PR is not production migration.

## 3. Phases

| Phase | Objective | Primary output | Stop gate |
|---|---|---|---|
| P0 Reconstruction | Bind live Git, authority, events, active claims and blockers | BootstrapState V2 | CP0 |
| P1 Ontology | Canonical node/edge/hyperedge semantics | HGA-2.0 | CP1 |
| P2 History | Reconstruct pivots, bugs and debt | Historical Graph | CP2 |
| P3 Gap analysis | Rank defects and residual uncertainty | Gap Matrix | CP3 |
| P4 Architecture | Freeze one greenfield-informed V2 | Architecture V2 | CP4 |
| P5 Contracts | Freeze authority, state, event, identity and lexicon contracts | Contract Kernel | CP5 |
| P6 Kernel | Implement graph, ledger, coordination, ContextPack and compiler | Python kernel | CP6 |
| P7 Recovery | Recover without chat/local checkout/cache | Recovery evidence | CP7 |
| P8 Agent death | Abort session and transfer leases/claims safely | Death-drill evidence | CP8 |
| P9 Concurrency | Prove collision, expiry and fencing semantics | Concurrency evidence | CP9 |
| P10 Security | Attack trust boundaries, secrets and authority escalation | Security report | CP10 |
| P11 E2E shadow | Execute domain command → event → projections → assurance | E2E artifact | CP11 |
| P12 Qualification | Measure replay/rebuild/recovery SLOs | Qualification report | CP12 |
| P13 Migration | Shadow-compare and migrate current truth with lineage | Migration manifest | CP13 |
| P14 Authority | Promote V2 coordination/projection contract | Release/transition | CP14 |

## 4. Checkpoints

### CP0 — Live Truth Reconstructed

Entry: repository and authority surfaces readable.  
Requires: unique session identity, exact Git parent, event watermark or explicit legacy absence, active claims, open PRs/P0s and capability map.  
Tests: ancestry, authority-ceiling and ContextPack freshness checks.  
Exit: another agent can identify the current objective and next safe action.  
Rollback: discard bootstrap candidate; authority unchanged.

### CP1 — Graph Complete

Requires: materially relevant entities represented, critical edges/hyperedges explicit, no unexplained critical orphan, shared IDs and ontology validation.  
Exit: L0/L1/L3/L8/L13/L15 projections answer architecture, execution, dependency, knowledge and agent questions.

### CP2 — Historical Regression Complete

Requires: major pivots, escaped bugs, rejected approaches and unresolved historical debt.  
Exit: every escaped P0/P1 bug maps to broken invariant and regression test.

### CP3 — Architecture Gaps Classified

Requires: severity, probability, blast radius, detection, mitigation, owner, test, evidence and phase.  
Exit: no hidden P0/P1; priorities are reproducible.

### CP4 — V2 Architecture Frozen

Requires: current vs greenfield classification `KEEP | REFINE | REFACTOR | MIGRATE | DEPRECATE | DELETE | DEFER`.  
Exit: one canonical V2 and no competing current architecture document.

### CP5 — Core Contracts Frozen

Requires: authority, events, state, graph, identity, agent/session, memory, tool, security and recovery semantics.  
Exit: overloaded words are eliminated through LEX-2.0.

### CP6 — Implementation Kernel Verified

Requires: graph, ledger, coordination, ContextPack, assurance, implementation compiler and COS registry code.  
Tests: unit, contract, replay, corruption, cycle, secret, claim collision, lease expiry, stale fence, stale ContextPack, gap and compiler tests.  
Exit: CI-bound build manifest reports `release_candidate=true`, authority unchanged and outbound closed.

### CP7 — Recovery Verified

Requires: delete chat/local cache/projections; rebuild from GitHub + authority + event/recovery artifacts.  
Exit: canonical state/topology/blockers/NEXT reproduced within tolerance and target time.

### CP8 — Agent Death Drill Passed

Requires: active session dies mid-wave.  
Exit: claims/leases expire or release, successor obtains newer fencing token, stale writer rejected, handoff queryable.

### CP9 — Concurrency Verified

Requires: overlapping and non-overlapping multi-agent campaigns, duplicate/late/out-of-order events and stale main.  
Exit: no conflicting mutation accepted; safe parallelism preserved.

### CP10 — Security Gauntlet Passed

Requires: prompt/provider poisoning, secret/PII leakage, path/URL/shell injection, authority escalation, replay and duplicate external action campaigns.  
Exit: P0/P1 security gaps zero; residual risks owned.

### CP11 — E2E Product Path Passed

Requires: one real read-only CRM work item traverses MEP/WOP → session/claim → evidence → event → graph/state → assurance → NEXT.  
Exit: outputs improve the North Star path and do not merely exercise infrastructure.

### CP12 — Empirical Qualification Passed

Requires: measured projection/replay/recovery duration, failure/retry rate and operator onboarding.  
Exit: declared SLOs supported by evidence rather than aspiration.

### CP13 — Migration Complete

Requires: legacy graph/state/events mapped or explicitly `HISTORICAL_UNKNOWN`; V1/V2 parity; no lost authority or history; older architecture marked `SUPERSEDED`.  
Exit: operational runs use V2 session/event/ContextPack contracts.

### CP14 — Production Authority

Requires: all preceding gates; authority transition emitted/persisted; rollback verified.  
Exit: V2 is the production coordination and projection architecture. It still cannot open outbound without its independent domain gates.

## 5. Executable tasks

Machine-complete task records are generated by `scripts/compile_graph_v2.py` into `implementation_program.json`. The task IDs are:

```text
V2-T00 live truth reconstruction
V2-T01 ontology and graph model
V2-T02 historical regression
V2-T03 gap/risk classification
V2-T04 architecture freeze
V2-T05 contracts and lexicon
V2-T06 temporal hypergraph kernel
V2-T07 event ledger/replay
V2-T08 session/claim/lease/fencing
V2-T09 COS 20D projections
V2-T10 ContextPack/memory
V2-T11 assurance and escaped-bug corpus
V2-T12 zero-context recovery drill
V2-T13 agent-death/takeover drill
V2-T14 security/provider-poisoning gauntlet
V2-T15 E2E shadow product path
V2-T16 operational/historical migration
V2-T17 production/empirical qualification
```

Each generated task includes objective, why, inputs, outputs, dependencies, affected nodes/edges/files, owner type, risk, implementation steps, tests, adversarial tests, security tests, evidence, rollback and full DoD.

## 6. Current executable frontier

### Implemented in this foundation PR

```text
V2-T00 foundation reconstruction contract
V2-T01 ontology
V2-T03 gap compiler
V2-T04 canonical architecture
V2-T05 contracts/lexicon
V2-T06 graph kernel
V2-T07 event ledger
V2-T08 coordination/fencing
V2-T09 COS registry/projections
V2-T10 ContextPack
V2-T11 assurance/compiler regression suite
```

These are architecture-foundation states, not operational migration claims.

### Next safe frontier

```text
V2-T02 historical regression corpus completion
V2-T12 physical zero-context recovery drill
V2-T13 physical agent-death/fencing takeover drill
V2-T14 security campaign
V2-T15 one read-only CRM shadow path
```

Operational production continues independently under existing contracts. V2-T16 cannot begin until shadow artifacts prove no conflict with current CRM work and active claims.

## 7. Parallelization plan

Safe parallel lanes use non-overlapping claims:

| Lane | Scope | Can run with |
|---|---|---|
| A Architecture/history | `docs/architecture`, `docs/decisions`, historical graph | B, C, D |
| B Kernel/tests | `src/swiss_os/v2_*`, V2 tests | A, C |
| C Recovery/security | recovery bundle, threat model, death drills | A, B |
| D CRM production | existing domain batches under separate operational claims | A and read-only B/C |

Must serialize:

- edits to the same stable contract;
- authority transitions;
- HOTELS_MASTER/constrained DB writes;
- graph migration cutover;
- STATE/NEXT pointer replacement;
- release promotion.

## 8. Migration strategy

```text
FOUNDATION
→ SHADOW COMPILE
→ PARITY REPORT
→ RECOVERY/DEATH/CONCURRENCY/SECURITY DRILLS
→ NEW-WAVE V2 COORDINATION
→ HISTORICAL BACKFILL
→ PROJECTION CUTOVER
→ AUTHORITY TRANSITION
```

No V1 records are deleted during migration. Their validity intervals and supersession relations are preserved.

## 9. Rollback

- Kernel/contract rollback: revert Git commit; generated artifacts remain evidence.
- Projection rollback: restore prior projection revision; ledger remains append-only.
- Coordination rollback: disable V2 claim gate only after all active V2 leases close; never accept stale tokens.
- Migration rollback: restore pre-migration authority manifest and control-plane snapshot; mark failed migration events; retain source artifacts.
- Outbound: remains closed throughout this program unless independently authorized after all domain gates.

## 10. Stop conditions

Valid closure states:

```text
SUCCESS_FOUNDATION
BLOCKED_EXTERNAL
AUTHORITY_BLOCK
DIMINISHING_RETURN
RUNTIME_BUDGET_EXHAUSTED_WITH_NEXT
```

A completed plan or merged PR is not sufficient. Each closure emits durable state, event/graph evidence and exact NEXT.

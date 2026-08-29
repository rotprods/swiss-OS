# GRAPH REFACTOR V2 — IMPLEMENTATION PROGRAM

Version: **GRV2-IP-1.0**  
Status: **EXECUTABLE PROGRAM**  
Owner: Mission Commander + Technical Product Manager  
Authority: planning/execution contract; operational authority remains separately gated  
Last updated: 2026-08-30

## Program objective

Introduce the temporal hypergraph, causal events, Session/Claim/Lease/FencingToken, ContextPack and assurance architecture without interrupting CRM production or creating a second source of operational truth.

## Program Definition of Done

```text
V2 architecture frozen
+ kernel implemented
+ tests executed and passed
+ security/concurrency invariants passed
+ current operational state shadow-migrated
+ deterministic projection parity proved
+ zero-context recovery qualified
+ agent-death/fencing takeover qualified
+ documentation and lexicon adopted
+ event/graph/state/ContextPack artifacts durable
+ no unresolved P0/P1 regression
+ authority migration accepted through named checkpoint
```

A merged architecture PR is not production migration.

## Phases

| Phase | Objective | Output | Checkpoint |
|---|---|---|---|
| P0 Reconstruction | Bind live Git, authority, events, claims and blockers | BootstrapState V2 | CP0 |
| P1 Ontology | Canonical node/edge/hyperedge semantics | HGA-2.0 | CP1 |
| P2 History | Pivots, escaped bugs and debt | Historical Graph | CP2 |
| P3 Gap analysis | Rank defects/residual uncertainty | Gap Matrix | CP3 |
| P4 Architecture | Freeze one greenfield-informed V2 | Architecture V2 | CP4 |
| P5 Contracts | Freeze authority/state/event/identity/lexicon | Contract Kernel | CP5 |
| P6 Kernel | Implement graph, ledger, coordination, ContextPack, assurance | Python kernel | CP6 |
| P7 Recovery | Recover without chat/checkout/cache | Recovery evidence | CP7 |
| P8 Agent death | Abort session and transfer safely | Death-drill evidence | CP8 |
| P9 Concurrency | Prove claim/fencing/event semantics | Concurrency evidence | CP9 |
| P10 Security | Attack trust boundaries and escalation | Security report | CP10 |
| P11 E2E shadow | Domain item through MEP/WOP/event/projections | E2E artifact | CP11 |
| P12 Qualification | Measure replay/rebuild/recovery SLOs | Qualification report | CP12 |
| P13 Migration | Shadow-compare and migrate current truth | Migration manifest | CP13 |
| P14 Authority | Promote V2 coordination/projections | Release transition | CP14 |

## Checkpoints

### CP0 — Live Truth Reconstructed

Entry: repository and authority surfaces readable.  
Requires: unique session, exact Git parent, event watermark or explicit legacy absence, active claims, open PRs/P0s and capability map.  
Exit: another agent can identify objective and next safe action.  
Rollback: discard bootstrap candidate; authority unchanged.

### CP1 — Graph Complete

Requires materially relevant entities, critical edges/hyperedges, shared IDs, ontology validation and no unexplained critical orphan. Exit when L0/L1/L3/L8/L13/L15 answer architecture, execution, dependency, knowledge, agent and workflow questions.

### CP2 — Historical Regression Complete

Requires major pivots, escaped bugs, rejected approaches and unresolved historical debt. Every escaped P0/P1 bug maps to root cause, broken invariant, missed-test cause, regression test and adjacent failure family.

### CP3 — Architecture Gaps Classified

Every gap has severity, probability, blast radius, detection, mitigation, owner, test, evidence and phase. No hidden P0/P1 remains.

### CP4 — V2 Architecture Frozen

Current-vs-greenfield differences are classified `KEEP | REFINE | REFACTOR | MIGRATE | DEPRECATE | DELETE | DEFER`; one canonical V2 exists.

### CP5 — Core Contracts Frozen

Authority, events, state, graph, identity, session/agent, memory, tools, security, recovery and lexicon are explicit.

### CP6 — Implementation Kernel Verified

Requires graph, ledger, coordination, ContextPack, assurance, implementation compiler and COS registry. CI must bind tests to the exact SHA and output a release-candidate foundation manifest with no authority/H-ID/outbound mutation.

### CP7 — Recovery Verified

Delete chat/local cache/projections and rebuild from GitHub + authority + ledger/recovery artifacts. Reproduce canonical state/topology/blockers/NEXT within declared tolerance and target time.

### CP8 — Agent Death Drill Passed

An active session dies mid-wave; claims/leases expire or release, successor gets a newer fence, stale writer is rejected and handoff remains queryable.

### CP9 — Concurrency Verified

Run overlapping/non-overlapping agents, duplicate/late/out-of-order events and moved-main campaigns. No conflicting mutation is accepted; safe parallelism remains available.

### CP10 — Security Gauntlet Passed

Attack prompt/provider poisoning, secrets/PII, path/URL/shell injection, authority escalation, replay and duplicate irreversible action. Open P0/P1 security gaps must be zero.

### CP11 — E2E Product Path Passed

One real read-only CRM item traverses MEP/WOP → Session/Claim → evidence → event → graph/state → assurance → NEXT and demonstrably advances the North-Star path.

### CP12 — Empirical Qualification Passed

Measure projection/replay/recovery duration, failure/retry rate and onboarding. SLOs must be evidenced rather than aspirational.

### CP13 — Migration Complete

Legacy graph/state/events are mapped or explicitly `HISTORICAL_UNKNOWN`; V1/V2 parity holds; no authority/history is lost; old architecture is marked `SUPERSEDED`.

### CP14 — Production Authority

All prior gates pass; an authority transition and rollback evidence are persisted. V2 becomes production coordination/projection architecture but still cannot open outbound without independent domain gates.

## Machine-compiled tasks

`scripts/compile_graph_v2.py` emits complete task records for:

```text
V2-T00 live truth reconstruction
V2-T01 ontology/hypergraph
V2-T02 historical regression
V2-T03 gap/risk classification
V2-T04 architecture freeze
V2-T05 contracts/lexicon
V2-T06 temporal graph kernel
V2-T07 event ledger/replay
V2-T08 Session/Claim/Lease/Fencing
V2-T09 COS 20D projections
V2-T10 ContextPack/memory
V2-T11 assurance/escaped-bug corpus
V2-T12 zero-context recovery drill
V2-T13 agent-death/takeover drill
V2-T14 security/provider-poisoning gauntlet
V2-T15 E2E shadow product path
V2-T16 operational/historical migration
V2-T17 empirical SLO qualification
```

Each contains objective, why, inputs/outputs, dependencies, affected nodes/edges/files, owner, risk, steps, tests, adversarial/security tests, evidence, rollback and full task DoD.

## Foundation scope

Implemented candidates in this PR:

```text
V2-T00, T01, T03, T04, T05, T06, T07, T08, T09, T10, T11
```

`V2-T02` and CP7–CP14 remain explicit work; foundation code must not claim their completion.

## Next executable frontier

```text
V2-T02 historical regression corpus
V2-T12 physical zero-context recovery drill
V2-T13 physical agent-death/fencing takeover drill
V2-T14 security campaign
V2-T15 read-only CRM shadow path
```

`V2-T16` migration cannot begin until shadow artifacts prove no conflict with active CRM production claims.

## Parallelization

| Lane | Claim scope | Safe concurrency |
|---|---|---|
| A Architecture/history | architecture/decisions/historical graph | B, C, D |
| B Kernel/tests | `src/swiss_os/v2_*`, V2 tests | A, C |
| C Recovery/security | recovery bundle, threat/death drills | A, B |
| D CRM production | current domain batches | A and read-only B/C |

Serialize same-contract edits, authority transitions, DB/HOTELS_MASTER writes, graph cutover, STATE/NEXT replacement and release promotion.

## Migration strategy

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

No V1 record is deleted. Validity intervals and supersession relations preserve historical truth.

## Rollback

- Kernel/contracts: revert Git commit; retain generated evidence.
- Projections: restore prior revision; ledger remains append-only.
- Coordination: close all V2 leases before disabling its gate; never accept stale tokens.
- Migration: restore pre-migration authority/control-plane snapshot, emit failure event, retain source artifacts.
- Outbound remains closed throughout unless independently authorized after domain gates.

## Valid stop states

```text
SUCCESS_FOUNDATION
BLOCKED_EXTERNAL
AUTHORITY_BLOCK
DIMINISHING_RETURN
RUNTIME_BUDGET_EXHAUSTED_WITH_NEXT
```

A completed plan is not a stop condition. Every closure persists state, graph/event evidence and exact NEXT.

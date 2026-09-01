# /GRAPH-REFACTOR-V2 — LIVE RECONSOLIDATION 2026-09-01

Status: `CP0_RECONSTRUCTED / CP1_DELTA_GRAPH_BUILT / DOWNSTREAM_PROMOTION_BLOCKED`
Authority: public-safe architecture/recovery analysis only; never operational hotel authority.
Session: `SES-20260901T150500Z-GRAPHV2-001`
Observed live main at bootstrap: `3f96e510fc22246ec69ca22e8f10cf750c7e97cf`

## A. Executive V2

The strongest justified architecture is **not a rewrite**. The repository already contains a qualified COS V2 coordination kernel and a later multi-niche employment/acquisition layer. The correct V2 is their reconciliation:

```text
G-0001 NORTH STAR
  verified viable Swiss offer + accepted relocation
        │
        ├──────────────────────────────────────────────────────────┐
        │                                                          │
        ▼                                                          ▼
COORDINATION / CONTINUITY PLANE                           EMPLOYMENT DOMAIN PLANE
Session / Event / Claim / Lease / Fence                  Candidate Truth / Assets
ContextPack / Projection / Handoff                       Market Universe / Niches
        │                                                 Organization / Opportunity
        │                                                 Evidence / Routing / Packet
        │                                                 Response / Interview / Offer
        │                                                 Finance / Relocation / Learning
        │                                                          │
        └──────────────────── constrains / observes ────────────────┘
                                   │
                                   ▼
                         OPERATIONAL AUTHORITY PLANES
                     constrained DB ↔ Sheets ↔ Graph/Intel
                                   │
                                   ▼
                           QA / SLO / Evidence / Recovery
```

Hotels are `NICHE-001`. They remain a domain adapter and current operational authority, not the project boundary.

The Coordination Plane must remain a **derived coordination authority**, never a hidden replacement for operational truth. Candidate private truth/assets remain outside the public repo except public-safe hashes/status receipts.

## B. Current live truth reconstructed

### Stable truths

- North Star: `GOAL.md#G-0001`.
- Hotel operational authority remains `HS_ENTITY_EPOCH_2026-08-25_E4` / SHA `70307f4a...94cc6`.
- physical/active hotel authority remains `690/690`.
- `H-0691` remains unallocated.
- `CRM_UNIVERSE_COMPLETE = FALSE`.
- `OUTBOUND = CLOSED`; `send_allowed = 0`.
- coherent HotellerieSuisse source: 2061 records / 172 pages; `coverage_complete=true`.
- latest public-safe NEXT projection reports terminal mappings 658 / `RECONCILE_REQUIRED=1403`.
- multi-niche core, Candidate Truth foundation and W5 packet compiler are already merged after the original V2 architecture freeze.

### Coordination drift found

`main` is `3f96e510...`, but:

- `project-state.json.main_sha_observed = 02dad1a...`;
- `active-claims.json.as_of_main_sha = dd4d41c...`;
- Context Survival ancestry floor = `1bbabe4...` and pins stale coordination projections;
- token-6 embeds `terminal_mappings=657 / reconcile_required=1404` while NEXT says `658 / 1403`;
- `STATE.md` still presents B06 as the current domain NEXT;
- checkpoint CP0 says PASS as a historical attestation but is not a current-liveness proof;
- open PR inventory has materially changed since the machine project-state snapshot.

Issue #416 records this as a P0 coordination defect.

## C. Architecture delta

### Existing V2 — KEEP

- deterministic Session/Event/Claim/FencingToken kernel;
- append-only causal event semantics;
- ContextPack and zero-context death drill;
- Operational Graph vs Project Memory Meta Graph separation;
- authority ceilings and fail-closed outbound;
- process-local coordination as current justified primitive;
- no Kafka/Redis/K8s/vector DB without measured trigger;
- recovery/replay/security/empirical qualification corpus;
- PK-keyed operational authority and cross-plane reconciliation.

### Post-V2 additions — INTEGRATE

- one horizontal multi-niche employment core;
- `NICHE-001 = Hotels` compatibility layer;
- generic organizations/opportunities/application schemas;
- Candidate Truth and Asset contracts;
- Email Identity contract;
- Application Packet Compiler with stable application idempotency and versioned packet identity;
- response/outcome taxonomy.

### REFINE

1. **Current architecture pointer.** `V2_ARCHITECTURE.md` predates the multi-niche/candidate/application core and must be reconsolidated before it can continue as the sole canonical architecture.
2. **Goal graph.** Current `GOAL.md` still makes hotel-specific G-0500/G-0700 definitions first-class while multi-niche architecture proposes a generalized goal topology. Preserve legacy IDs through alias/compatibility mapping; do not renumber destructively.
3. **Checkpoint semantics.** Historical PASS must be bound to exact evidence/main/authority revision and cannot imply current liveness indefinitely.
4. **Coordination projection freshness.** Project-state/active-claims/context-pack must be rebuildable and rejected when internal preconditions disagree with domain NEXT.
5. **Asset approval semantics.** Technical QA != human approval. Public handoffs must not upgrade private `QA_PENDING` assets to `APPROVED`.
6. **Application readiness.** `PACKET_COMPILED != TARGET_READY != SEND_AUTHORIZED`. PR #415 proposes an AAG-bound target gate and must be semantically reviewed before merge.
7. **PR hygiene.** Old open architecture/domain PRs require explicit `SUPERSEDED | ACTIVE | BLOCKED | MERGE_CANDIDATE` classification.

## D. Canonical system boundaries

### Coordination authority

Owns:
- session identity;
- append-only coordination events;
- claims/leases/fencing;
- workstream ownership;
- ContextPack/project-memory projections;
- recovery navigation.

Must not own:
- hotel/entity authority;
- candidate private truth;
- external-action authorization;
- source membership facts.

### Operational market authority

Owns:
- canonical organizations/entities;
- source-record mapping;
- aliases/supersessions;
- evidence-backed opportunities;
- operational graph state;
- cross-plane committed state.

### Candidate authority

Owns:
- factual candidate canon;
- private references;
- claim permissions;
- asset approval state;
- selected external wording.

### Acquisition authority

Owns:
- application identity;
- packet version identity;
- channel policy;
- suppression/idempotency;
- send authorization;
- response/interview/offer outcomes.

A compiled packet is derived state, not permission to send.

## E. Hypergraph core

### Principal nodes

`Project`, `NorthStar`, `Goal`, `Objective`, `Checkpoint`, `Workstream`, `Task`, `Test`, `Evidence`, `Decision`, `Risk`, `Bug`, `Invariant`, `Repository`, `Commit`, `PR`, `Session`, `Agent`, `Claim`, `Lease`, `FencingToken`, `Event`, `ContextPack`, `Projection`, `AuthorityPlane`, `Niche`, `SourceSnapshot`, `SourceRecord`, `Organization`, `Location`, `Group`, `Opportunity`, `Person`, `Channel`, `CandidateFact`, `CandidateClaim`, `Asset`, `Application`, `Packet`, `ExternalAction`, `Response`, `Interview`, `Offer`, `FinancialModel`, `RelocationTask`.

### Critical hyperrelations

1. `Decision MULTI_NICHE_CORE`
   - generalizes hotel-specific market model;
   - preserves E4 authority;
   - modifies architecture/goal/data/application surfaces;
   - requires NICHE-001 equivalence tests;
   - creates future NICHE-N adapter boundary.

2. `Decision W5_DUAL_IDENTITY`
   - application identity = target + lane + channel;
   - packet identity additionally includes exact asset/readiness versions;
   - prevents CV revision from authorizing duplicate application;
   - must be coupled to target-readiness and external-action gates.

3. `Risk COORDINATION_PROJECTION_STALE`
   - affects Session/Claim/ContextPack/DeathDrill/Handoff;
   - contradicted by current main/NEXT;
   - blocks new coordination-state promotion;
   - requires event/projection rebuild and regression tests.

4. `Risk CANDIDATE_ASSET_APPROVAL_DRIFT`
   - private state = QA_PENDING pending human review;
   - public prose contains approval-like language;
   - blocks real packet/send readiness;
   - requires exact status projection and human approval event.

## F. COS traversal summary

- **L0 Visual:** architecture has two clusters (coordination V2, employment multi-niche) connected by prose but not one canonical diagram. REFACTOR.
- **L1 Execution:** current executable critical path is coordination repair → canonical architecture consolidation → target/candidate gate truth → real acquisition canary. Hotel source reconciliation remains parallel.
- **L2 State:** checkpoint and asset approval states have temporal ambiguity. REFACTOR.
- **L3 Dependency:** `ARCHITECTURE.md → V2_ARCHITECTURE.md` omits later core; `TASKS → old V2 program` omits W1–W5. P1/P0 continuity impact.
- **L4 Call:** W5 reuses Candidate Truth/Asset contracts correctly; PR #415 requires review for target-readiness coupling.
- **L5 Control:** fail-closed outbound is strong; stale ContextPack acceptance must remain impossible.
- **L6 DataFlow:** evidence→authority path is strong in hotels; candidate asset approval projection is weaker and partly prose-driven.
- **L7 Compute:** no measured need for distributed infrastructure.
- **L8 Knowledge:** graph/history are rich but post-V2 changes are not fully integrated.
- **L9 Semantic:** `complete`, `verified`, `approved`, `ready`, `authority`, `packet` need stricter version-bound definitions.
- **L10 Similarity:** explicitly non-authoritative; KEEP.
- **L11 GraphRAG:** recovery path exists but stale projections mean zero-context answer can be internally inconsistent. FAIL CURRENT.
- **L12 Memory:** classes exist; invalidation implementation/projection freshness currently degraded.
- **L13 Agent:** stale claim is a live defect. FAIL CURRENT.
- **L14 Tool:** connectors have explicit trust boundaries; local/runtime capability varies and must not change truth.
- **L15 Workflow:** external action gates are strong in principle; exact target-readiness integration is under PR review.
- **L16 Network:** NOT_APPLICABLE beyond providers/tool boundaries at current scale.
- **L17–L19:** domain-specific projections only when justified; no new infrastructure for symmetry.

## G. Ranked gap matrix

| ID | Gap | Sev | Blast | Fix |
|---|---|---|---|---|
| GR2-001 | coordination state/claims/context are stale and mutually inconsistent | P0 | project-wide continuation | rebuild from durable events/claims; freshness regression; exact-main death drill |
| GR2-002 | canonical architecture excludes later multi-niche/candidate/application architecture | P0 architecture | all future implementation | produce one V2.2 architecture; supersede competing candidate docs as subcontracts |
| GR2-003 | canonical goal graph conflicts semantically with multi-niche target graph | P1 high | roadmap/metrics/priorities | compatibility/alias goal migration; preserve IDs/history |
| GR2-004 | asset technical QA can be confused with human APPROVED | P0 before outbound / P1 now | external representation | canonical asset-state projection + explicit human approval event |
| GR2-005 | checkpoint PASS is not always evidence-revision bound in operator interpretation | P1 | false completion | every checkpoint receipt pins commit, authority, evidence hashes, valid-until semantics |
| GR2-006 | root TASKS/V2 program predates W1–W5 employment-core implementation | P1 | execution routing | recompile tasks/checkpoints from integrated architecture |
| GR2-007 | many stale/open PRs remain unclassified | P1 | concurrency/operator error | semantic PR inventory + explicit supersession/closure |
| GR2-008 | current hotel authority remains unresolved against 1403 source records | P0 domain | CRM completeness | continue bounded entity-resolution in isolated workstream |
| GR2-009 | H-0580 semantic cross-plane drift remains unresolved from prior recovery | P0 authority promotion | hotel authority | first-party/HotellerieSuisse re-attestation + atomic repair; no inferential fix |
| GR2-010 | target-readiness is not yet merged into W5 main | P0 before real application | application correctness | review/merge or replace PR #415 after exact diff/CI/ancestry |
| GR2-011 | branch protection disabled | P1 | repo integrity | decide after local-first/solo workflow tradeoff; not automatically enable |
| GR2-012 | Gmail signature installation cannot currently be verified by connected settings API | P2 | UX only until outbound | Mac mini / sendAs-capable runtime + readback; do not block architecture |

## H. Greenfield ideal vs current

Greenfield ideal:

```text
Coordination Kernel
       ↓
Unified Employment Core
       ├─ Niche adapters
       ├─ Candidate authority
       ├─ Opportunity/evidence
       ├─ Application/packet/message
       ├─ Response/interview/offer
       └─ Finance/relocation/learning
       ↓
Operational authority adapters
       ↓
Observability/recovery
```

Migration classification:
- V2 coordination kernel: KEEP/REFINE.
- Hotel engines: KEEP as NICHE-001 adapter.
- generic multi-niche overlay: KEEP, prove compatibility.
- Candidate Truth: KEEP.
- current CV artifacts: QA_PENDING until human approval.
- W5 packet compiler: KEEP/REFINE with exact target-readiness gate.
- old hotel-only goal semantics: MIGRATE via compatibility map.
- stale ContextPack/project-state: REBUILD, not patch by hand.
- stale PRs: SUPERSEDE/CLOSE after semantic inventory.
- distributed infra: DEFER.

## I. Security / trust model delta

Trust boundaries:

- Web/provider/GitHub issue/comment/email content = UNTRUSTED_DATA.
- Git code/contracts = versioned coordination evidence, not operational authority.
- Drive private Candidate Canon/assets = sensitive candidate authority.
- constrained DB + synchronized operational planes = domain authority.
- External send/provider receipt = irreversible external-action evidence.

New required security invariants:

1. public repo may store asset hashes/status, never private phone/reference data or raw private candidate evidence;
2. `QA_PENDING` cannot satisfy `APPROVED` lane gate;
3. stale ContextPack cannot acquire mutation authority;
4. stale fencing token cannot mutate a claimed scope;
5. application packet cannot become send authorization;
6. target-readiness receipt must be bound to exact organization/opportunity/lane/channel;
7. asset revision cannot bypass application idempotency;
8. provider timeout after potential acceptance requires provider-state verification before retry.

## J. Recovery model

Current operational recovery remains authority-first.

Coordination recovery must be requalified after repair:

```text
live main
→ durable event/claim records
→ validate hash chain/schema
→ replay projections
→ compare active-claim semantics to live domain NEXT
→ rebuild project-state/graph/context-pack/CSP
→ delete projections
→ rebuild again
→ exact semantic equality
→ zero-context death drill
```

A saved projection is never sufficient recovery evidence.

## K. Current STOP/CONTINUE decision

`CONTINUE_READ_ONLY_REFACTOR` is allowed inside this isolated scope.

`STOP` applies to:
- mutation of `docs/state/v2/**` while token-6 scope collision is unresolved;
- hotel authority promotion;
- H-ID allocation;
- real application compilation using candidate assets as APPROVED;
- outbound/send authorization.

## L. Immediate executable frontier

1. `GR2-T001` — repair coordination lineage/claim projection through explicit supersession, not silent edits.
2. `GR2-T002` — rebuild V2 machine state/ContextPack/CSP from current main and durable events; add stale-precondition regressions.
3. `GR2-T003` — compile canonical `V2.2` architecture integrating coordination + multi-niche + Candidate/Application OS.
4. `GR2-T004` — compile goal compatibility map; do not destructively renumber legacy IDs.
5. `GR2-T005` — semantic inventory all open PRs; classify ACTIVE/MERGE_CANDIDATE/BLOCKED/SUPERSEDED.
6. `GR2-T006` — reconcile candidate asset public status to private QA_PENDING; require human approval event for APPROVED.
7. `GR2-T007` — adversarially review PR #415 target-readiness integration.
8. Parallel domain lane may continue H-0580/current-source reconciliation only under disjoint valid claim/authority gates.

## M. Definition of Done for reconsolidation

This reconsolidation is NOT DONE until:

- current main/authority/claim/event state is coherent;
- zero stale active claim survives without explicit semantics;
- ContextPack/CSP rebuild passes from durable sources;
- one canonical architecture describes both coordination and employment domain core;
- root GOAL/TASKS/HANDOFF/ARCHITECTURE pointers resolve without semantic contradiction;
- current asset readiness is exact and human approval separated from technical QA;
- critical open PRs are semantically classified;
- every P0 above is either resolved or represented as explicit BLOCKER with owner/test/trigger;
- zero-context death drill can recover the exact next safe task without chat.

Until then, do not declare `V2_FINAL`.

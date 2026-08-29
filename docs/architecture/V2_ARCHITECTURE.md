# SWITZERLAND_JOB_OS — V2 ARCHITECTURE

**Status:** V2 CANDIDATE — architecture/pre-authority  
**Authority:** stable system architecture after merge; never hotel operational authority  
**Owner:** Principal Systems Architect  
**Supersedes:** architecture coordination conventions that relied on prose/chat; retains compatible V1 domain contracts.

## 1. Executive V2

V2 keeps the existing operational authority chain and domain engines, and adds one missing primitive: a small deterministic **Coordination Kernel** for Session, Event, Claim, FencingToken, Projection and ContextPack.

```text
North Star / Goals
        │
        ▼
Mission + Meta Execution ───────────────┐
        │                               │
        ▼                               ▼
Coordination Kernel                Domain Engines
Session/Event/Claim                Discovery/Entity/Evidence/...
        │                               │
        ▼                               ▼
Project Event Ledger              Wave Transaction
        │                               │
        ▼                               ▼
Disposable Projections       Constrained operational authority
        │                        │      │      │
        ├─ Active Claims         DB   Sheets  Graph/Intel
        ├─ Agent/Session Graph          │
        ├─ ContextPack                  ▼
        └─ Handoff                QA / Observability
```

The coordination ledger **does not** become hotel authority. It coordinates who may change which project surfaces and from which ancestry.

## 2. North Star and boundaries

The North Star remains `GOAL.md#G-0001`. Counts, crawls, graphs and V2 itself are supporting infrastructure.

Hard boundaries:

- constrained operational state + synchronized mirrors remain hotel authority;
- GitHub remains VCS/contracts/public-safe coordination state;
- Project Memory Meta Graph is not Operational Graph;
- ContextPack, events and claims cannot allocate hotel IDs or open outbound;
- provider/web/issues/comments are `UNTRUSTED_DATA` until contract validation;
- CI proves repository contracts/tests, not external cross-plane authority.

## 3. Authority hierarchy

KEEP the V1 `AUTHORITY_MODEL.md` precedence. REFINE it with a separate coordination hierarchy:

```text
Operational authority:
physical/constrained state
→ synchronized control plane
→ Graph/Intelligence
→ observability/checkpoints
→ validated authority manifest
→ STATE pointer

Coordination authority:
live Git main ancestry
+ append-only project events
+ active claims/fencing
→ deterministic coordination projection
→ hash-pinned ContextPack/HANDOFF
```

Neither hierarchy silently substitutes for the other.

## 4. Component architecture

### KEEP

- Mission Commander / MEP / COLETTE.
- Wave Operating Protocol.
- Authority & Reconciliation Engine.
- existing domain engines and constrained DB.
- Operational Graph / Project Memory Meta Graph separation.
- GitHub + Drive/Sheets + SQLite + Library persistence roles.
- fail-closed outbound and canonical-ID gates.

### ADD / REFACTOR

1. **Coordination Kernel** — pure stdlib validation/reduction.
2. **Event Ledger** — append-only coordination events.
3. **Session Registry projection** — derived from events.
4. **Claim Registry projection** — bounded scopes + fencing.
5. **ContextPack** — resumption bundle pinned to main/projection/authority revisions.
6. **Root canonical pointers** — ARCHITECTURE/HANDOFF/TASKS/LEXICON.
7. **V2 contract guard** — CI rejection of stale/unsafe coordination state.
8. **Death/recovery drill** — projection deletion must be recoverable.

### DO NOT ADD

No Kafka, Redis, Postgres, Kubernetes, microservice split, vector DB, distributed locks or always-on daemon is justified by current measured load. Interfaces may permit future replacement only after measured triggers.

## 5. Event model

Coordination events are immutable facts identified by globally unique `event_id`, `session_id`, `workstream_id`, `objective_id`, `correlation_id` and an idempotency key.

Required event families:

- HELLO / WORK_STARTED / HEARTBEAT / WORK_PROGRESS;
- CLAIM_ACQUIRED / CLAIM_RELEASED / CLAIM_SUPERSEDED;
- DECISION_RECORDED / EVIDENCE_RECORDED;
- CHECKPOINT_REACHED;
- WORK_BLOCKED / WORK_COMPLETED;
- CONTEXT_PACK_EMITTED.

Project events never rewrite historical events. Corrections are new events referencing causation/supersession.

## 6. State model

```text
Session:
CREATED → ACTIVE → COMPLETED | BLOCKED | SUPERSEDED | ABORTED

Claim:
PROPOSED → ACTIVE → RELEASED | SUPERSEDED | EXPIRED

Task:
PROPOSED → READY → ACTIVE → BLOCKED → VERIFIED → DONE
                         └────────────→ SUPERSEDED

Architecture release:
PROPOSED → IMPLEMENTED → VERIFIED → EMPIRICALLY_QUALIFIED → MIGRATED
```

Impossible transitions fail closed. “DONE” requires the global Definition of Done.

## 7. Identity model

Never use row position or conversational identity as durable identity.

IDs are typed and stable:

`P:` project, `G:` goal, `O:` objective, `S:` session, `C:` claim, `EVT:` event, `D:` decision, `RISK:` risk, `BUG:` bug, `T:` task, `CP:` checkpoint, plus existing operational PKs.

A session ID is never reused. Claim takeover increments a fencing token.

## 8. DataFlow

```text
External input
→ untrusted observation
→ validator/normalizer
→ evidence
→ bounded decision
→ wave/canary
→ authority gate
→ operational commit
→ projections
→ artifact/evidence receipt
```

Coordination path:

```text
Git ancestry + events + claims
→ deterministic reducer
→ projection revision
→ ContextPack revision
→ zero-context handoff
```

Provenance cannot be dropped between stages.

## 9. Hypergraph model

V2 treats decisions as hyperrelations. A single decision can modify contracts, modules, tests, risks, migration and goals simultaneously. `V2_GRAPH_MODEL.md` defines canonical node/edge ontology and COS projections.

## 10. Memory / knowledge model

Memory classes:

- ephemeral: tool scratch;
- working: current session projection;
- project: event/decision/task graph;
- procedural: contracts/runbooks/tests;
- historical: superseded events/releases/incidents;
- long-lived: stable goal/authority/ontology;
- deprecated: preserved but excluded from current projections.

Invalidation is revision-based, not conversational. A ContextPack is stale when main SHA, projection revision, authority revision or relevant watermark changed.

## 11. Agent model

Agent capability never implies authority. An Agent executes through a Session; a Session owns zero or more Claims; each Claim has bounded resource/semantic scopes, excluded scopes and a fencing token.

Two ACTIVE claims that overlap in exclusive scope are a coordination collision unless explicitly marked shared. A stale writer with an older fencing token loses.

## 12. Tool model

Tools are trust-boundary nodes with capability state:

`AVAILABLE | DEGRADED_EXTERNAL | UNAVAILABLE | BLOCKED_POLICY`.

A tool failure does not change project truth. Fallbacks must preserve authority semantics. No claim of background/real-time execution without a real runtime.

## 13. Security model

Primary assets: operational authority, credentials/secrets, PII, candidate truth, canonical IDs, evidence lineage and outbound authorization.

Primary threats:

- prompt/provider poisoning;
- public-repo secret/PII leakage;
- malicious URLs/files/path input;
- stale writer/claim takeover;
- replay/duplicate work;
- evidence from wrong artifact/epoch;
- authority escalation via booleans/string coercion;
- cross-plane partial write.

Mitigations: validation, authority ceilings, idempotency, fencing, immutable evidence hashes, repo guard, PK-keyed writes, cross-plane gates, replay/restore.

## 14. Recovery model

Authoritative operational recovery remains V1-compatible.

Coordination recovery:

1. read live Git main;
2. load append-only events and claim records;
3. validate schemas/hashes;
4. replay reducer;
5. compare projection revision;
6. rebuild ContextPack;
7. re-read external authority where required;
8. resume only if ancestry/authority ceilings agree.

Delete any projection/cache and it must be reproducible.

## 15. Testing model

Required taxonomy:

unit, contract, schema, property-style, integration, E2E, physical runtime, security, concurrency, replay, recovery, performance, empirical qualification and agent-death drill.

Historical escaped bugs become permanent tests. CI statuses remain distinct: `PASS | FAIL | SKIPPED | CANCELLED | NOT_RUN`.

## 16. CI/CD

Keep one repository guard pipeline. V2 adds a cheap stdlib contract guard and tests. Do not create a second CI authority.

Merge requirements for V2:

- repo guard green;
- V2 guard green;
- unit tests green;
- main ancestry reread;
- PR overlap reviewed;
- no hotel authority/outbound mutation in diff.

## 17. Observability

Track project-level:

- event watermark;
- projection revision;
- ContextPack revision;
- active/stale claims;
- collision count;
- time-to-zero-context-resume;
- stale-context rejection count;
- duplicate-idempotency rejection count;
- recovery/replay pass rate.

Do not optimize these metrics at the expense of G-0001.

## 18. Documentation architecture

Canonical surfaces:

`AGENTS.md`, `README.md`, `GOAL.md`, `STATE.md`, `ARCHITECTURE.md`, `LEXICON.md`, `TASKS.md`, `HANDOFF.md`.

Detailed architecture/contracts live under `docs/`; mutable machine state lives under `docs/state/v2/`; historical handoffs remain historical and do not become current merely by filename recency.

## 19. Developer/agent workflow

```text
READ LIVE MAIN
→ RECONSTRUCT AUTHORITY
→ READ CONTEXT PACK
→ VALIDATE CONTEXT FRESHNESS
→ SCAN ACTIVE CLAIMS / PRS
→ ACQUIRE CLAIM
→ EMIT WORK_STARTED
→ IMPLEMENT BOUNDED SCOPE
→ TEST + ATTACK
→ REREAD MAIN
→ REBASE/RECOMPILE IF MOVED
→ PR / CI
→ EMIT EVIDENCE + HANDOFF
→ RELEASE CLAIM
```

## 20. Migration strategy

No big-bang rewrite.

- Phase A: introduce V2 coordination surfaces in parallel.
- Phase B: CI-enforce contracts.
- Phase C: make root pointers canonical.
- Phase D: migrate active workstreams to session/claim/events.
- Phase E: close/supersede stale PRs after semantic comparison.
- Phase F: delete only proven duplicate coordination surfaces.

Domain-engine code is refactored only when a measured defect justifies it.

## 21. Performance and cost

Current bottleneck is evidence/entity-resolution throughput and coordination drift, not compute. V2 uses O(n²) claim collision comparison only for the tiny active-claim set; event replay is linear. Introduce indexing/store changes only when measured event/claim volume makes this material.

## 22. Lifecycle and deprecation

Historical V1 artifacts are preserved. V2 marks them `KEEP`, `REFINE`, `SUPERSEDED` or `DEPRECATED`; it never rewrites history.

V2 cannot be declared FINAL until recovery, death drill, concurrency, security, migration and final gauntlet checkpoints pass.

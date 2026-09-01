# SWITZERLAND_JOB_OS — V2.2 CANONICAL ARCHITECTURE

Status: **CANDIDATE / ARCHITECTURE-ONLY**  
Issue: #422  
Base main: `7a610cd8c6ec96930983471b80112c667be9aeaf`  
Claim: `CLAIM-GRAPHV22-ARCH-009` / fencing token 9  
Authority ceiling: `ARCHITECTURE_AND_COORDINATION_ONLY_NO_DOMAIN_OR_EXTERNAL_MUTATION`

This document is the V2.2 candidate that reconciles the V2 Coordination Kernel with the Multi-Niche Employment OS and the implemented Candidate/Application stack. It changes **architecture semantics only**. It grants no hotel authority, candidate-truth authority, application execution authority or outbound permission.

## 1. North Star

`GOAL.md#G-0001` remains immutable in meaning:

> secure a truthful, verified, economically viable Swiss offer that Roberto accepts and can relocate around sustainably.

The optimization target remains:

```text
P(verified viable Swiss offer × Roberto accepts × relocation succeeds)
```

Counts, niches, graphs, CVs, packets, applications and coordination are supporting systems.

## 2. Canonical system topology

```text
                              G-0001 NORTH STAR
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
                ▼                     ▼                     ▼
       COORDINATION PLANE      EMPLOYMENT CORE        AUTHORITY PLANES
   Session/Event/Claim/Lease   Candidate/Market/      domain truth remains
   Fencing/Context/Recovery    Opportunity/Application independent of graph
                │             Response/Offer/Relocation       │
                │                     │                       │
                └──────────── constrains / observes ──────────┘
                                      │
                                      ▼
                              TEST + EVIDENCE PLANE
```

The system has **three independent authority families**. No projection may collapse them:

1. **Coordination authority** — Git ancestry + append-only events + claims/fencing → reproducible projections/ContextPack.
2. **Operational domain authority** — constrained DB/state and reconciled mirrors for market/entity state.
3. **Candidate/external-action authority** — private Candidate Canon/asset approval + explicit action authorization for application/outbound.

A PASS in one family never grants authority in another.

## 3. Horizontal employment core

Hotels are `NICHE-001`, not the system boundary. The horizontal core owns generic contracts for:

1. Candidate Truth
2. Candidate Assets
3. Niche Registry
4. Sources + Snapshots
5. Organizations / Locations / Brands / Groups
6. Entity Resolution
7. Role Families / Vacancies / Opportunities
8. People / Recruiters
9. Channels / Policies
10. Evidence / Freshness / Search Proof
11. Benefits / Housing
12. Fit / Ranking
13. Application Readiness
14. Application Packet Compilation
15. Messaging Identity / Templates
16. External Action Gate
17. Response / Outcome
18. Interview
19. Offer Verification
20. Financial Viability
21. Relocation
22. Learning / Experiments
23. QA / Governance / Recovery

Niche adapters specialize discovery, taxonomy, source scope, entity semantics, role families, recruiting channels, scoring and QA. They cannot redefine core identity, evidence, safety or outbound contracts.

## 4. NICHE-001 compatibility boundary

Existing hotel authority is preserved as a compatibility projection/adapter.

```text
HOTELS_V2 / HOTEL_GROUPS_V2
            │
            ▼
     NICHE-001 ADAPTER
            │
            ▼
ORGANIZATION / LOCATION / GROUP abstractions
```

Rules:

- no destructive migration of hotel authority;
- existing H-IDs remain immutable operational identifiers;
- generic organization IDs are additive identities with explicit bridge lineage;
- no generic schema may reserve or allocate H-IDs;
- hotel counts are compatibility tests, not the North Star;
- E4/690 remains authoritative until an independently eligible authority migration occurs.

## 5. Candidate truth and asset boundary

Candidate truth is not public Git state and is not inferred from rendered assets.

```text
PRIVATE CANDIDATE CANON
        │
        ├── Claim Ledger
        │      └── provenance / verification / approval
        │
        └── Asset Compiler
               ├── CV_ENTRY
               ├── CV_HYBRID
               ├── CV_CREATIVE
               └── supporting artifacts
```

Asset states are semantically distinct:

`DRAFT → TECHNICALLY_VALIDATED → QA_PENDING → APPROVED → DEPRECATED`

Technical rendering/ATS/hash tests cannot produce `APPROVED`. Human/private authority must do so where required.

## 6. Opportunity and application identity

A vacancy/opportunity is an evidence-backed temporal entity. An application is a stable intent identity. A packet is a versioned compilation of that intent.

```text
Organization
   + Opportunity
   + Candidate lane
        │
        ▼
APPLICATION identity (stable)
        │
        ├── Packet v1
        ├── Packet v2
        └── Packet vN
```

Therefore:

- asset revisions do not create duplicate applications;
- target changes do create different application identities;
- packet receipts are version-specific provenance;
- application rows must not pretend a stale asset pointer is the current packet truth;
- `PACKET_COMPILED` is never equivalent to `SEND_AUTHORIZED`.

## 7. External action gate

All irreversible employer-facing actions pass a separate command gate:

```text
verified opportunity
+ candidate truth valid
+ approved applicable assets
+ target-bound readiness
+ channel policy
+ suppression
+ idempotency
+ freshness
+ explicit authorization where required
        │
        ▼
EXTERNAL ACTION COMMAND
        │
        ├── ACCEPTED → durable receipt
        ├── REJECTED → typed failure
        └── UNKNOWN/timeout → reconcile before retry
```

Retries are never inferred safe from absence of a local receipt.

Current global lock remains:

```text
CRM_UNIVERSE_COMPLETE = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```

## 8. Response-to-offer lifecycle

```text
APPLICATION
→ ACTION RECEIPT
→ RESPONSE
→ OUTCOME
→ INTERVIEW
→ OFFER
→ OFFER VERIFICATION
→ FINANCIAL VIABILITY
→ HUMAN ACCEPTANCE
→ RELOCATION READY
→ G-0001 COMPLETE
```

Observed employer reasons and inferred hypotheses are different node types. A rejection may influence strategy only through evidence-labeled learning.

## 9. Goal compatibility graph

Legacy goal IDs remain durable. V2.2 introduces **target capabilities**, not replacement IDs.

| Durable goal | Existing meaning | V2.2 capability projection |
|---|---|---|
| G-0001 | verified viable offer + relocation | unchanged North Star |
| G-0500 | canonical hotel universe / CRM parity | NICHE-001 authority + compatibility |
| G-0600 | candidate readiness | Candidate Truth + Asset Approval |
| G-0700 | hotel intelligence / outreach readiness | Opportunity/Evidence/People/Channel intelligence |
| G-0800 | maximum acquisition readiness | Generic Acquisition + External Action Gate |

Target concepts from the multi-niche proposal (`Candidate Truth`, `Candidate Assets`, `Generic Market Universe`, `Niche Coverage`, `Opportunity Intelligence`, `Acquisition`, `Response`, `Offer`, `Finance`, `Relocation`) become capability nodes attached with `IMPLEMENTS`, `CONTRIBUTES_TO` and `REQUIRED_BY` edges. They do **not** renumber or silently supersede durable goal IDs.

A later explicit goal-schema migration may introduce new durable IDs only with an ADR, compatibility aliases, migration tests and zero broken historical references.

## 10. Coordination plane contract

Coordination is intentionally small:

```text
Agent → Session → Claim/Fencing → Events → Reducer
                                ↓
                       disposable projections
                       active claims / graph
                       ContextPack / handoff
```

Coordination may determine **who can mutate a surface**, but not whether a domain proposition is true.

Permanent invariants:

- session IDs are unique;
- fencing is monotonic;
- stale writers lose;
- active-claim projections are reducer-derived;
- root NEXT ownership must equal active-claim projection;
- ContextPack/CSP must be reproducible;
- zero-context death drill must pass;
- coordination state never opens outbound or allocates H-IDs.

## 11. Evidence model

All external data enters as `UNTRUSTED_DATA`.

Evidence nodes require:

- source identity;
- observation timestamp;
- artifact/hash where applicable;
- authority class;
- freshness/TTL policy;
- claims supported and not supported;
- transformation lineage.

Similarity, ranking and LLM inference are review accelerators, never authority.

## 12. State machines

### Opportunity

`DISCOVERED → VERIFIED → CURRENT → ELIGIBLE → EXPIRED|FILLED|WITHDRAWN`

### Application

`PROPOSED → READINESS_PENDING → READY_NO_SEND → PACKET_COMPILED → AUTHORIZATION_PENDING → ACTION_SUBMITTED → WAITING → RESPONDED → CLOSED`

No state named `READY` implicitly means send permission.

### Asset

`DRAFT → TECHNICALLY_VALIDATED → QA_PENDING → APPROVED → DEPRECATED`

### Claim

`PROPOSED → ACTIVE → RELEASED|SUPERSEDED|EXPIRED`

### Offer

`OBSERVED → VERIFIED → FINANCIALLY_ASSESSED → ACCEPTABLE|NOT_ACCEPTABLE → ACCEPTED|DECLINED`

## 13. Source-of-truth matrix

| Concept | Authority | Projections / mirrors |
|---|---|---|
| coordination ownership | event/claim ledger + Git ancestry | active-claims, ContextPack, graph snapshot, NEXT ownership |
| hotel canonical identity | constrained operational authority E4 | Sheets/graph/intelligence/observability |
| generic niche organization | generic operational store once promoted | niche views / graph |
| candidate facts | private Candidate Canon / Claims Ledger | CVs, public-safe receipts |
| candidate asset approval | private asset authority | public-safe hash/status receipt |
| opportunity fact | validated evidence store | shortlist/ranking/views |
| application identity | application ledger | dashboards/queues |
| packet provenance | packet receipt ledger | application summaries |
| send authorization | explicit action-gate authority | queues/UI |
| employer response | message/provider receipt + typed ingestion | metrics/learning graph |
| offer acceptance | explicit human decision | project completion projection |

Any consumer that elevates a mirror/projection to independent authority is a P0/P1 defect according to blast radius.

## 14. Security boundaries

Primary trust boundaries:

- public Git ↔ private candidate data;
- web/provider payload ↔ validated evidence;
- coordination ↔ operational authority;
- packet generation ↔ external action;
- DB authority ↔ Sheets/graph mirrors;
- model inference ↔ evidence-backed claim.

Threat families include stale writer, replay, prompt/provider poisoning, PII leakage, path/URL injection, cross-plane partial write, duplicate spend/send, stale asset approval and target-readiness substitution.

## 15. Recovery architecture

A successor must recover without chat:

1. read live main;
2. validate Context Survival;
3. replay events/claims;
4. identify active claim/fencing;
5. load GOAL + V2.2 architecture + TASKS;
6. separately re-read any external operational/private authority needed for intended mutation;
7. reject stale projections;
8. execute only the highest-value non-colliding safe task.

Deleting graph/ContextPack/active-claims must not destroy history; they are reproducible projections.

## 16. Overengineering filter

Do not add Kafka, Redis, Kubernetes, microservices, vector DBs or distributed consensus for architectural symmetry. Current coordination volume fits deterministic files + Git + CI. Add infrastructure only against measured throughput, availability or concurrency triggers.

## 17. Architecture delta

### KEEP
- G-0001 North Star.
- E4/690 operational authority semantics.
- Wave Operating Protocol / fail-closed gates.
- V2 Coordination Kernel.
- additive Multi-Niche schema strategy.
- NICHE-001 compatibility approach.
- Candidate/Application compiler semantics already implemented and tested.

### REFINE
- “Domain Engines” → explicit horizontal employment core.
- goal tree → compatibility graph rather than competing numbering scheme.
- Candidate readiness → split technical validity, private approval and target-bound readiness.
- Application state → stable identity + versioned packet provenance.
- CI → deterministic coordination rebuild is a permanent invariant.

### DEPRECATE AS CANONICAL AFTER V2.2 ACCEPTANCE
- `docs/architecture/V2_ARCHITECTURE.md` as the latest architecture surface;
- `docs/architecture/MULTI_NICHE_EMPLOYMENT_OS_V1.md` as a competing architecture document.

They remain historical design evidence and are never deleted.

## 18. V2.2 acceptance gates

V2.2 can be promoted only when:

- CP-V22-00 live truth reconstructed;
- CP-V22-01 token9/no-collision coordination state valid;
- CP-V22-02 architecture + goal compatibility graph persisted;
- CP-V22-03 authority/SSOT matrix has no unexplained duplicates;
- CP-V22-04 TASKS/checkpoints recompiled;
- CP-V22-05 old architecture surfaces explicitly superseded, not erased;
- CP-V22-06 deterministic rebuild + Context Survival + death drill PASS;
- CP-V22-07 full repo CI PASS;
- CP-V22-08 exact-main post-merge qualification PASS.

Until CP-V22-08, status is **V2.2 CANDIDATE**, never `V2_FINAL`.

## 19. Immediate executable frontier

1. persist machine-readable goal compatibility graph;
2. compile V2.2 gap/decision ledger;
3. recompile TASKS/checkpoints around implemented W1-W5 and remaining W6-W10;
4. reconcile coordination projections under token9;
5. run CI/adversarial gauntlet;
6. merge only from unchanged/compatible main;
7. post-merge death drill;
8. then classify remaining PRs against V2.2, beginning with blocked PR #415.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

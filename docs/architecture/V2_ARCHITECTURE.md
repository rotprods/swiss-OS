# SWITZERLAND_JOB_OS — CANONICAL V2.2 ARCHITECTURE

**Status:** IMPLEMENTED_ARCHITECTURE / DOMAIN_MIGRATION_PARTIAL  
**Authority:** stable system architecture; never hotel/candidate/application operational authority  
**Owner:** Principal Systems Architecture  
**Source revision:** `/GRAPH-REFACTOR-V2` reconsolidation + merged W1–W5  
**Supersedes:** prior V2 architecture prose where incompatible; preserves compatible V1 domain contracts and historical truth.

## 1. Executive V2.2

SWITZERLAND_JOB_OS is one Swiss employment-acquisition operating system with three explicit planes:

```text
                     G-0001 NORTH STAR
                            │
        ┌───────────────────┼────────────────────┐
        ▼                   ▼                    ▼
COORDINATION PLANE    EMPLOYMENT CORE     OPERATIONAL AUTHORITY
Session/Event/Claim   Candidate Truth     constrained DB
Fencing/ContextPack   Assets              Sheets/control plane
Recovery/Handoff      Market/Niches       Evidence/Graph/Intel
                      Opportunities        External providers
                      Applications
                      Responses
                      Interviews/Offers
                      Finance/Relocation
```

The planes constrain one another but do not silently substitute for one another.

**Hotels are NICHE-001, not the system boundary.** The hotel universe and immutable H-IDs remain a specialized operational projection/adapter while generic employment concepts live in the multi-niche core.

## 2. North Star

G-0001 remains unchanged: maximize the probability of a truthful, legal, verified, economically viable Swiss offer that Roberto accepts and can relocate for sustainably.

Counts, scrapes, canonical hotels, niches, messages, applications and architecture maturity are supporting signals, not success.

## 3. Authority model

### 3.1 Operational truth

Authority is concept-specific.

- hotel/entity operational truth: constrained operational DB + matching authority manifest, synchronized control-plane mirror and evidence;
- candidate private truth: Candidate Canon / Claims Ledger in the private authority plane;
- application/outreach truth: application/action ledgers + provider receipts;
- external employer truth: claim-level evidence with freshness/scope/provenance;
- financial truth: sourced offer terms + explicit assumptions/ranges.

No GitHub coordination projection may override these.

### 3.2 Coordination truth

```text
live Git main ancestry
+ append-only project events
+ claims/fencing tokens
        ↓ deterministic reducer
coordination projection
        ↓
ContextPack / Context Survival / Handoff
```

Projections are disposable; event/claim history is durable. A stale writer loses to a higher fencing token.

### 3.3 Stable architecture truth

`ARCHITECTURE.md` points here. Historical architecture documents remain evidence/history, not competing current authority.

## 4. Core component model

### A. Coordination Kernel

Session, Event, Claim, Lease semantics, FencingToken, reducer, projection revision, ContextPack, Context Survival, death drill.

Responsibilities: ownership, ancestry, continuity, collision detection, recovery.

Explicit non-responsibilities: hotel identity decisions, candidate facts, application authorization, H-ID allocation, email sending.

### B. Candidate Truth OS

Candidate Canon → Claims Ledger → lane truth gates.

Allowed states include `VERIFIED`, `UNKNOWN`, `CONFLICT`; external claims require approved evidence/wording. Technical QA never equals human approval.

### C. Candidate Asset OS

Candidate truth → versioned asset manifests → renderer → text/render/link QA → human approval → approved asset.

Primary families: CV_MASTER, CV_ENTRY, CV_HYBRID, CV_CREATIVE, portfolio/case studies where lane-relevant, email identity/signature.

### D. Multi-Niche Market Core

Generic entities: NICHES, NICHE_ADAPTERS, ORGANIZATIONS, LOCATIONS, GROUPS, BRANDS, SOURCES, SNAPSHOTS, SOURCE_RECORDS, PEOPLE, CHANNELS, ROLE_FAMILIES, OPPORTUNITIES, EVIDENCE, BENEFITS, HOUSING, FIT.

A niche adapter declares taxonomy, source/snapshot semantics, entity resolution, roles, seasonality, channels, scoring extensions and QA. Global truth/governance is never forked per niche.

### E. NICHE-001 Hotels

`canonical_hotels` remains authoritative during compatibility migration. `legacy_hotel_org_bridge` maps hotels into generic organizations. W2 must prove semantic equivalence before any authority migration. CP-0750 remains a hotel-specific scale checkpoint, not North Star progress.

### F. Application Packet Compiler

Inputs: organization + opportunity + lane + channel + evidence + candidate truth + approved assets.

Outputs: stable application identity, versioned packet identity, selected assets/claims/evidence and reason vector.

Application idempotency is independent of CV revision; changing an asset cannot authorize duplicate application.

### G. Application Adversarial Gate

`PACKET_COMPILED != SEND_AUTHORIZED`.

Before any irreversible action: target binding, evidence freshness, candidate asset approval, channel policy, suppression, idempotency, duplicate/group logic and explicit user authorization must all pass.

### H. Response / Learning Engine

APPLICATION → THREAD → RESPONSE → typed OUTCOME → observed reason / inferred hypothesis separation → lane/CV/template/channel/niche metrics.

Canonical outcomes: ACKNOWLEDGED, NO_VACANCY, REJECTED, MORE_INFO, INTERVIEW, OFFER, WITHDRAWN, OTHER.

### I. Interview / Offer / Finance / Relocation

Interview creates preparation/follow-up state. Offer verification precedes sourced financial viability. G-0001 closes only after offer acceptance and relocation readiness.

## 5. Data and graph model

Operational relational state is the authority substrate for high-volume entities. Graphs are relationship projections unless explicitly declared authoritative for a concept.

### Project Memory Meta Graph

Goals, checkpoints, sessions, claims, decisions, risks, artifacts, tests, evidence, architecture and workstreams.

### Operational Graph

Organizations, groups, people, channels, opportunities, applications and domain relationships derived from constrained operational state.

Never treat project-memory graph JSON as a full operational backup.

## 6. Temporal hypergraph semantics

Every material node/edge carries where applicable: `valid_from`, `valid_until`, source event/commit, authority, evidence, confidence and supersession. Corrections append new truth and use `SUPERSEDES`; history is not rewritten.

Major decisions are hyperrelations connecting contracts, modules, tests, risks, migration and goals.

## 7. State machines

```text
Session: CREATED → ACTIVE → COMPLETED | BLOCKED | SUPERSEDED | ABORTED
Claim: PROPOSED → ACTIVE → RELEASED | SUPERSEDED | EXPIRED
Task: PROPOSED → READY → ACTIVE → BLOCKED → VERIFIED → DONE
Asset: DRAFT → QA_PENDING → APPROVED | DEPRECATED
Application: COMPILED → GATED → AUTHORIZED → SUBMITTED → RESPONSE/INTERVIEW/OFFER/... 
Offer: RECEIVED → VERIFYING → VERIFIED → FINANCIALLY_VIABLE | NOT_VIABLE → ACCEPTED | DECLINED
Architecture: PROPOSED → IMPLEMENTED → VERIFIED → EMPIRICALLY_QUALIFIED → MIGRATED
```

Impossible transitions fail closed. `DONE` obeys the global Definition of Done.

## 8. Identity model

Stable typed IDs; never row positions or chat identity. Existing H-IDs are immutable. Session IDs never repeat. Claim takeover requires increasing fencing token. Application identity binds target/lane/channel, while packet identity additionally binds asset versions.

## 9. Evidence and freshness

External inputs are untrusted observations until validated. Evidence is claim-level, scope-aware, timestamped, freshness-aware, conflict-aware and supersedable. `UNKNOWN_AFTER_SEARCH` requires search proof. Unknown never silently becomes NO.

## 10. Security and privacy

Protect: operational authority, credentials, PII, candidate truth, H-IDs, evidence lineage and outbound authorization.

Threat families: prompt/provider poisoning, PII/secret leakage, malicious URLs/files, stale writer, replay/duplicate work, wrong-epoch evidence, authority escalation, partial cross-plane write and duplicate external action.

Mitigations: bounded claims, fencing, schema validation, public-repo guard, private candidate plane, evidence hashes, suppression, idempotency, provider-state verification and rollback/replay.

## 11. Testing architecture

Quality ladder:

L0 syntax/compile
L1 unit
L2 schema/integrity
L3 integration
L4 semantic equivalence
L5 adversarial/property/security
L6 restore/replay
L7 authority reconciliation
L8 candidate/claim safety
L9 outbound/idempotency
L10 zero-context recovery/death drill

Historical escaped bugs require permanent regression tests. `PASS`, `FAIL`, `SKIPPED`, `CANCELLED`, `NOT_RUN` stay distinct.

## 12. CI/CD

Local-first deterministic validation is primary developer feedback; GitHub Actions is an independent redundant verifier, not operational authority.

```text
LOCAL PASS → PR → REMOTE PASS → ancestry reread → merge → post-merge qualification
```

Never merge solely because CI once passed if main/authority changed materially.

## 13. Recovery model

Coordination recovery is executable: replay append-only events/claims, rebuild projections and ContextPack, reject drift, then re-read operational authority.

Operational recovery remains DB/manifest + synchronized control-plane reconciliation. Deleting chat, local checkout, graph projection or local cache must not destroy recoverable project state.

## 14. Documentation architecture

Canonical roots: `AGENTS.md`, `README.md`, `GOAL.md`, `STATE.md`, `ARCHITECTURE.md`, `LEXICON.md`, `TASKS.md`, `HANDOFF.md`.

Detailed current contracts live under `docs/architecture`, `docs/operations`, `docs/state/v2`. Historical docs remain explicitly historical/superseded.

## 15. Agent workflow

```text
READ LIVE MAIN
→ reconstruct authority + ContextPack
→ scan claims/PRs/blockers
→ acquire bounded claim
→ WORK_STARTED event
→ implement bounded scope
→ local tests + adversarial review
→ reread main/authority
→ PR + independent CI
→ merge only on current ancestry
→ post-merge qualification
→ durable evidence/handoff
→ release/supersede claim
```

## 16. Migration strategy

No big bang.

1. Coordination V2 kernel — implemented and empirically qualified.
2. Multi-niche additive schema — implemented.
3. NICHE-001 compatibility tooling — implemented; real semantic promotion blocked by unresolved authority drift where applicable.
4. Candidate Truth/Asset foundation — implemented; private human approval remains separate.
5. Application Packet Compiler — implemented.
6. Target-bound adversarial gate — must reconcile asset/current-packet SSOT before merge.
7. Response/learning engine — next product loop.
8. Second niche only after one end-to-end employment loop produces meaningful signal or a strategic source justifies earlier work.

## 17. Overengineering filter

No Kafka/Redis/Kubernetes/microservices/vector DB/distributed worker fleet without measured trigger. New abstraction must solve a demonstrated cross-niche/global responsibility. Prefer interfaces now and infrastructure later.

## 18. Current residual blockers

Architecture completion does not imply North Star readiness. Current typed blockers include:

- CRM source universe still unresolved; root NEXT is authoritative for mutable counts;
- H-0580 cross-plane semantic drift blocks hotel authority promotion until evidence/reconciliation closes it;
- candidate external assets remain subject to private/human approval state;
- target-bound application authorization is not yet production-qualified;
- outbound remains CLOSED until all independent gates and explicit authorization pass.

## 19. V2.2 Definition of Done

V2.2 architecture is accepted when:

- this document is the single canonical architecture surface;
- goal compatibility is explicit and non-destructive;
- coordination recovery/death drill remains green;
- tasks/checkpoints reflect merged W1–W5 and residual domain blockers;
- no architecture document claims operational authority;
- current open PRs are semantically classified before they can masquerade as active work;
- all remaining uncertainty is represented as BLOCKER/RISK/UNKNOWN/DEFERRED_DECISION with resolution path.

V2.2 architectural acceptance does **not** mean G-0001, CRM universe, candidate readiness or outbound are complete.
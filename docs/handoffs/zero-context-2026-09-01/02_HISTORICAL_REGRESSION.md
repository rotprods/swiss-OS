# HISTORICAL REGRESSION — FROM FIRST INTENT TO CURRENT PRODUCTION SYSTEM

## Phase 0 — Human intent

The project began with a relocation goal: leave Spain and build a future in Switzerland or Australia; willingness to start with hospitality/operational work; no university degree; no verified B2 language level; willingness to work hard and use hospitality as an entry route; and simultaneously leverage photography, video, content, digital marketing, Meta Ads, web/app development, chatbots, AI and automation to create additional employer value.

Switzerland became the dominant execution market because the user wanted a concrete system capable of finding, tracking and applying to real opportunities at scale.

## Phase 1 — Economic model

The Swiss decision was decomposed into salary/gross/net, taxes, health insurance, rent/employee housing, utilities, municipal costs, food, transport, relocation, recurring household charges and free cash flow. The mission evolved from “get any job” to “secure a truthful, viable Swiss offer and relocate sustainably.”

## Phase 2 — Job-search OS

`SWITZERLAND_JOB_OS` expanded into CV/candidate assets, job portals, URL/application tracking, employer intelligence, message/email architecture, LinkedIn/company discovery, hospitality-first execution, proactive creative/digital offers, CRM/graph/evidence architecture, Drive persistence and strict separation of research from irreversible outbound.

## Phase 3 — Hotel universe + graph

Hotels became the first enumerated vertical. The system built canonical hotels, vacancies, people, channels, housing/benefits, evidence, digital audits, scoring, completeness QA, template routing, candidate gates, run logs, decision ledgers, issues, invariants and graph projections.

Escaped defects included spill corruption, column shifts, duplicate QA states, mixed score scales, misleading completeness semantics, stale schedulers, duplicate metrics, source drift and Sheets capacity pressure. These drove DB shadowing, QA V3, Scoring V3, gates, suppression/idempotency, state transitions and SLOs.

## Phase 4 — Authority architecture

The project evolved into multiple authority planes:
- GitHub = executable contracts/code/tests/CI/public-safe state;
- Drive/Sheets/DB = hotel/CRM authority/control plane;
- Library = cold-recovery artifacts;
- meta graph != operational hotel graph;
- open PR/canary/staging != authority.

Protocols emerged: MEP, NPP, WOP, CUP, DSA, MDM, SSR, PAB, PRG and CSP.

## Phase 5 — Canonical authority evolution

Historical checkpoints included 500 canonical + 50 strict parity, H01 production hardening, CP-0650 completion and CP-0750 activation. The durable authority later stabilized at entity epoch E4.

At this handoff:
- 690 physical/canonical hotel rows;
- H-0691 unallocated;
- zero new H-ID allocations from the current preauthority review stream;
- CRM universe still incomplete.

## Phase 6 — Coherent current source

A coherent HotellerieSuisse source universe was recovered:
- snapshot `HS-MEMBER-DE-33339392661`
- 2061 records / 172 pages
- 658 terminal source mappings
- 656 unique canonical targets
- 1403 `RECONCILE_REQUIRED`
- 34 reverse authority/source gaps

Historical snapshots/caches remain discovery aids only.

## Phase 7 — Current-source entity resolution

The system entered deterministic review of unresolved low-similarity historical tails. By B06:
- 1438/1438 ECV candidates accounted;
- high/mid/lower review bands completed;
- RAGR evidence classified;
- `<0.35` tail became the dominant unresolved body;
- 60 zero-exact-city records reviewed in current-source order;
- 174 cumulative `NEW_CANONICAL_PREAUTH`;
- zero H-ID allocations/reservations.

Permanent lessons:
- similarity is rank-only;
- locality normalization matters;
- generic hotel names cannot autobind;
- accommodation type/granularity matters;
- sibling/shared-reception/operator relationships are not aliases by default;
- EGR relationships preserve structure without canonical collapse.

## Phase 8 — Market enrichment + vacancy-first applications

A 2061-record market-enrichment run produced:
- 1705 official sites;
- 611 careers routes;
- 436 hotels with current opening routes;
- 121 spontaneous signals;
- 9 explicit no-opening states.

A 44-shard Vacancy Detail process rechecked all 436 opening-route hotels.

Escaped failures then became regression protection:
- self-referential aggregate hash bug;
- one route-level security rejection destroying a whole shard;
- lexical vs numeric shard ordering;
- GitHub artifact 503 transport instability;
- duplicate vacancy URLs multiplied across properties;
- restaurant/navigation labels classified as jobs;
- future/expired structured JobPosting conflicts;
- multi-property shared-vacancy ownership ambiguity.

## Phase 9 — Adversarial application readiness

AAG-3.0 added 100 adversarial questions, 19 quality dimensions, 11 non-compensable gates, employer-risk analysis, 6-stakeholder unanimity and fail-closed readiness states.

AAG-3.1 added five vacancy-provenance gates:
1. semantic validity;
2. temporal validity;
3. employer scope;
4. mandatory requirements extracted;
5. application route verified.

Total = 16/16 hard gates. No soft score can compensate a false/unknown hard gate.

## Phase 10 — Context survival

CSP-1.0 made context loss a designed-for condition:
- chat/model context is disposable cache;
- survival paths are content-addressed;
- ancestry floor and Git blob OIDs are pinned;
- active claims/fencing are persisted;
- exact domain NEXT is pinned;
- zero-context bootstrap is mandatory.

PR #401 added a causal historical regression and escaped-bug ledger.

## Current principle

Never “continue where the chat left off.” Always verify fresh main, CSP, authority epoch, active claims, external authority and durable NEXT before execution.

# MULTI-NICHE SWISS EMPLOYMENT OS — V1

Status: DESIGN LOCK / IMPLEMENTATION PLAN
Protocol: CGEV2 + MEP/COLETTE
North Star: G-0001 remains unchanged.

## Decision

Hotels are NICHE-001, not the system boundary. Existing hotel authority E4/690 remains frozen and authoritative while the core is generalized. No H-ID is allocated by this architecture wave. OUTBOUND remains CLOSED.

The target architecture is one horizontal employment-acquisition core plus N niche adapters.

## Core domains

1. Candidate Truth OS
2. Candidate Asset Compiler
3. Market Universe Engine
4. Niche Registry / Adapter Runtime
5. Source Registry + Snapshot Capture
6. Organization / Location / Brand / Group Graph
7. Entity Resolution
8. Vacancy / Role Family Engine
9. People / Recruiter Engine
10. Channel / Policy Engine
11. Evidence / Search Proof / Freshness Engine
12. Benefits / Housing Engine
13. Fit / Opportunity Ranking
14. Application Packet Compiler
15. Email Identity + Messaging Engine
16. Outreach / Portal Execution Gate
17. Response / Outcome Ingestion
18. Interview Engine
19. Offer + Financial Viability Engine
20. Relocation Engine
21. Learning / Experimentation Engine
22. QA / Governance / Observability / Recovery

## Generic data model target

HOTELS_V2 and HOTEL_GROUPS_V2 become NICHE-001 projections/adapters over generic concepts, not immediate destructive migrations.

Core target entities:
- NICHES
- NICHE_ADAPTERS
- ORGANIZATIONS
- ORGANIZATION_LOCATIONS
- BRANDS
- GROUPS
- SOURCES
- SOURCE_SNAPSHOTS
- SOURCE_RECORDS
- PEOPLE
- CHANNELS
- VACANCIES
- ROLE_FAMILIES
- EVIDENCE
- SEARCH_PROOF
- BENEFITS
- HOUSING
- FIT_SCORES
- CANDIDATE_CANON
- CLAIMS
- ASSETS
- APPLICATIONS
- OUTREACH_ACTIONS
- RESPONSES
- INTERVIEWS
- OFFERS
- FINANCIAL_MODELS
- RELOCATION_TASKS
- EXPERIMENTS
- OUTCOME_METRICS

## Niche adapter contract

Every niche declares:
- niche_id and taxonomy
- source registry and source-scope rules
- discovery/capture adapters
- normalization rules
- entity-resolution rules
- organization/group semantics
- role families
- relevant benefits/housing semantics
- language/geography/seasonality profile
- recruiting channels and portal policy
- scoring weights
- candidate-lane compatibility
- enrichment dimensions
- application strategy
- QA/invariants/SLO extensions

NICHE-001 = HOTELS. Existing hotel-specific state is preserved and wrapped first.

## Candidate Asset OS

Required versioned outputs:
- CV_MASTER
- CV_ENTRY
- CV_HYBRID
- CV_CREATIVE
- ATS QA report
- truthful claims manifest
- language-safe wording
- portfolio/case-study manifest where lane-relevant
- asset hashes + versions

No V1 asset is silently promoted. Every rendered CV must trace claims to Candidate Canon / Claims Ledger.

## Email Identity OS

Required:
- professional sender/display-name contract
- HTML signature
- plain-text fallback
- mobile-safe signature
- contact/privacy policy
- ENTRY / HYBRID / CREATIVE / PORTAL / recruiter / spontaneous / follow-up schemas
- render tests for Gmail desktop/mobile, Apple Mail, Outlook, dark mode, images-blocked and plain text

Installing/changing the real Gmail signature is an external account mutation and requires an explicit execution step supported by available tooling; a generated HTML artifact alone is not installation.

## Application packet compiler

Input:
organization + vacancy + niche + canton + language + lane + candidate evidence + recruiter/channel + employer context

Output:
selected CV + message schema + evidence refs + claims refs + asset versions + channel policy + reason vector + QA result + idempotency key.

## Response-learning loop

APPLICATION -> RESPONSE -> typed OUTCOME -> reason extraction -> niche/lane/CV/template/channel metrics -> experiment -> strategy update.

Never infer a rejection reason that the employer did not state. Keep observed reason separate from hypothesis.

## Goal tree refactor proposal

G-0001 North Star remains stable.

- G-0100 Candidate Truth
- G-0200 Candidate Assets
- G-0300 Generic Market Universe Platform
- G-0400 Niche Adapter Coverage
- G-0500 NICHE-001 Hotels / legacy compatibility
- G-0600 Opportunity Intelligence
- G-0700 Acquisition Engine
- G-0800 Outbound Readiness
- G-0900 Response / Interview
- G-1000 Offer
- G-1100 Financial Viability
- G-1200 Relocation

Do not renumber/remove legacy durable goal IDs in-place until a migration/alias decision is approved. Implement this initially as a target graph and compatibility map.

## Verifiable checkpoints

- CP-MN-000 Architecture contract PASS
- CP-MN-010 Generic schemas + migration plan PASS
- CP-MN-020 NICHE-001 compatibility adapter PASS
- CP-CA-010 Candidate Canon completeness by lane PASS
- CP-CA-020 CV compiler + CV v2 assets PASS
- CP-EM-010 Email identity/signature artifacts PASS
- CP-EM-020 Messaging/template compiler PASS
- CP-AP-010 Application packet compiler PASS
- CP-RS-010 Response ingestion/outcome taxonomy PASS
- CP-MN-030 NICHE-002 adapter PASS
- CP-MN-040 >=5 adapters PASS
- CP-ACQ-010 controlled acquisition canary PASS
- CP-ACQ-020 first verified positive employer response
- CP-ACQ-030 first interview
- CP-OFFER-010 first verified offer
- CP-OFFER-020 financial viability PASS
- CP-NS-100 accepted offer + relocation-ready = North Star complete

Existing CP-0750 remains a NICHE-001 scale checkpoint and is not deleted.

## Implementation waves

### W0 — Authority freeze + architecture ledger
DoD: E4/690 unchanged; H-0691 unallocated; outbound closed; architecture decision persisted; current P0s preserved.

### W1 — Generic schema overlay
Create additive generic schemas and compatibility views/mappings. No destructive hotel migration.
Tests: schema contracts, PK/FK, round-trip mapping, restore/replay, no authority delta.

### W2 — NICHE-001 adapter
Wrap hotels as first adapter. Prove generic core can reproduce hotel identity/source/entity-resolution semantics without count drift.
Tests: 690/690 equivalence, source mapping equivalence, alias semantics, QA/SLO parity.

### W3 — Candidate Truth + Asset Compiler
Reconcile Candidate Canon and Claims Ledger; define lane-specific required/optional facts; compile CV_MASTER/ENTRY/HYBRID/CREATIVE v2.
Tests: claim provenance, ATS, no invented qualification/CEFR, lane gate matrix, PDF/text extraction QA.

### W4 — Email Identity + Messaging
Design signature and message schemas; create HTML/plain-text artifacts and rendering QA. Install in real email only through supported account mutation after explicit authorization where required.
Tests: HTML validity, no remote tracking, mobile/dark-mode/fallback, link/contact correctness.

### W5 — Application Packet Compiler
Deterministic vacancy/company/lane packet selection with evidence, claims, assets, channel policy and idempotency.
Tests: golden fixtures, unsupported-claim rejection, stale evidence rejection, portal-only suppression, duplicate action prevention.

### W6 — Response / Outcome Engine
Ingest historical Swiss replies and future responses into typed states.
Tests: rejection/no-vacancy/ack/interview/offer classifiers; observed vs inferred reason separation; thread/action linkage.

### W7 — NICHE-002 canary
Select second niche based on expected employment yield and source quality, not novelty. Implement adapter without modifying core semantics.
DoD: source snapshot -> CRM coverage -> entity resolution -> vacancy/routing -> QA through generic interfaces.

### W8 — Multi-niche scale
Add adapters incrementally. Every new niche must pass adapter contract and source-scope QA before scale.

### W9 — Controlled acquisition
Only after independent market/candidate/claims/channel/suppression/idempotency/user-authorization gates pass. Start bounded canary, ingest outcomes, compare lane/template/channel performance.

### W10 — Offer/finance/relocation
Offer verification -> sourced Swiss financial model -> acceptability -> relocation execution.

## QA / gates

Every wave runs CGEV2/MEP COLETTE plus:
- authority/ancestry reconciliation
- schema and graph impact
- provenance
- PK/FK/integrity
- duplicate/missing-ID scan
- semantic equivalence
- freshness/TTL
- invariants/SLOs
- scheduler anti-join
- suppression/idempotency
- candidate truth gate
- outbound gate
- restore/replay when authority changes
- durable handoff

P0 => fail closed.

## PR strategy

Small bounded PRs:
1. architecture/ADR only
2. generic schemas/contracts
3. hotel adapter compatibility
4. candidate truth/compiler
5. CV assets pipeline
6. email identity/signature pipeline
7. application compiler
8. response engine
9. NICHE-002 adapter
10. acquisition canary/metrics

No mega-PR. Main must remain green after each merge.

## Immediate next action

Do not resume blind hotel scaling first. Execute W0 then W1 while preserving the existing CP-0750 hotel frontier. Current technical debt/P0 remediation remains a prerequisite for authority promotion, but read-only/additive architecture work may proceed safely.

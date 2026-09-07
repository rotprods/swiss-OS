# SWISS EMPLOYMENT OS — IMPLEMENTATION BACKLOG

Date: 2026-09-07
Status: RESEARCH-QUALIFIED BACKLOG / NO MATERIAL CLAIM
Outbound: CLOSED

## Strategic order

The system now has an additive generic multi-niche core (W1 merged) but lacks national source coverage and a production vacancy schema. Work should proceed as independent bounded PRs after current material-writer/fencing conflicts are cleared.

## Epic A — Market Source Registry

A1. Ratify `SourceSurface` schema.
A2. Create registry seed from SOURCE_REGISTRY_CANDIDATES_V3.
A3. For each source record: ownership, scope, languages, niche coverage, canton coverage, access method, robots/ToS constraints, pagination, freshness, dedup policy, primary-vs-discovery semantics.
A4. Add BLOCKED/UNOBSERVABLE states.
A5. Add timestamped source-health receipts.
A6. Coverage metric: qualified / declared sources.

DoD: >=20 high-value source surfaces qualified/blocked with explicit policy and zero silent omissions.

## Epic B — Niche Registry

B1. Ratify 32 macro niches or split/merge with migration map.
B2. Stabilize role-family identifiers.
B3. Add candidate-lane compatibility.
B4. Add regulated-role flag and eligibility-evidence contract.
B5. Add source families by niche.
B6. Add language/geography/seasonality profile hooks.

DoD: every niche can validate against one NicheContract version; NICHE-001 compatibility unaffected.

## Epic C — Vacancy V3

C1. Production JSON/SQLite schema from VACANCY_V3 draft.
C2. SourceRecord -> normalized vacancy candidate mapper.
C3. Canonical vacancy identity fingerprint.
C4. Multi-source dedup candidate engine.
C5. Explicit status reducer and TTL/freshness.
C6. Employer-direct verification state.
C7. Raw-text lineage preservation.
C8. Golden fixtures from DE/FR/IT regions and >=5 niches.

DoD: same vacancy found on 3 boards produces one canonical candidate with three source records; expiry/fill events are reproducible.

## Epic D — Geography / Canton Runtime

D1. Canonical registry of 26 cantons.
D2. municipality/locality normalization.
D3. bilingual/multilingual locality aliases.
D4. work-location vs residence/commute separation.
D5. canton/niche vacancy-density projection.
D6. commute/housing edges only after evidence.

DoD: no city-string equality as sole geographic identity authority.

## Epic E — Language Intelligence

E1. LanguageRequirement assertion schema.
E2. mandatory/preferred/working/advantage semantics.
E3. CEFR explicit-only policy.
E4. ad-language separate from requirement-language.
E5. candidate-gap matcher using Candidate Canon.
E6. language opportunity matrix per niche/canton.

DoD: UNKNOWN, NOT_STATED and explicit no-requirement states remain distinguishable and queryable.

## Epic F — Salary Intelligence

F1. SalaryAssertion schema.
F2. disclosed salary parser.
F3. derived-rule applicability model.
F4. market-estimate ingestion/statistics model.
F5. workload normalization.
F6. 13th salary semantics.
F7. gross/net discipline.
F8. opportunity financial viability model.

DoD: no market estimate is ever rendered as employer-offered compensation.

## Epic G — Employer CRM

G1. generic Organization/Location/Brand/Group identity model.
G2. employer career-surface registry.
G3. recruiter/person/channel entities.
G4. source record links.
G5. duplicate employer review queue.
G6. preserve hotel H-ID compatibility adapter.

DoD: employer identity survives name/brand/location variations and source duplication with provenance.

## Epic H — Candidate Asset Compiler

H1. Re-read private Candidate Canon at current horizon.
H2. produce lane completeness matrix.
H3. verify claims ledger.
H4. compile/approve CV_MASTER_V2.
H5. revalidate ENTRY/HYBRID V2 against current links/dates.
H6. compile CV_CREATIVE_V2 only from evidence.
H7. add role-family CV projection policy.
H8. ATS/text extraction/link QA.
H9. recruiter 10-second gauntlet.

DoD: every rendered claim has approved lineage; no one-CV-fits-all default.

## Epic I — Portfolio Evidence System

I1. inventory public-safe work artifacts.
I2. map responsibility/evidence per project.
I3. create case-study registry.
I4. mark confidential/non-public cases.
I5. compile Creative/Marketing/AI-Tech/Hybrid projections.
I6. validate live links and mobile rendering.

DoD: every portfolio claim resolves to evidence and every externally named client/project has publication permission or public status.

## Epic J — Identity / Messaging

J1. reconcile salvage PR #425 with main.
J2. verify current contact/LinkedIn/portfolio routes privately.
J3. HTML + plaintext render QA.
J4. ENTRY/HYBRID/CREATIVE/PORTAL message schemas.
J5. role/vacancy-specific first-scan content.
J6. no tracking/PII leakage.

DoD: identity is consistent across CV, email, portfolio and application route.

## Epic K — Application Packet Compiler

K1. requirement extractor.
K2. candidate truth matcher.
K3. gap detector.
K4. lane selector.
K5. CV/portfolio selector.
K6. message compiler.
K7. stale-fact rejection.
K8. unsupported-claim rejection.
K9. channel policy.
K10. idempotency key and no-send receipt.

DoD: identical inputs compile deterministically; invalid/stale/private data fails closed.

## Epic L — Response / Interview / Offer

L1. replay existing 10-application learning set.
L2. response taxonomy ingestion.
L3. observed reason vs hypothesis separation.
L4. interview preparation pack.
L5. question/objection ledger.
L6. offer verification.
L7. contract/housing/salary/runway model.

DoD: employer outcomes update strategy without inventing causal reasons.

## Epic M — Relocation

M1. current EU/EFTA administrative route by canton.
M2. registration/insurance checklist.
M3. housing contract verification.
M4. travel/start-date dependency graph.
M5. runway/first-paycheck stress test.
M6. Spanish fiscal/autónomo transition as separate professional-review track.

DoD: relocation is blocked until accepted verified offer + housing + finance + start date + admin plan.

## Epic N — Coverage and Observability

N1. source coverage dashboard.
N2. niche/canton/language/salary missingness.
N3. freshness SLO.
N4. dedup quality metrics.
N5. adapter failure rate.
N6. employer-direct verification rate.
N7. opportunity funnel metrics only after outbound opens.

DoD: system reports what it does NOT know; never labels a partial crawl as Switzerland-complete.

## PR sequence after writer admission

1. `feat/source-surface-contract`
2. `feat/niche-registry-v1`
3. `feat/vacancy-v3-schema`
4. `feat/geography-language-assertions`
5. `feat/salary-assertions`
6. `feat/job-room-adapter-canary`
7. `feat/cross-source-dedup`
8. `feat/employer-direct-verifier`
9. `feat/cos-employment-projection`
10. `feat/candidate-asset-compiler`
11. `feat/portfolio-case-registry`
12. `feat/application-packet-compiler`

Each PR must preserve `OUTBOUND=CLOSED` unless a later explicit outbound-readiness gate is separately approved.

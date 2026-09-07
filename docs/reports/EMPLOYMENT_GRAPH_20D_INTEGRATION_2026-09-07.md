# EMPLOYMENT DOMAIN × COS 20D INTEGRATION — 2026-09-07

Mode: RESEARCH_ONLY / NO AUTHORITY EFFECT

## Boundary

The existing COS V2 project-memory graph is a coordination/knowledge projection. Operational labour-market entities remain in the domain authority plane. This document defines shared IDs and projections; it does not make project-memory JSON the vacancy CRM source of truth.

## Domain authority layers

1. SourceSurface / SourceSnapshot / SourceRecord — observed external evidence.
2. CanonicalEmployer / EmployerLocation / CanonicalVacancy — normalized operational entities.
3. RequirementAssertion / SalaryAssertion / LanguageRequirement / HousingAssertion — fact/assertion layer with provenance and validity.
4. Opportunity — candidate-relative evaluation; never intrinsic vacancy truth.
5. Application / Response / Interview / Offer — external-action/outcome ledger.
6. COS Graph projections — execution, dependency, knowledge, evidence, decision, state and recovery views.

## COS projection mapping

| COS layer | Employment projection |
|---|---|
| L0 Visual | canton × niche heatmaps, opportunity funnels, source-coverage maps; generated from authoritative IDs |
| L1 Execution | G-0001 -> market checkpoints -> adapters -> evidence -> asset gates -> application -> offer -> relocation |
| L2 State | source/vacancy/opportunity/application/interview/offer state machines |
| L3 Dependency | source freshness, candidate asset, language, housing and finance blockers |
| L4 Call | adapter/parser/normalizer/dedup/scoring/compiler call graph after implementation |
| L5 Control | fail-closed rules for stale facts, unsupported claims, duplicate sends, authority promotion |
| L6 DataFlow | source -> snapshot -> record -> normalized assertion -> canonical vacancy -> opportunity -> application packet |
| L7 Compute | bounded batch ingestion, dedup candidate generation, deterministic reducers; no distributed compute assumed |
| L8 Knowledge | labour-market facts, role requirements, sector rules, candidate evidence and outcomes |
| L9 Semantic | canonical vocabulary for niche, role, requirement, salary, language, vacancy status and outcomes |
| L10 Similarity | dedup/retrieval triage only; never employer/vacancy identity authority |
| L11 GraphRAG | queries over employer/vacancy/requirement/evidence/opportunity graph with provenance |
| L12 Memory | historical vacancies/outcomes/market trends with invalidation and temporal lineage |
| L13 Agent | source researcher, normalizer, verifier, asset compiler, recruiter-reply analyst, interview coach |
| L14 Tool | source access, browser/search, Git/DB/Sheets, email/portal and document renderer capabilities |
| L15 Workflow | discovery -> normalize -> verify -> score -> compile -> QA -> authorization -> send -> outcome -> learn |
| L16 Network | activate only for commute/transport/provider-network semantics after a domain-specific contract; not automatically required |
| L17 Additional | RESERVED until a measurable domain need exists |
| L18 Additional | RESERVED until a measurable domain need exists |
| L19 Additional | RESERVED until a measurable domain need exists |

## New domain IDs

Suggested ID spaces (draft; production allocation requires schema approval):
- SRC-xxxxx SourceSurface
- SNAP-xxxxx SourceSnapshot
- SR-xxxxx SourceRecord
- ORG-xxxxx Employer
- LOC-xxxxx EmployerLocation
- VAC-xxxxx CanonicalVacancy
- OCC-xxxxx OccupationFamily / Role
- LANGREQ-xxxxx LanguageRequirement
- SAL-xxxxx SalaryAssertion
- BEN-xxxxx BenefitAssertion
- HOUSE-xxxxx HousingAssertion
- OPP-xxxxx CandidateOpportunity

Do not reuse legacy H-IDs for non-hotel employers. H-IDs remain NICHE-001 compatibility identity until a separately reviewed migration contract says otherwise.

## Hyperrelations

Use first-class multi-party relations when a fact depends simultaneously on vacancy + employer + location + collective agreement + workload + time horizon. Example: salary-rule applicability must not be flattened into `Vacancy -> Salary` if the rule only applies under specific role/category/workload/season conditions.

## Required graph queries for acceptance

Q1. All LIVE_VERIFIED vacancies by canton and niche with source freshness.
Q2. Vacancies where English is mandatory/working and no national language is explicitly mandatory, preserving NOT_STATED.
Q3. Entry vacancies offering confirmed/possible housing by canton and expected start window.
Q4. Vacancies whose salary is DISCLOSED vs DERIVED_RULE vs MARKET_ESTIMATE.
Q5. Source surfaces with stale/blocked coverage and the affected niche/canton frontier.
Q6. Duplicate source records mapped to one canonical vacancy.
Q7. Candidate opportunities blocked only by language vs experience vs asset vs unknown requirement.
Q8. Applications whose source vacancy expired after submission.
Q9. Rejection outcomes grouped by observed reason only; hypotheses separately queryable.
Q10. Offer candidates that pass contract + housing + runway gates.

## Graph invariants

- SourceRecord != CanonicalVacancy.
- Vacancy != Opportunity.
- Opportunity score != hiring probability.
- Market estimate != employer salary.
- NOT_STATED != NOT_REQUIRED.
- Similarity != identity.
- Projection != authority.
- One external action has one idempotency key and receipt/ambiguous state.
- Historical facts retain validity interval and provenance.
- private Candidate Canon values do not enter the public graph projection.

## Acceptance gauntlet

1. schema validation;
2. referential integrity;
3. duplicate ID/canonical key tests;
4. temporal/freshness tests;
5. provenance completeness;
6. source replay/rebuild equality;
7. cross-source duplicate fixtures;
8. UNKNOWN/NOT_STATED adversarial cases;
9. stale vacancy suppression;
10. private-candidate leakage scan;
11. golden GraphRAG queries Q1-Q10;
12. cold-agent recovery with exact source horizon.

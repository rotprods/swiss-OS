# SWISS EMPLOYMENT MARKET — WAVE 001

Date: 2026-09-07
Mode: RESEARCH_ONLY / NON_AUTHORITATIVE / OUTBOUND_CLOSED
Base main observed: 1072d5cfb33beee3f2afcd31a59ba00c514df170

## Objective

Advance G-0300 Generic Market Universe Platform and G-0400 Niche Adapter Coverage without modifying E4 hotel authority, Candidate Canon, H-IDs, applications, Gmail or outbound state.

This packet turns the existing multi-niche design into an evidence-backed national labour-market discovery plan. It is deliberately additive and research-only because token16 material writers are active on separate scopes and main remains unprotected at platform level (#441).

## Live repo facts recovered

- W1 additive multi-niche schema/contracts merged in PR #407.
- Existing generic core includes NicheContract and NICHE-001 Hotels.
- W2 hotel compatibility is tracked in issue #408 and requires 690/690 semantic equivalence before authority migration.
- Candidate Asset OS V2 already defines CV_MASTER_V2, CV_ENTRY_V2, CV_HYBRID_V2 and CV_CREATIVE_V2 with claim provenance/ATS/lane gates.
- Current main reports OUTBOUND=CLOSED / send_allowed=0.
- Open PR #425 is a salvage/rebase candidate for professional email signature V2; do not treat it as main authority.

## Market-source evidence sampled 2026-09-07

### Tier A — public/official or primary employment infrastructure

1. Job-Room / arbeit.swiss (SECO public employment service)
   - official Swiss public employment surface;
   - Job-Room carries vacancies and 2026 job-registration workflows;
   - source class: OFFICIAL_PUBLIC_EMPLOYMENT.

2. Employer career pages
   - primary vacancy truth when current and directly attributable;
   - source class: EMPLOYER_FIRST_PARTY.

3. Cantonal/federal/public institution career pages
   - public administration, hospitals, universities, transport/public utilities;
   - source class: PUBLIC_EMPLOYER_FIRST_PARTY.

### Tier B — large Swiss aggregators/boards

4. jobs.ch
   - broad German/English Swiss job market surface;
   - exposes location, workload, contract type and freshness metadata on results;
   - source class: NATIONAL_JOB_BOARD.

5. jobup.ch
   - major French-speaking Switzerland surface;
   - observed result page on 2026-09-07 reported 38,938 jobs;
   - source class: REGIONAL_NATIONAL_JOB_BOARD.

6. JobScout24 Switzerland
   - broad multi-sector board; include after access/duplication policy review.

### Tier C — specialist / newcomer / sector boards

7. jobswitzerland.ch
   - cross-canton, multilingual/newcomer-oriented board; links applications back to employer sources;
   - source class: AGGREGATOR_DISCOVERY.

8. Hospitality sector boards/directories
   - existing NICHE-001 estate remains reusable; source-specific policy required.

9. Staffing / recruitment agencies
   - Adecco, Randstad, Manpower and specialist agencies are candidate source families, not yet qualified adapters.

10. Trade/professional associations
   - recommended by EURES Switzerland as a job-search surface in addition to Job-Room/private agencies;
   - source class: ASSOCIATION_DIRECTORY / ASSOCIATION_CAREERS.

## Coverage principle

The system MUST NOT claim `ALL_SWISS_VACANCIES_COMPLETE=true` merely because many records exist. Completeness is defined only relative to an explicit source registry and horizon:

`coverage = observed eligible source surfaces / declared source surfaces`

Required dimensions:
- source coverage;
- canton coverage;
- niche coverage;
- role-family coverage;
- language-requirement coverage;
- salary-field coverage;
- freshness coverage;
- employer-direct verification coverage;
- deduplication coverage.

Any unreachable/private/blocked source remains visible as BLOCKED/UNOBSERVABLE and reduces completeness confidence.

## Priority niche waves

Wave A — immediate accessibility / relocation yield
- NICHE-001 HOTELS (existing)
- CLEANING_FACILITIES
- GASTRONOMY
- LOGISTICS_WAREHOUSE
- MANUFACTURING_PRODUCTION
- RETAIL
- CONSTRUCTION_TRADES
- TRANSPORT_DELIVERY
- AGRICULTURE_FOOD_PRODUCTION

Wave B — transferable service/operations
- CUSTOMER_SUPPORT
- SALES
- ADMINISTRATION
- EVENTS_LEISURE
- AUTOMOTIVE
- SECURITY
- REAL_ESTATE_FACILITIES

Wave C — candidate differentiated lanes
- MEDIA_AUDIOVISUAL
- PHOTOGRAPHY_CONTENT
- MARKETING_ADVERTISING
- DESIGN_BRANDING
- SOFTWARE_IT
- AI_DATA_AUTOMATION
- PRODUCT_WEB

Wave D — qualification-regulated / specialist intelligence
- HEALTHCARE_CARE
- ENGINEERING
- FINANCE_INSURANCE
- PHARMA_BIOTECH
- EDUCATION_RESEARCH
- ENERGY_UTILITIES
- PUBLIC_SECTOR
- LUXURY_WATCHMAKING
- AVIATION_RAIL

Regulated niches are indexed even if candidate eligibility is currently low; market coverage and candidate fit are separate concepts.

## Geography / language model

Every normalized vacancy should connect to:
- canton;
- municipality/locality;
- work location vs remote/hybrid;
- language requirement assertions (DE/FR/IT/EN/other);
- CEFR only when explicitly stated or evidence supports a derived requirement;
- mandatory/preferred/working-language semantics.

Never infer a formal CEFR level merely from advertisement language.

Switzerland is officially quadrilingual; regional labour-market language distribution must be represented rather than flattening Switzerland into a single German-language market.

## Salary model

Store three non-interchangeable classes:

1. DISCLOSED — explicit vacancy/employer salary.
2. DERIVED_RULE — collective agreement/statutory/public pay scale with applicability evidence.
3. MARKET_ESTIMATE — market observation/statistical estimate, never presented as employer offer.

Required fields include currency, period, gross/net flag, workload normalization, 13th salary handling when known, source, observed_at, confidence and applicability constraints.

## Vacancy lifecycle

DISCOVERED -> NORMALIZED -> DEDUP_CANDIDATE -> CANONICAL_REVIEWED -> LIVE_VERIFIED -> ELIGIBILITY_SCORED -> PACKET_ELIGIBLE -> EXPIRED/FILLED/WITHDRAWN

Research may advance only through LIVE_VERIFIED. PACKET_ELIGIBLE additionally requires Candidate Truth, asset, freshness, channel and outbound gates.

## Graph integration

Domain nodes remain operational-domain entities and project-memory COS stays a projection/coordination plane.

Core domain nodes to add/extend:
- Niche
- OccupationFamily
- CanonicalRole
- Employer
- EmployerLocation
- Vacancy
- SalaryObservation
- LanguageRequirement
- Benefit
- HousingOption
- SourceSurface
- SourceSnapshot
- SourceRecord
- Opportunity

Edges:
- VACANCY_IN_NICHE
- INSTANCE_OF_ROLE
- POSTED_BY
- LOCATED_IN
- REQUIRES_LANGUAGE
- REQUIRES_SKILL
- OFFERS_COMPENSATION
- MAY_INCLUDE_HOUSING
- OBSERVED_IN
- DERIVED_FROM
- DUPLICATE_OF_CANDIDATE
- VERIFIED_BY
- ELIGIBLE_FOR_CANDIDATE

COS projections consume these IDs; they do not become independent authority.

## Candidate / asset workstream

Keep Candidate Canon private. Public repo stores only contracts, hashes/status and public-safe receipts.

Asset target before outbound:
- CV_MASTER_V2
- CV_ENTRY_V2
- CV_HYBRID_V2
- CV_CREATIVE_V2
- role-family compilation policy
- portfolio master evidence index
- creative/marketing/AI-tech/hybrid portfolio projections
- professional email identity/signature
- application-message compiler
- recruiter 10-second QA
- factual/ATS/link/render QA

Current known state: ENTRY/HYBRID approved assets exist in private control-plane evidence; CREATIVE remains a material next gate; signature V2 has an open salvage PR and must be reconciled before authority.

## Immediate implementation frontier

P0 research/definition:
1. qualify SOURCE_REGISTRY_V3 candidate sources;
2. freeze NICHE_TAXONOMY_V1 IDs before adapter coding;
3. ratify VACANCY_V3 normalization schema;
4. add salary/language/geography contracts;
5. define source-specific access/ToS/pagination/freshness policy;
6. define coverage metrics and completeness vocabulary;
7. build adapter backlog by expected yield × source quality × implementation cost.

P1 code after safe material-writer admission:
1. extend NicheContract with geography/language/seasonality/source-policy hooks without breaking NICHE-001;
2. implement SourceSurface/SourceSnapshot normalization;
3. implement vacancy canonical identity/dedup primitives;
4. implement freshness/TTL reducer;
5. implement salary/language assertion types;
6. add Job-Room adapter canary;
7. add jobs.ch/jobup discovery adapters where access policy permits;
8. add employer-direct verifier;
9. project to COS Graph V2;
10. run cross-source duplicate gauntlet.

## Definition of Done for Market Foundation

- declared source registry exists with tier/status/access policy;
- >= 20 high-value source surfaces qualified or explicitly blocked;
- 26 cantons represented in geography registry;
- >= 30 macro niches mapped to role families;
- VACANCY_V3 schema validated with fixtures from at least 5 niches and 3 language regions;
- salary and language assertions preserve UNKNOWN vs NOT_REQUIRED;
- duplicate source records cannot create duplicate canonical vacancies silently;
- freshness/expiry is explicit;
- source coverage metrics are reproducible;
- no hotel E4 authority drift;
- no private Candidate Canon leakage;
- OUTBOUND remains CLOSED.

## Sources sampled

- https://www.job-room.ch/
- https://www.arbeit.swiss/en/jobseekers/eures-professional-mobility-in-the-euefta
- https://www.arbeit.swiss/en/employers/job-registration-requirement
- https://www.jobs.ch/en/new-vacancies/
- https://www.jobup.ch/en/jobs/
- https://jobsswitzerland.ch/en/about
- https://www.aboutswitzerland.eda.admin.ch/en/multilingualism

No source count in this research packet is promoted to durable completeness authority without a timestamped capture/adapter receipt.
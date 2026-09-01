# LOCAL-FIRST EXECUTION MATRIX V1

Status: implementation contract
Principle: Local execution is primary for deterministic validation; GitHub Actions is redundant remote verification, not the sole gate.

## 1. Local CI parity

Canonical command:

```bash
PYTHONPATH=src bash scripts/local_ci.sh
```

Must execute the same deterministic checks as `.github/workflows/repo-guard.yml` plus local compile checks. A local PASS is necessary but does not by itself create operational authority.

## 2. Action classes

### A. Repository / code
- bootstrap exact main ancestry
- create bounded branch
- run secret/public-boundary guard
- run stable-contract drift guard
- run coordination/CSP guards
- run context survival guard
- compile Python
- unit tests
- integration tests
- property/negative tests where invariants justify them
- dependency audit
- dead-code/import audit
- format/lint/type checks when configured
- inspect diff
- anti-overengineering review
- produce local receipt
- commit in bounded units
- open PR
- verify remote CI as independent redundancy
- merge only after gates pass
- re-run local CI on merged main

### B. SQLite / schema / data
- initialize ephemeral DB from schema
- apply additive migrations
- PRAGMA integrity_check
- PRAGMA foreign_key_check
- schema object diff
- row-count reconciliation
- PK uniqueness scan
- missing-ID scan
- alias/supersession semantic scan
- domain/entity duplicate scan
- source-record coverage scan
- restore/backup logical equivalence
- replay migration from clean parent
- rollback test
- semantic fingerprint DB vs mirror export
- migration idempotence (apply twice safely where contract allows)
- canary fixtures for invalid FK/state/check constraints
- no authority promotion from local-only DB

### C. Multi-niche core
- validate NicheContract
- validate NICHE-NNN uniqueness
- seed NICHE-001 Hotels
- generate organization projection from legacy hotels
- create compatibility bridge
- prove 690/690 identity equivalence before hotel migration
- compare names/cities/cantons/domains/state/source refs
- prove no duplicate organizations across niches
- prove cross-niche organizations support multiple relations without duplicate identity
- source-scope classification tests
- adapter pause/resume test
- NICHE-002 canary before adding generic hooks

### D. Candidate Truth / Claims
- reconstruct Candidate Canon from durable authority
- classify each field VERIFIED/UNKNOWN/CONFLICT
- reconcile phone/email/LinkedIn/portfolio/languages/availability/equipment
- prohibit unsupported CEFR/degree/title/metrics
- build Claims Ledger with source/evidence/version
- mark externally allowed vs prohibited claims
- lane-specific required/optional matrix
- candidate truth QA

### E. CV / asset pipeline
- create CV_MASTER_V2 content model
- compile CV_ENTRY_V2
- compile CV_HYBRID_V2
- compile CV_CREATIVE_V2
- create PORTAL-compatible variant if needed
- deterministic asset manifest/version/hash
- render PDF
- extract PDF text
- compare critical facts against intended source
- ATS hierarchy QA
- link QA
- page-count QA
- metadata QA
- language/grammar QA
- role-specific top-third QA
- visual QA
- approval state per lane
- never silently reuse deprecated V1 assets

### F. Email identity / signature
- resolve approved sender identity from Candidate Canon
- design professional HTML signature
- plain-text fallback
- no JS/tracking pixels/external-font dependency
- mobile-safe table/CSS layout
- dark-mode degradation test
- images-disabled test
- Gmail/Apple Mail/Outlook render fixtures
- verify phone/email/LinkedIn/portfolio links
- create version/hash
- mark ARTIFACT_READY_NOT_INSTALLED until account mutation verified
- install into Gmail only through supported settings mutation
- re-read settings after installation
- send only a self/test message when separately authorized
- inspect received rendering before production use

### G. Message / application compiler
- define schemas for ENTRY, vacancy-specific, spontaneous, hybrid, creative, recruiter, group, portal, followups
- resolve exact organization/opportunity/person/channel
- resolve exact asset versions
- resolve exact evidence/claims
- stale-fact rejection
- unsupported-claim rejection
- portal-only suppression
- group-level routing
- idempotency key generation
- deterministic golden fixtures
- plain-text and HTML render
- no send in compiler tests

### H. Market / source acquisition
- maintain Source Registry
- snapshot source with timestamp/hash/scope
- classify CURRENT_SNAPSHOT/HISTORICAL_INDEXED/RECONCILE_REQUIRED/UNKNOWN_SCOPE
- normalize records
- entity resolve
- anti-join canonical entities
- preserve aliases/groups
- typed exclusions
- Search Proof for UNKNOWN_AFTER_SEARCH
- provenance and TTL
- source coverage metrics
- niche adapter coverage metrics
- never equate scraped row count with North Star progress

### I. Vacancy / people / channels / evidence
- current careers-page capture
- vacancy extraction
- role-family classification
- person/recruiter resolution from public professional evidence
- channel policy classification
- housing/benefit evidence
- freshness TTL assignment
- evidence conflict detection
- confidence and source tier
- typed unknown after search
- stale refresh queue creation

### J. Scoring / opportunity ranking
- 0-100 heuristic only
- reason vector
- confidence
- blockers
- lane fit
- economic proxies
- housing/benefit signals
- freshness penalty
- evidence coverage penalty
- no hiring-probability language
- calibration only from aggregate historical outcomes

### K. Scheduler / work graph
- canonical IDs only
- dependencies
- priority
- goal/checkpoint linkage
- completed anti-join
- queued-equivalent anti-join
- suppression anti-join
- freshness key
- refresh semantics
- idempotent task creation
- lease/fencing before shared mutable work

### L. Outbound safety
- CRM universe prerequisite according to active contract
- candidate lane gate
- claim gate
- evidence freshness gate
- channel policy gate
- suppression gate
- idempotency gate
- group-level dedupe
- explicit user authorization
- provider-state verification before retry
- external-action ledger before/after write
- outbound remains CLOSED by default

### M. Response / outcome ingestion
- link response to application/thread/action
- classify ACKNOWLEDGED/NO_VACANCY/REJECTED/MORE_INFO/INTERVIEW/OFFER/WITHDRAWN/OTHER
- preserve verbatim evidence reference
- observed reason separated from inferred hypothesis
- suppression propagation where applicable
- follow-up scheduler transition
- response metrics by niche/lane/CV/template/channel

### N. Interview
- interview event record
- employer/person/role verification
- prep packet from evidence
- truthful candidate claim pack
- questions for salary/housing/schedule/contract
- calendar/task persistence
- post-interview outcome/follow-up
- no fabricated language proficiency

### O. Offer / finance
- verify written offer and employer identity
- gross salary
- 13th salary
- overtime/premiums
- deductions/tax assumptions with sources
- health insurance
- housing/utilities
- food/transport/phone
- relocation costs
- buffer
- monthly free cash flow
- uncertainty ranges
- viability gate
- Roberto acceptance gate

### P. Relocation
- permit/work eligibility checklist
- employment contract artifacts
- accommodation
- insurance
- banking/payment
- municipality/admin
- travel/start-date plan
- emergency buffer
- relocation readiness checkpoint
- North Star closes only after verified viable offer is accepted and relocation is executable

### Q. Observability / persistence
Every material wave records as applicable:
- run receipt
- metrics
- SLO result
- invariant result
- issues
- state transitions
- scheduler delta
- checkpoint delta
- Git state/handoff
- Drive/Sheets mirror when authority affected
- constrained DB/manifest when authority affected
- graph/meta-memory update
- zero-context recovery pointer

## 3. Local quality ladder

L0 syntax/compile
L1 unit
L2 schema/integrity/FK
L3 integration/fixtures
L4 semantic equivalence
L5 adversarial/negative
L6 restore/replay/rollback
L7 authority/mirror reconciliation
L8 candidate/claim/gate safety
L9 outbound/idempotency/suppression
L10 zero-context recovery

No wave is PERFECT merely because L0-L3 pass. Authority-changing waves require all applicable levels.

## 4. What local can replace

Local CAN replace GitHub CI for execution of deterministic tests, static checks, DB canaries, restore drills, schema/semantic validation and artifact generation.

Local CANNOT replace independent remote verification, live Drive/Sheets truth, provider/account state, Gmail settings verification, web/source freshness, external-action provider receipts or user authorization.

## 5. Definition of done for a code wave

- local_ci PASS
- affected specialized tests PASS
- no secret/PII boundary violation
- no unresolved P0
- diff reviewed
- anti-overengineering review PASS
- state/handoff persisted
- remote CI used as independent redundant check when PR exists
- merge/rebase ancestry revalidated
- local_ci PASS again on merged main for material releases

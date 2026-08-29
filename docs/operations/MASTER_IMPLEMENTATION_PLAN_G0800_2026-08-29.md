# MASTER IMPLEMENTATION PLAN — G-0800 / SWITZERLAND_JOB_OS

Date: 2026-08-29
Status: EXECUTION CONTRACT
Authority baseline: read from `STATE.md`; never hard-code stale mutable counters into execution logic.

## 0. North Star

G-0001 remains the only business North Star: secure a truthful, legal, economically viable Swiss offer that Roberto accepts and can use for sustainable relocation.

G-0800 is the maximum-readiness operating goal: close the Swiss hotel source universe mathematically, promote canonical authority safely, deeply enrich every active hotel, generate lane-aware opportunities and personalized outreach assets, continuously refresh evidence/graph state, and leave irreversible outbound action independently gated.

## 1. Verified starting point for this plan

At plan creation, `STATE.md` reports:

- frozen member-directory snapshot `HS-MEMBER-DE-33206402141`;
- 172 source pages / 2061 source records;
- 690 active canonical hotels;
- 623 ACTIVE_MATCH and 1438 TRUE_MISSING at the current source-mapping frontier;
- 1438 / 1438 exact-current candidates verified;
- effective terminal mappings 627;
- RECONCILE_REQUIRED 1434;
- reverse authority/source gaps 66;
- Graph / Intelligence 690 / 690;
- CRM_UNIVERSE_COMPLETE = FALSE;
- OUTBOUND = CLOSED; send_allowed = 0.

These values are mutable and must be re-read from `STATE.md` before every material wave.

## 2. Critical-path theorem

The project must not optimize for raw scraping volume now. The critical path is:

```text
2061 frozen source records
→ exhaustive terminal entity-resolution decisions
→ bounded authority promotion
→ exact DB ↔ Sheets ↔ Graph ↔ Intelligence reconciliation
→ CRM_UNIVERSE_COMPLETE = TRUE
→ full L4/L5/L6/L7/L8/L9 enrichment factory
→ candidate gates
→ explicit outbound authorization
→ application/response/interview/offer/economics learning loop
```

No downstream layer may weaken an upstream truth/integrity gate.

## 3. Execution lanes

Four lanes run concurrently whenever dependencies allow.

### Lane A — CRM Universe Closure / P0

Goal: every frozen source record ends exactly once in `ACTIVE_CANONICAL | ALIAS_TO_CANONICAL | EXCLUDED_WITH_REASON`.

Pipeline:

```text
ECV complete
→ SMC exhaustive candidate
→ SRR-1.1 entity-resolution review
→ deterministic existing matches
→ explicit alias/exclusion reviews
→ NEW_CANONICAL candidates
→ unresolved = 0
→ bounded authority batches
→ final CUP validation
```

Hard gates:

- source_record_key unique;
- exact-current evidence for MATCH/ALIAS/NEW;
- no ambiguous first-match behavior;
- NEW_CANONICAL allocates no H-ID before authority commit;
- terminal source mapping immutable without a formal migration;
- RECONCILE_REQUIRED = 0 before CRM completion;
- reverse authority/source gaps = 0;
- all 2061 source records accounted for exactly once.

### Lane B — Authority Promotion Factory

Goal: convert approved NEW_CANONICAL / alias / exclusion decisions into canonical authority without cross-plane drift.

Per batch protocol:

```text
PROPOSE
→ STAGE
→ CANARY
→ VALIDATE
→ reserve immutable H-IDs only inside transaction
→ DB COMMIT
→ HOTELS_MASTER PK mirror
→ Intelligence exactly once
→ Graph nodes/edges exactly once
→ metrics/checkpoints/state
→ restore/replay proof
→ COMMIT WAVE
```

Batch sizing:

- default 25 new canonical allocations per batch;
- reduce to 10 when conflict/alias/group density is high;
- expand to 50 only after three consecutive clean 25-record batches and restore equivalence PASS.

Rollback: previous constrained DB snapshot + deterministic batch manifest + Sheets before-image/PK set + Graph/Intelligence delta digest.

### Lane C — Full Intelligence / L9 Factory

Goal: every active canonical hotel becomes an evidence-backed dossier.

Level contract:

```text
L1 identity admitted
L2 official web/contact basics
L3 careers/vacancy resolution
L4 vacancy + housing + people + channels/groups core
L5 social + digital + creative + tech audits
L6 lane opportunities + heuristic scores
L7 hotel-specific proposition / personalization
L8 channel-specific message bundle
L9 full QA / provenance / TTL / suppression / idempotency readiness
L10 SEND_ALLOWED only after independent explicit authorization gate
```

For every unresolved dimension use either `SEARCH_PENDING` or `UNKNOWN_AFTER_SEARCH + SEARCH_PROOF_V3`; never infer negatives from absence.

### Lane D — Candidate / Offer Acquisition

Goal: turn market readiness into real interviews/offers without contaminating market truth.

Sequence:

```text
candidate truth completion
→ lane assets ENTRY/HYBRID/CREATIVE/PORTAL
→ claims ledger / asset QA
→ market + candidate + channel gates
→ explicit user authorization
→ bounded outbound
→ response classification
→ interview prep
→ offer verification
→ OFFER_FINANCIAL_MODEL
→ accept/reject decision
→ feedback into scoring/calibration
```

Outbound remains CLOSED until all independent gates pass.

## 4. Checkpoint graph

### CP-R01 — SRR deterministic baseline

Definition of Done:

- build SRR over all current RECONCILE_REQUIRED records;
- classify deterministic exact-detail/name+city matches;
- quantify NEW_CANONICAL proposals;
- quantify ambiguous/unresolved records;
- artifact validates under SRR transfer validator;
- no H-ID allocation; authority unchanged.

### CP-R02 — Resolution review complete

DoD:

- every remaining ambiguous record has evidence-backed review;
- alias/exclusion semantics explicit;
- unresolved_review = 0;
- authority_batch_ready = TRUE;
- deterministic hashes persisted.

### CP-A01 — Authority canary

DoD:

- first bounded batch promoted DB-first;
- native Sheets PK mirror PASS;
- Intelligence/Graph exact;
- restore/replay exact;
- zero duplicate IDs / FK violations / orphan edges / denominator drift.

### CP-A02 — Authority scale

DoD:

- all approved NEW_CANONICAL/alias/exclusion decisions committed in bounded batches;
- every batch independently recoverable;
- no outstanding batch drift.

### CP-CUP — CRM Universe Complete

DoD:

```text
raw source records = 2061 (or current frozen-snapshot count)
unmapped = 0
RECONCILE_REQUIRED = 0
reverse authority/source gaps = 0
invalid aliases = 0
duplicate source conflicts = 0
DB ↔ Sheets exact
Graph exact
Intelligence exact
same snapshot lineage
same active denominator
CRM_UNIVERSE_COMPLETE = TRUE
```

### CP-I04 — 100% active canonical L4

All active canonical hotels have core vacancy/housing/people/channel/group resolution or typed unknown/search proof.

### CP-I05 — 100% L5

Social/digital/creative/tech audits complete or typed unknown with proof.

### CP-I06 — 100% L6

ENTRY/HYBRID/CREATIVE/PORTAL opportunity graph and heuristic scores generated with evidence vectors.

### CP-I07 — 100% L7

Hotel-specific proposition exists for every eligible lane/hotel pair and references only supported claims.

### CP-I08 — 100% L8

Channel policy aware email/portal/form/LinkedIn and WhatsApp-only-when-eligible drafts generated and versioned.

### CP-I09 — 100% L9

Claims QA, asset QA, provenance, freshness, TTL, suppression, idempotency and render validation PASS for every dossier.

### CP-OS — Realtime operating system

DB, Sheets, Graph, Intelligence, Scheduler, metrics, RUN_LOG, DECISION_LEDGER, STATE and recovery manifests converge after every material wave.

### CP-OFFER — North Star event

A real Swiss offer is verified, financially modeled and accepted by Roberto. Only this closes G-0001.

## 5. Scheduler priorities

```text
P1000 integrity/authority corruption
P980  source identity conflict / impossible mapping
P960  reverse authority/source gap
P950  ambiguous entity resolution
P930  authority canary/restore blocker
P900  NEW_CANONICAL exact-current/dedupe work
P850  explicit exclusion/alias review
P800  L4 core enrichment
P700  L5 audits
P650  L6 opportunity scoring
P600  L7 personalization
P550  L8 message rendering
P500  L9 QA/freshness
P400  TTL refresh
```

Anti-join completed work, open tasks, fresh facts, suppression, duplicate target and dependency blockers before task creation.

## 6. Test matrix / gauntlet

Every structural release must run:

1. repo_guard;
2. system_contract_guard;
3. all unit tests;
4. SQLite `integrity_check = ok`;
5. FK violations = 0;
6. PK uniqueness / duplicate source key scans;
7. source mapping conservation equation;
8. alias-target validity;
9. Graph endpoint/orphan scan;
10. DB↔Sheets exact active denominator;
11. Intelligence/Graph active denominator exact;
12. replay from previous recovery artifact;
13. idempotent re-run produces no semantic delta;
14. outbound/send_allowed remain closed unless explicitly authorized.

At 25%, 50%, 75% and 100% of authority promotion execute a full restore/replay rehearsal.

## 7. Observability

Canonical metrics:

- source_records_total;
- terminal_mappings;
- reconcile_required;
- reverse_gaps;
- active_canonical;
- aliases;
- exclusions;
- new_canonical_pending;
- SRR unresolved;
- L4/L5/L6/L7/L8/L9 counts;
- stale facts by TTL class;
- graph/DB/Sheets denominator parity;
- scheduler backlog by task type/priority;
- external_actions;
- responses/interviews/offers.

A metric has one canonical live value; no duplicate authoritative metric rows.

## 8. Persistence contract

After each material state change update, as applicable:

```text
constrained DB + manifest
HOTELS_MASTER control plane
Graph / Intelligence
RUN_LOG
DECISION_LEDGER
STATE_TRANSITIONS
GOAL_STATE / CHECKPOINT_REGISTRY
ENGINE_METRICS / ENGINE_HEALTH
STATE.md
ACTA_DE_CONSCIENCIA.md
PROGRESS.md when present
recovery manifest / snapshot
```

Stable contracts (`GOAL.md`, `AGENTS.md`, operating protocols) change only when semantics change.

## 9. Immediate execution order

The next work sequence is fixed:

```text
W1  Re-read current STATE and ECV/SMC artifacts
W2  Build full SRR deterministic baseline
W3  Validate SRR and persist exact distribution
W4  Resolve ambiguous alias/exclusion records
W5  Reach authority_batch_ready
W6  Execute first authority canary batch
W7  Restore/replay + cross-plane reconciliation
W8  Scale bounded authority batches to source-universe closure
W9  Run final CUP gate and set CRM_UNIVERSE_COMPLETE only if every condition passes
W10 Shift dominant capacity to L4→L9 enrichment while TTL refresh runs continuously
W11 Candidate lanes/assets to ready state
W12 Only after explicit authorization, execute bounded outreach and learn from real responses
```

## 10. Stop conditions

Stop the active wave and fail closed on any of:

- stale parent/authority ancestry;
- source snapshot lineage mismatch;
- duplicate canonical/source keys;
- unresolved ambiguous target during promotion;
- DB/Sheets/Graph/Intelligence denominator drift;
- graph orphan endpoints;
- restore/replay mismatch;
- unexpected H-ID allocation;
- unsupported claim entering personalization/outbound;
- outbound action without explicit authorization.

## 11. Success criterion for this implementation program

The program is successful only when the system can prove, from a single frozen/versioned source universe through deterministic mappings and synchronized authority, that every target hotel is accounted for and can be continuously enriched to L9, while producing real, truthful, evidence-backed employment opportunities and eventually a verified accepted offer.

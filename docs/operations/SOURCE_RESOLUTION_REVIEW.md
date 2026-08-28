# SOURCE RESOLUTION REVIEW — SWITZERLAND_JOB_OS

Version: **SRR-1.0**  
Status: **EXECUTABLE PRE-AUTHORITY ENTITY-RESOLUTION CONTRACT**

## Objective

Turn SMC-1.0 `RECONCILE_REQUIRED` source records into an explicit, auditable pre-authority resolution plan without allocating canonical IDs or mutating the operational authority plane.

```text
SMC-1.0 exhaustive source mapping candidate
+ read-only active canonical catalog
+ optional explicit resolution reviews
→ deterministic source resolution review
→ terminalizable existing/alias/exclusion mappings
+ NEW_CANONICAL authority work
+ unresolved research work
```

SRR exists because `unmapped_records = 0` is not enough. A complete frozen source universe can still contain records that require entity-resolution decisions before an authority-eligible DB → Sheets → Graph/Intelligence promotion.

## Resolution actions

```text
MATCH_EXISTING
ALIAS_EXISTING
EXCLUDE
NEW_CANONICAL
UNRESOLVED
```

`MATCH_EXISTING`, `ALIAS_EXISTING` and `NEW_CANONICAL` require current exact evidence. `MATCH_EXISTING` and `ALIAS_EXISTING` also require a unique active canonical target in the supplied catalog.

`EXCLUDE` requires an explicit typed `reason_code` and `evidence_ref`. It is a candidate terminal source mapping only; the exclusion is persisted during the later authority commit.

`NEW_CANONICAL` never allocates an H-ID in SRR. It remains `RECONCILE_REQUIRED` with:

```text
authority_action = ALLOCATE_NEW_CANONICAL_ON_AUTHORITY_COMMIT
```

## Deterministic auto-proposal precedence

When an explicit review is not supplied for an SMC reconcile record, SRR may produce a proposal using the read-only active canonical catalog:

```text
1. unique exact normalized HotellerieSuisse detail URL
2. unique normalized name + city
3. no canonical match + CURRENT_DETAIL_VERIFIED → NEW_CANONICAL proposal
4. ambiguity / weak evidence → UNRESOLVED
```

Ambiguous matches never select the first result.

Auto-proposal is a work-planning aid, not authority. An operator/agent may provide explicit review records where alias or exclusion semantics require evidence beyond deterministic identity matching.

## Input review schema

```json
[
  {
    "source_record_key": "hs:123",
    "action": "ALIAS_EXISTING",
    "canonical_hotel_id": "H-0042",
    "reason_code": "VERIFIED_NAMING_VARIANT",
    "evidence_ref": "evidence:..."
  }
]
```

Reviews may target only SMC mappings currently in `RECONCILE_REQUIRED`. A terminal SMC mapping cannot be rewritten by SRR.

## Canonical catalog boundary

The catalog is a read-only authority snapshot used only for deterministic target validation. Minimal fields:

```json
[
  {
    "hotel_id": "H-0042",
    "name": "Example Hotel",
    "city": "Bern",
    "detail_url": "https://.../hotel-example-hotel",
    "is_active": true
  }
]
```

Canonical IDs must be unique. `is_active` is strict JSON boolean. Non-active targets are forbidden for match/alias actions.

Private production catalog data does not belong in the public repository; only synthetic fixtures/contracts do.

## Output semantics

SRR reports independently:

```text
original_reconcile_required
explicit_reviews_supplied
explicit_review_complete
review_decision_complete
counts_by_mapping_state
counts_by_resolution_action
terminal_mappings_candidate
new_canonical_candidates
unresolved_review
reconcile_required_after_review
terminal_mapping_coverage_pct
authority_batch_ready
```

`authority_batch_ready` means no SRR item remains `UNRESOLVED`; it does **not** mean authority was committed, `RECONCILE_REQUIRED=0`, or CRM completion was reached. `NEW_CANONICAL` items still require the bounded authority transaction that allocates immutable H-IDs and reconciles every affected plane.

## Commands

```bash
python -m swiss_os.source_resolution build \
  CRM_SOURCE_MAPPING_CANDIDATE.json \
  CANONICAL_CATALOG.json \
  --reviews RESOLUTION_REVIEWS.json \
  --out SOURCE_RESOLUTION_REVIEW.json

python -m swiss_os.source_resolution validate SOURCE_RESOLUTION_REVIEW.json
```

`--reviews` is optional; without it SRR emits deterministic proposals under the precedence above.

## Relationship to CRM universe completion

```text
coherent source capture
→ SSR / source-scope reconciliation
→ CMI anti-join
→ CWP active work packets
→ ECV exact-current verification
→ SMC exhaustive source mapping candidate
→ SRR entity-resolution review
→ bounded authority allocation/mapping transaction
→ DB
→ HOTELS_MASTER by PK
→ Intelligence
→ Operational Graph
→ observability / recovery
→ final CUP validation
→ CRM_UNIVERSE_COMPLETE only when every gate passes
```

SRR intentionally cannot skip the authority transaction.

## Hard invariants

```text
SMC input valid and strictly pre-authority
source_record_key unique
terminal SMC mappings immutable in SRR
canonical target exists and is active
ambiguous deterministic matches remain unresolved
current exact evidence required for existing/alias/new-canonical decisions
NEW_CANONICAL allocates no H-ID
all output hashes deterministic
CRM_UNIVERSE_COMPLETE = FALSE
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND = CLOSED
send_allowed = 0
```

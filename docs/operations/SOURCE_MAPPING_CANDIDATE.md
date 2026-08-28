# SOURCE MAPPING CANDIDATE — SWITZERLAND_JOB_OS

Version: **SMC-1.0**  
Status: **EXECUTABLE PRE-AUTHORITY CUP MAPPING CONTRACT**

## Objective

Account for every source record from the complete directory snapshot exactly once after CMI anti-join and exact-current verification.

```text
CMI decisions
+
final exact-current verified/requeue ledgers
→ one mapping per source_record_key
→ ACTIVE_CANONICAL | RECONCILE_REQUIRED
→ exhaustive source mapping candidate
```

SMC eliminates silent unmapped source records while refusing to disguise unresolved/new/conflicting records as canonical.

## Input

- complete CMI decision set for one snapshot;
- final exact-current verified result array;
- final exact-current requeue result array;
- exact source snapshot ID and manifest SHA-256.

Verification arrays must contain unique active source keys and may not include terminal CMI matches.

## Mapping rules

### Existing terminal match

```text
CMI work_state = MATCHED_EXISTING
+ canonical target present
→ mapping_state = ACTIVE_CANONICAL
→ reason = CMI_EXISTING_CANONICAL_MATCH
```

### Verified new entity

```text
VERIFY_NEW_ENTITY
+ CURRENT_DETAIL_VERIFIED
→ mapping_state = RECONCILE_REQUIRED
→ reason = CURRENT_VERIFIED_NEW_ENTITY_AWAITING_CANONICAL_REVIEW
```

It remains unresolved until dedupe/group/alias review and an authority-eligible canonical commit.

### Verified conflict

```text
RECONCILE_REQUIRED
+ CURRENT_DETAIL_VERIFIED
→ mapping_state = RECONCILE_REQUIRED
→ reason = CURRENT_VERIFIED_CANONICAL_CONFLICT
```

### Weak/failed current evidence

```text
name-only | city-only | mismatch | fetch failure | robots block
→ mapping_state = RECONCILE_REQUIRED
→ typed exact-current reason
```

### Unknown CMI semantics

Never inferred as canonical. It remains `RECONCILE_REQUIRED`.

## Output metrics

```text
source_records
mappings_count
unmapped_records
counts_by_mapping_state
terminal_mappings
reconcile_required
terminal_mapping_coverage_pct
mapping_sha256
candidate_sha256
```

The candidate may reach `unmapped_records=0` while still remaining incomplete because `RECONCILE_REQUIRED > 0`.

## Commands

```bash
python -m swiss_os.source_mapping build \
  CMI_STDOUT.json \
  EXACT_CURRENT_VERIFIED_FINAL.json \
  EXACT_CURRENT_REQUEUE_FINAL.json \
  --snapshot-id <snapshot-id> \
  --source-manifest-sha256 <sha256> \
  --out CRM_SOURCE_MAPPING_CANDIDATE.json

python -m swiss_os.source_mapping validate \
  CRM_SOURCE_MAPPING_CANDIDATE.json
```

## CUP relationship

SMC supports the CUP requirement that every frozen source record maps to exactly one terminal/reconcile state.

It does not set completion because the candidate intentionally keeps:

```text
CRM_UNIVERSE_COMPLETE = FALSE
SOURCE_SCOPE_SSR_PENDING
RECONCILE_REQUIRED not zero or authority reconciliation pending
```

## Hard invariants

```text
source keys unique
one mapping per CMI decision
ACTIVE_CANONICAL requires canonical target
RECONCILE_REQUIRED cannot carry canonical target
mapping and candidate hashes exact
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND = CLOSED
send_allowed = 0
```

A future terminalization engine may convert a mapping only with explicit evidence and constrained state transitions.

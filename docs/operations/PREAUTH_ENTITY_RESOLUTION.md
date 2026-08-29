# PRE-AUTHORITY ENTITY RESOLUTION — SWITZERLAND_JOB_OS

Version: **ER-PREAUTH-1.0**  
Status: **READ-ONLY / REVIEW WORKSET**

## Purpose

Once the complete candidate set has exact-current evidence, produce a deterministic review workset that finds only exact duplicate-equivalence components without creating canonical identity, source mappings, aliases, exclusions, or authority mutations.

## Allowed exact signals

```text
EXACT_DETAIL_URL
EXACT_NAME_CITY
```

Signals are normalized with the same `normalize_url` / `normalize_text` primitives used by snapshot and mass-ingest identity logic. Components are transitive unions of exact signals. Fuzzy similarity, embeddings, model judgment, page position, and cache-only inference are forbidden.

## Inputs / gates

```text
one frozen snapshot id
all CMI work packets for that snapshot
NEXT.ecv_frontier.current_detail_verified == candidate_records_total
remaining_unverified == 0
remaining_never_verified == 0
pending_requeue == 0
lineage_holes == []
```

Packet safety is fail-closed. Conflicting repeated `source_record_key` records abort the workset. Byte-identical repeated records are deduplicated because historical/subbatch packet overlap is expected.

## Outputs

```text
EXACT_DUPLICATE_GROUP_REVIEW
unique_source_record_keys
entity_group_candidates
workset_sha256
```

A duplicate group is a review candidate, not an alias edge and not a merge decision. A unique record is still only a pre-authority new-entity candidate.

## Hard invariants

```text
terminal_mapping_effect = NONE
canonical_id_allocation_allowed = false
H_ID_ALLOCATIONS = 0
AUTHORITY_ADVANCED = false
OUTBOUND = CLOSED
send_allowed = 0
```

No H-ID may be reserved or allocated by this phase. No `ACTIVE_CANONICAL`, `ALIAS_TO_CANONICAL`, or `EXCLUDED_WITH_REASON` mapping may be emitted from this workset.

## Execution

```bash
PYTHONPATH=src python -m swiss_os.preauth_entity_resolution build \
  docs/state \
  --next docs/state/NEXT.json \
  --snapshot-id HS-MEMBER-DE-33206402141 \
  --expected-records 1438 \
  --out .artifacts/PREAUTH_ENTITY_RESOLUTION_33206402141.json

PYTHONPATH=src python -m swiss_os.preauth_entity_resolution validate \
  .artifacts/PREAUTH_ENTITY_RESOLUTION_33206402141.json
```

The GitHub workflow `preauth-entity-resolution-workset.yml` performs this read-only build on `main` only when the durable NEXT route and exact-current completion gate match.

## Promotion boundary

Any later change that converts review candidates into terminal source mappings, canonical identities, alias edges, exclusions, or authority state is a separate authority-sensitive WOP and must satisfy its own branch → tests → PR → CI → adversarial review → merge contract. SSR-1.0 and cross-plane reconciliation remain independent hard gates.

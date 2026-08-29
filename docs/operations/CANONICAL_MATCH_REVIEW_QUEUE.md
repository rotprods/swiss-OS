# CMRQ-1.0 — Canonical Match Review Queue

## Purpose

`CMRQ-1.0` is the read-only candidate→canonical similarity gate that follows exact-current verification and `CEP-1.1` candidate partitioning.

It exists to surface a **bounded evidence-review queue** for likely duplicate, alias, legacy-name or near-duplicate relationships between PREAUTH candidate source records and the active E4 canonical catalog. It must never convert fuzzy similarity into a terminal mapping by itself.

## Inputs

- frozen candidate universe / snapshot lineage;
- deterministic candidate records SHA-256;
- active canonical catalog plus deterministic catalog SHA-256;
- candidate records must still be PREAUTH and must not already carry `matched_hotel_id`.

Private canonical rows may be materialized from `HOTELS_MASTER` for execution, but the full private catalog or full review queue must not be committed to public GitHub. Persist full recovery evidence in an authorized private plane such as Drive; GitHub may carry hashes and public-safe counts.

## Review signals

All candidate→canonical comparisons are city-scoped first. A pair can enter the queue only when normalized cities are equal and at least one deterministic signal fires:

1. `EXACT_NORMALIZED_NAME_CITY` — normalized names are identical;
2. `TOKEN_SIGNATURE_EQUAL` — generic hotel vocabulary removed, remaining token sets are equal;
3. `VERY_HIGH_NAME_SIMILARITY` — deterministic `SequenceMatcher` ratio >= `0.92`;
4. `HIGH_TOKEN_OVERLAP` — token Jaccard >= `0.75` and name similarity >= `0.75`.

The normalization profile and thresholds are emitted into every result and hashed as part of the review policy.

## Hard semantics

A queue row is **not** a resolution decision.

```text
required_action = EVIDENCE_BACKED_EXPLICIT_REVIEW
auto_merge_allowed = false
terminal_mapping_allowed_from_queue = false
authority_advanced = false
h_id_allocations = 0
canonical_id_reservations = 0
outbound = CLOSED
send_allowed = 0
```

The queue schema intentionally forbids `action` and `resolution_action` fields. Any terminal `MATCH_EXISTING`, `ALIAS_EXISTING`, `EXCLUDE` or `NEW_CANONICAL` decision must be expressed later through the existing `source_resolution.py` explicit-review contract with current evidence and its normal validation gates.

## Determinism and QA

The engine:

- fails closed on malformed candidate/canonical records, duplicate source keys, duplicate H-IDs, invalid hashes, pre-matched candidates or unsafe candidate export flags;
- evaluates only same-city canonical candidates;
- sorts candidates, canonical targets and queue output deterministically;
- hashes both policy and full queue using canonical JSON;
- reports pair count, distinct source count, multi-target count and per-signal counts;
- validates that no queue row encodes a resolution action, crosses city boundaries or enables authority/outbound effects.

## Production flow

```text
ECV 1438/1438
  -> CEP-1.1 exact candidate partition
  -> CMRQ-1.0 review-only candidate→canonical queue
  -> evidence-backed explicit review(s)
  -> SOURCE-RESOLUTION-REVIEW-1.0
  -> authority work manifest only when all identity/reconciliation gates pass
```

Fuzzy similarity is discovery evidence only. It can reduce the manual review search space; it cannot reserve an H-ID, create an alias, mutate HOTELS_MASTER, advance authority, open outbound, or satisfy `CRM_UNIVERSE_COMPLETE` by itself.

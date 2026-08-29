# SRET-1.0 — Source Resolution Evidence Triage

Status: pre-authority, review-only.

SRET exists to classify `RECONCILE_REQUIRED` source records into bounded evidence work without weakening SRR-1.x identity requirements. It is deliberately positioned before terminal source resolution. It MUST NOT allocate or reserve a canonical H-ID, mutate authority, open outbound, infer deletion from source absence, or turn similarity into an identity decision.

## Inputs

1. A complete source-mapping payload containing a `mappings` array. Existing terminal mappings are carried as counts and are not rewritten.
2. The active canonical catalog with explicit boolean `is_active` values.

The caller is responsible for pinning the source-mapping and canonical-catalog lineage to durable hashes. SRET itself is deterministic for identical JSON inputs.

## Triage states

`MATCH_EXISTING_REVIEW`: a unique exact detail-URL or normalized name+city identity signal exists. This is a review queue state, not a terminal mapping. SRR still requires independently sufficient current identity evidence.

`AMBIGUOUS_REVIEW`: exact signals conflict, are duplicated, or the same normalized name occurs under another locality. Locality/name collisions remain unresolved until independent evidence disambiguates them.

`NOVELTY_REVIEW`: the source record has current exact evidence but no exact canonical identity signal. This means only that a novelty/distinctness review is warranted. It MUST NOT be interpreted as `NEW_CANONICAL_READY`, and it MUST NOT reserve or allocate an H-ID.

`EVIDENCE_PENDING`: current exact evidence is absent or non-terminal, so identity classification must not advance.

## Similarity semantics

Same-city token-Jaccard suggestions may be emitted to reduce review space. Every such suggestion is marked `REVIEW_SPACE_REDUCTION_ONLY`. Similarity never changes the triage state, never sets `canonical_hotel_id`, and never authorizes SRR or authority mutation.

## Hard invariants

Every SRET output and item asserts:

- `terminal_mapping_allowed=false`
- `canonical_id_reservation_allowed=false`
- `authority_advanced=false`
- `h_id_allocations=0`
- `crm_universe_complete=false`
- `OUTBOUND=CLOSED`
- `send_allowed=0`
- item `authority_action=NONE`

The validator rejects any item that contains a non-empty `canonical_hotel_id` or `allocated_hotel_id`.

## Execution

```bash
python -m swiss_os.source_resolution_evidence_triage build \
  effective_source_mapping.json canonical_catalog.json \
  --out source_resolution_evidence_triage.json

python -m swiss_os.source_resolution_evidence_triage validate \
  source_resolution_evidence_triage.json
```

## Relationship to SRR / SMO / RAGR

SRET does not replace SRR or SMO. It produces review work from the source-to-authority direction after exact-current verification. `MATCH_EXISTING_REVIEW` records can become SRR `MATCH_EXISTING` only after evidence sufficiency is independently demonstrated. `NOVELTY_REVIEW` can become an explicit `NEW_CANONICAL` review only after distinctness is independently demonstrated; even then, no H-ID is allocated until a separately authorized authority transaction.

RAGR remains the reverse diagnostic from active canonical authority to source coverage. Once RAGR's safe shallow exact routes are exhausted, SRET is the preferred next layer for the unresolved source tail because it preserves ambiguity instead of forcing a fuzzy mapping.

## Failure posture

Fail closed on malformed mappings, duplicate source keys, non-boolean catalog activity, unsupported mapping states, unsafe authority/outbound flags, hash tampering, or attempted target/ID materialization. A failed SRET run changes no authority state.

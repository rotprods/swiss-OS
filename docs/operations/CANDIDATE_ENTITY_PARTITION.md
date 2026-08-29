# Candidate Entity Partition — CEP-1.1

CEP-1.1 is the pre-authority entity-partition gate for `CRM_UNIVERSE_COMPLETE`.

It consumes the durable multipart `CRM_CANDIDATE_EXPORT_33206402141` through the same lineage validator used by the candidate materializer. It does **not** consume chat state, cache state, a canary-only reconstruction, or a newly scraped universe.

## Exact rules

1. Every candidate record is assigned exactly once.
2. Two or more candidate rows sharing the same normalized, non-empty `detail_url` form a `STABLE_SAME_ENTITY_CLUSTER`.
3. All remaining rows remain `SINGLETON_DISTINCT_CANDIDATE`.
4. Equal normalized `name + city` across distinct stable identities is diagnostic only and becomes `EXPLICIT_ENTITY_REVIEW_NO_AUTOMERGE`.
5. Missing detail URLs become `REFRESH_STABLE_ENTITY_DETAIL` review items.
6. No fuzzy score, nearest-neighbour choice, first-match heuristic or language-model inference may merge identities in this gate.

## Hard safety invariants

CEP never reserves or allocates canonical H-IDs, never advances the authority epoch, never mutates `HOTELS_MASTER`, never opens outbound, and never changes `send_allowed`.

Required values in every CEP artifact:

- `authority_advanced=false`
- `h_id_allocations=0`
- `canonical_id_reservations=0`
- `outbound=CLOSED`
- `outbound_opened=false`
- `send_allowed=0`

The partition is pre-authority evidence only. Even an `EXACT_PARTITION` does not authorize canonical allocation. Canonical near-duplicate/alias review, reverse authority/source reconciliation and the final cross-plane gate remain separate dependencies.

## Current CP-R01 acceptance gate

For snapshot `HS-MEMBER-DE-33206402141`, the exact-current candidate transport must resolve to:

- 1,438 candidate records
- 1,438 exact assignments
- 1,438 singleton clusters
- 0 exact shared-detail-url clusters
- 0 normalized name+city collision groups
- 0 missing detail URLs
- 0 omitted, foreign or duplicate assignments

Any deviation fails the canary and reopens the entity-partition P0 rather than silently changing identity semantics.

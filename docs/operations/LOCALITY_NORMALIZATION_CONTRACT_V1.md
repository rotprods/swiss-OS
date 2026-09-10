# LOCALITY NORMALIZATION CONTRACT V1

## Purpose

Reduce false-new-property risk caused by presentation differences in Swiss localities without converting locality similarity into identity authority.

## Authority semantics

`locality_keys()` and `locality_variant_review()` are REVIEW-SPACE primitives only.

A locality equivalence:

- MAY add canonical comparators;
- MAY mark ambiguity;
- MAY route a row away from the naive zero-city lane;
- MUST NOT prove same-property identity;
- MUST NOT create a source mapping;
- MUST NOT reserve or allocate an H-ID;
- MUST NOT mutate canonical authority;
- MUST NOT open outbound.

## Conservative transformations

Current review keys may normalize accents/punctuation, parenthetical qualifiers, canton-code suffixes, numeric district suffixes and terminal airport/aeroport qualifiers.

Every transformation is lossy and therefore non-authoritative.

## Fail-closed conditions

The guard raises on duplicate or missing source record keys and duplicate or missing canonical hotel IDs. A normalized locality with multiple canonical targets is explicitly `MULTIPLE_CANONICAL_LOCALITY_CANDIDATES`.

Exact global-name cross-locality collisions are segregated into a distinct identity-conflict lane before zero-city batching.

## Regression corpus

Permanent examples include:

- `Wilen (Sarnen)` ↔ `Wilen` — discovered false zero-city negative, same-property later proven separately for Seehotel Wilerbad/H-0681;
- `Brienz` ↔ `Brienz BE`;
- `Davos-Dorf` ↔ `Davos Dorf`;
- `Genève 15 Aéroport` ↔ `Genève`;
- `Neuchâtel 1` ↔ `Neuchâtel`.

The first example proves why the guard exists; it does not authorize the other examples to bind.

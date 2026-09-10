# LOCALITY NORMALIZATION CONTRACT V1

Authority: PREAUTH review-space only.

Purpose: reduce false-new-property risk caused by presentation differences in Swiss localities without converting locality similarity into identity authority.

`locality_keys()` and `locality_variant_review()` MAY expand canonical comparators, flag ambiguity, and route a row away from naive zero-city novelty. They MUST NOT prove same-property identity, create a source mapping, reserve/allocate an H-ID, mutate canonical authority, or open outbound.

Conservative review transformations currently include accents/punctuation, parenthetical qualifiers, canton-code suffixes, numeric district suffixes, and terminal airport/aeroport qualifiers. Every transformation is lossy and non-authoritative.

Fail closed on duplicate/missing source record keys and duplicate/missing canonical hotel IDs. A locality normalization that exposes multiple canonical candidates is `MULTIPLE_CANONICAL_LOCALITY_CANDIDATES`, not a match.

Exact global-name cross-locality collisions are segregated into a distinct identity-conflict lane before zero-city batching.

Permanent regression examples: `Wilen (Sarnen)` ↔ `Wilen`; `Brienz` ↔ `Brienz BE`; `Davos-Dorf` ↔ `Davos Dorf`; `Genève 15 Aéroport` ↔ `Genève`; `Neuchâtel 1` ↔ `Neuchâtel`. Only Wilerbad has separate same-property evidence; these locality examples do not authorize other binds.

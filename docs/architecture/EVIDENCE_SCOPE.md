# Canonical Evidence Scope

Canonical identity evidence is scope-aware. A source may support current entity identity without supporting every stronger membership claim.

## Scope classes

### EXACT_CURRENT_ENTITY_DETAIL

Direct current HotellerieSuisse entity/member detail. Highest-preference canonical identity evidence.

### CURRENT_REGIONAL_ASSOCIATION_SUPPORT

Current first-party HotellerieSuisse regional association/board surface that explicitly links the named property to the association context. This may support a current entity relationship when identity, location and dedupe gates pass, but it must never be relabeled as exact member-directory detail.

### HISTORICAL_OR_INDEX_DISCOVERY

Historical/cache/index/pagination surfaces. Discovery only until current entity-level reconciliation supplies sufficient evidence.

### RECONCILE_REQUIRED

Identity or scope remains ambiguous. No active canonical promotion.

## Promotion contract

A non-exact support source may enter canonical state only when all applicable gates pass:

1. source is current and first-party;
2. subject property and location are unambiguous;
3. source scope is stored explicitly;
4. normalized name/city/domain/alias anti-join passes;
5. identity confidence satisfies the declared policy;
6. constrained DB canary/constraints pass;
7. Sheets mirror and active canonical set reconcile;
8. Intelligence and Graph receive the same immutable PK exactly once;
9. observability/governance counters advance in the same material execution;
10. no stronger claim is inferred from the weaker evidence scope.

Evidence precedence remains scope-aware. Exact detail is preferred; current support is not silently upgraded; historical/index material is not current membership evidence.

## E4 precedent

`HS_ENTITY_EPOCH_2026-08-25_E4` admitted `H-0678..H-0690` under explicit `CURRENT_REGIONAL_ASSOCIATION_SUPPORT` semantics. These records are L1 identity seeds. Their unresolved vacancy, housing, people, channel, social, digital and tech dimensions remain `SEARCH_PENDING` until separately resolved.

This contract prevents two failure modes at once: rejecting useful current first-party identity evidence merely because it is not an exact directory detail, and overstating what that evidence actually proves.

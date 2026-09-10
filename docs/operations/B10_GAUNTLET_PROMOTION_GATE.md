# B10 GAUNTLET PROMOTION GATE

Promotion requires all of the following on the same candidate head:

1. Claim `CLAIM-CRM-ENTITY-RESOLUTION-017` is terminal (`RELEASED`).
2. Coordination projection is deterministically rebuilt and reports zero active token17 writers.
3. `fencing_high_watermark >= 17` and equals the maximum durable claim token.
4. Locality guard unit/adversarial tests pass.
5. B10 state/evidence/NEXT regression tests pass.
6. Exact-global-name locality conflicts remain excluded from B11 zero-city selection.
7. Repository guard, stable-contract guard, V2 coordination guard, recovery/death drill, continuity guards and manifest canaries all pass.
8. Live main is reread after CI. Any relevant-scope drift blocks merge; unrelated descendant drift requires ancestry-safe reconciliation.
9. Authority tuple remains E4/690, H-0691 unallocated, terminal mappings 658, RECONCILE_REQUIRED 1403, OUTBOUND=CLOSED, send_allowed=0.
10. Merge uses expected tested head SHA.

If any condition fails, promotion state is `BLOCKED_GAUNTLET`; do not weaken the invariant to obtain green CI.

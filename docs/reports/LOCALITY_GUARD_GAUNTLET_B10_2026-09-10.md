# LOCALITY GUARD ADVERSARIAL GAUNTLET — B10

State: PREAUTHORITY / NO HOTEL AUTHORITY EFFECT

## Failure families covered

1. Literal locality false negatives such as `Wilen (Sarnen)` vs `Wilen`.
2. Accent/punctuation variants such as `Genève` vs `Geneve`.
3. Canton and district qualifiers such as `Brienz BE` and numeric locality suffixes.
4. Airport presentation suffixes such as `Genève 15 Aéroport`.
5. Multiple canonical candidates sharing the same conservative locality key: explicit ambiguity, never autobind.
6. Duplicate source record keys: fail closed.
7. Duplicate canonical H-IDs: fail closed.
8. Missing source/canonical identities: fail closed.
9. Exact global-name cross-locality conflicts: segregated from the zero-city lane.
10. Deterministic source-key ordering and replay.
11. Stale fencing projection after claim release: CI must reject high-watermark lag.
12. STATE/NEXT divergence: CI must reject different B11 worksets.
13. Test-runner drift: tests remain stdlib `unittest` compatible.

## Current measured reconstruction

```text
source universe                         2061
candidate universe                      1438
raw literal zero-exact-city              488
exact-global-name conflicts segregated     3
operational zero-city lane                485
B01..B10 reviewed                         100
zero-city remaining                       385
locality-expanded review candidates         5
```

The locality normalization layer is a comparator-space expansion only. It has no permission to create a terminal source mapping, reserve/allocate an H-ID, mutate hotel authority, or open outbound.

## Safety result

B10 keeps E4/690 unchanged, H-0691 unallocated, terminal mappings at 658, RECONCILE_REQUIRED at 1403, CRM_UNIVERSE_COMPLETE=false, OUTBOUND=CLOSED and send_allowed=0.

## Promotion gate

This branch is not mergeable merely because locality unit tests pass. Promotion requires:

- token17 released;
- deterministic coordination projection rebuilt with fencing high-watermark >=17 and no token17 active claim;
- B10/STATE/NEXT contract tests green;
- full repository guard green;
- fresh-main drift check before merge.

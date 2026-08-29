# ASR repair canary V2 — issue #89

Status: **CANARY_PASS_DOWNSTREAM_AUTHORITY_RECONCILIATION_REQUIRED**

This public-safe state artifact records the non-authoritative repair canary for the four phantom alias edges identified in issue #89.

## Proven semantic failure

The persisted edges were:

```text
H-0610 → H-0656
H-0624 → H-0639
H-0629 → H-0638
H-0630 → H-0640
```

The purported alias H-IDs identify four unrelated physical hotels consistently across the available constrained lineage and HOTELS_MASTER. Each target identity is unique in V13 and HOTELS_MASTER. `ENTITY_RESOLUTION` names the target identity but binds the wrong physical H-ID, proving H-ID/row drift rather than a real duplicate hotel.

## V13 repair canary

```text
invalid alias edges quarantined      4
physical H-IDs preserved           690
effective active projection        690
SQLite integrity                    ok
FK violations                        0
repair replay unintended deletes     0
active name+city duplicates           0
known bad edges remaining             0
restore integrity                    ok
restore FK violations                 0
```

The canary:

- allocates no H-ID;
- mutates no authoritative Sheets/CRM state;
- advances no checkpoint or canonical authority;
- performs no external action;
- keeps `CRM_UNIVERSE_COMPLETE = FALSE`;
- keeps `OUTBOUND = CLOSED` and `send_allowed = 0`.

## Authority consequence

The previously published `686 active` denominator is semantically unsafe and may not be used as the parent of further canonical allocation.

The canary projection of `690 effective active` is not authority. Before publication it requires:

```text
native HOTELS_MASTER writer
→ atomic constrained DB repair
→ DB↔HOTELS_MASTER alias/active PK reconciliation
→ Intelligence active PK-set recomputation
→ Operational Graph node/edge recomputation
→ scheduler/checkpoint/metrics/transition repair
→ restore/replay/idempotency gauntlet
→ ASR-1.0 EXACT across all affected planes
→ COMPLETE_AUTHORITY
```

## Artifacts outside the public repository

The constrained SQLite canary, restore copy, full proof report and hashes are persisted to the project recovery surfaces. Operational binaries remain outside this public repository.

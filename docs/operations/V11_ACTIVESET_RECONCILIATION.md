# V11 Active-Set Reconciliation

> **HISTORICAL RECONCILIATION RECORD — NOT CURRENT AUTHORITY.**  
> This file preserves lineage for the V11 active-set correction. Statements such as “next parent” were true only at the time of the run and are superseded by later authority-eligible state. Current execution MUST reconstruct authority via WOP + live control plane + latest authority-eligible manifest + `STATE.md`.

Run: `RUN-2026-08-25-1718-CANONICAL-SUPERSESSION-RECONCILE`

## Why

The control plane had conflated physical hotel IDs with active canonical entity count. A newer constrained identity registry resolved four physical IDs as duplicate aliases.

## Historical result

```text
physical lineage rows: 677
superseded aliases: 4
active canonical entities: 673
identity registry rows: 673
SQLite integrity: ok
FK violations: 0
restore: PASS
send_allowed: 0
next physical ID at that time: H-0678
```

Mappings:

```text
H-0610 -> H-0656
H-0624 -> H-0639
H-0629 -> H-0638
H-0630 -> H-0640
```

No physical ID was deleted or reused. Alias lineage remains explicit and excluded from active canonical coverage.

## Historical V11 lineage

V11 was introduced to remove an operational ambiguity in the then-current constrained lineage.

Historical V11 SHA-256:

`10157eacf4a180ca2781b9b68bbf605c13b7db89282eab2928cb791ec5b1b283`

**Do not use V11 as a current parent merely because this file names it.** Parent selection is a runtime authority decision under `docs/operations/WAVE_OPERATING_PROTOCOL.md`.
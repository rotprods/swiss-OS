# V11 Active-Set Reconciliation

Run: `RUN-2026-08-25-1718-CANONICAL-SUPERSESSION-RECONCILE`

## Why

The control plane had conflated 677 physical hotel IDs with active canonical entity count. A newer constrained identity registry resolved four physical IDs as duplicate aliases.

## Result

```text
physical lineage rows: 677
superseded aliases: 4
active canonical entities: 673
identity registry rows: 673
SQLite integrity: ok
FK violations: 0
restore: PASS
send_allowed: 0
next physical ID: H-0678
```

Mappings:

```text
H-0610 -> H-0656
H-0624 -> H-0639
H-0629 -> H-0638
H-0630 -> H-0640
```

No physical ID was deleted or reused. Graph alias nodes remain for audit lineage and are excluded from active coverage.

## V11 lineage

V11 is a monotonic wrapper over the newest constrained active-set state and removes the operational ambiguity created by a later-generated `V4` existing alongside an older `V10` naming sequence.

V11 SHA-256:

`10157eacf4a180ca2781b9b68bbf605c13b7db89282eab2928cb791ec5b1b283`

The next canonical transaction must use V11 as its sole constrained parent.

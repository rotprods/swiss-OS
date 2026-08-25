# STATE — LIVE HANDOFF POINTER

Last reconciliation used for this repository state: **2026-08-25**.

## Authoritative state correction

The latest constrained manifest currently available is newer than the `677 canonical` prose in Sheets/repository bootstrap and distinguishes **physical rows** from **active canonical entities**:

- physical HOTELS rows: **677**
- `SUPERSEDED_DUPLICATE` IDs: `H-0610`, `H-0624`, `H-0629`, `H-0630`
- active canonical entities: **673**
- identity registry rows: **673**
- SQLite integrity: `ok`
- foreign-key violations: `0`
- CP-0650: COMPLETE at 673 active canonical
- CP-0750: ACTIVE, effective frontier **673 / 750**
- outbound: `CLOSED`
- `send_allowed = 0`

## Control-plane drift

`GOAL_STATE`, Graph/Intelligence counters and earlier repository prose still expose `677` as canonical/current coverage. Under the project authority order this is a **drift to reconcile**, not permission to silently prefer the higher counter.

Until the superseded IDs are propagated through Sheets/Graph/Intelligence metrics:

```text
ACTIVE_CANONICAL = 673
PHYSICAL_ROWS = 677
CONTROL_PLANE_CANONICAL_COUNTER = 677  # stale / needs reconciliation
```

The next safe operational action is therefore **canonical-state reconciliation of the four superseded duplicate IDs**, then resume CP-0750 discovery from the reconciled active frontier.

## Source precedence

```text
PHYSICAL + CONSTRAINED DATA
> live Sheets registries / active control plane
> latest validated operational manifest
> repository STATE.md
> release prose / handoffs
> legacy documentation
```

Drift must be emitted and repaired; never silently normalized.

## Repository role

This file is a public-safe handoff pointer. Live hotel rows, people, channels, evidence and SQLite payloads remain outside this public repository.

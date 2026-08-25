# STATE — LIVE HANDOFF POINTER

Last Drive reconciliation used for repository bootstrap: **2026-08-25**.

## Authoritative live state

- Release contract: `V6.5-G0800-MAXIMUM-READINESS`
- `G-0001`: ACTIVE
- `G-0500`: ACTIVE_SCALE_WAVE_B
- `CP-0750`: **677 / 750 ACTIVE**
- Current entity epoch: `HS_ENTITY_EPOCH_2026-08-23_E3`
- Last canonical batch: `RUN-2026-08-23-1915-CP0750-BATCH03`
- New canonical IDs in Batch03: `H-0668..H-0677`
- Next canonical task: `SV2-058 / CP0750-BATCH04`
- Intelligence coverage: **677 / 677**
- Graph V2 coverage: **677 / 677**
- `CP-0800-CURRENT-L4`: **105 / 677 ACTIVE**
- `G-0700`: **0 / 2050 L9**
- `G-0600`: `BLOCKED_USER_INPUT`, 0/4 lanes
- Outbound: `CLOSED`
- `send_allowed = 0`

## Source precedence

When this file conflicts with live operational state, use:

```text
PHYSICAL + CONSTRAINED DATA
> live Sheets registries / active control plane
> latest validated operational manifest
> repository STATE.md
> release prose / handoffs
> legacy documentation
```

Never silently resolve drift. Record it and repair the stale layer.

## Known quarantines

Entity-scoped contaminated routes remain excluded from unsafe downstream promotion until independently reconciled:

- `H-0039`
- `H-0136`
- `H-0658`

## Repository note

This file is intentionally a lightweight handoff pointer, not an operational mirror. Live hotel rows, people, channels, evidence and SQLite payloads stay outside this public repository.

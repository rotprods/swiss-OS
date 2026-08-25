# STATE — LIVE HANDOFF POINTER

Last material reconciliation: **2026-08-25T17:18:00+02:00**.

## Authoritative current state

- physical HOTELS lineage rows: **677**
- superseded duplicate IDs: `H-0610`, `H-0624`, `H-0629`, `H-0630`
- active canonical entities: **673**
- identity registry rows: **673**
- explicit alias merges: **4**
- CP-0750: **673 / 750 ACTIVE**
- next physical hotel ID: **H-0678**
- active Intelligence denominator: **673**
- active Graph V2 denominator: **673**
- current L4: **105 / 673**
- G-0700 L9: **0 / 2050**
- outbound: **CLOSED**
- `send_allowed = 0`

## Operational shadow

Current monotonic constrained parent:

`switzerland_job_os_operational_shadow_v11.sqlite`

Manifest:

`OPERATIONAL_DB_SHADOW_MANIFEST_V11.json`

V11 checks:

```text
integrity_check = ok
foreign_key_violations = 0
active_canonical_hotels = 673
identity_registry_rows = 673
alias_merge_rows = 4
sheet_physical_hotel_rows = 677
restore_test = PASS
next_physical_hotel_id = H-0678
id_reuse_allowed = false
send_allowed = 0
```

SHA-256:

`10157eacf4a180ca2781b9b68bbf605c13b7db89282eab2928cb791ec5b1b283`

## Resolved drift

The previous control plane counted all 677 physical IDs as active canonical. The constrained identity registry proved four physical IDs were duplicate aliases. The system now preserves those IDs for lineage while excluding them from active canonical, Intelligence and Graph metrics.

Alias lineage:

```text
H-0610 → H-0656
H-0624 → H-0639
H-0629 → H-0638
H-0630 → H-0640
```

Graph V2 retains the physical alias nodes as blocked/superseded and exposes explicit `ALIASES_TO` edges.

## Active execution frontier

`SV2-058 / CP0750-BATCH04`

Acquire a bounded 10–25 exact-current-T1 entity batch. Anti-join active canonical entities, alias IDs, domains, active tasks and quarantines. Allocate new physical IDs from `H-0678` upward. Never reuse superseded IDs.

77 active entities remain to CP-0750.

## Source precedence

```text
PHYSICAL + CONSTRAINED DATA
> live Sheets registries / active control plane
> latest validated operational manifest
> repository STATE.md
> release prose / historical handoffs
```

This repository stores public-safe executable contracts and handoff state only. Operational SQLite payloads, people/channels, candidate private data and raw evidence remain outside GitHub.

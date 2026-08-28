# ALIAS CROSS-PLANE RECOVERY — SWITZERLAND_JOB_OS

Version: **ACR-1.0**  
Status: **PRE-AUTHORITY HARD GATE**

## Purpose

ARR-1.0 deterministically repairs the constrained SQLite copy. ACR-1.0 validates that the accompanying `ASR_CROSS_PLANE_WRITESET_V1` is complete enough to repair every affected operational plane as one later WOP recovery transaction.

ACR validates a plan. It does not execute writes, infer the corrected active denominator, allocate H-IDs, advance authority or open outbound.

## Required coverage

A valid write-set binds one exact entity set across:

```text
constrained DB / ARR replay
HOTELS_V2
HOTEL_INTELLIGENCE_V1
GRAPH_NODES_V2 — HOTEL + INTEL
GRAPH_EDGES_V2 — invalid ALIASES_TO removal + HAS_INTELLIGENCE restoration
ENTITY_RESOLUTION research-evidence preservation
append-only STATE_TRANSITIONS
observability + scheduler recomputation
```

The plan must also bind:

- an observed Sheets revision;
- a durable rollback copy;
- stable PK/entity-key/edge-ID resolution at commit time;
- exact invalid alias targets;
- deterministic repaired SQLite SHA observation;
- `active_denominator_after_replay = null` until cross-plane reconciliation;
- historical revision-backed Intelligence restoration to `L1 / CANONICAL_INDEXED_RECONCILE_SEED` where that is the proved prior state;
- ASR, DB↔Sheets, restore/replay/idempotency and production-gauntlet gates.

## Executable validator

```bash
python -m swiss_os.alias_cross_plane docs/state/ISSUE_89_CROSS_PLANE_WRITESET.json
```

Success emits:

```text
cross_plane_write_set_state = EXACT
cross_plane_write_set_valid = true
authority_advanced = false
h_id_allocations = 0
outbound_opened = false
send_allowed = 0
```

## Concurrency and authority

An `EXACT` result is not live authorization. Immediately before mutation, the recovery wave must reread Git ancestry, the constrained parent, the current Sheet revision and every affected stable key. Any drift invalidates the plan and returns to `RECOVERY_RECONCILE`.

The repaired denominator is derived only after DB, HOTELS_MASTER, Intelligence, Operational Graph and observability agree and ASR-1.0 returns `EXACT`.

```text
OUTBOUND = CLOSED
send_allowed = 0
```

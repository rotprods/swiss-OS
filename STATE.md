# STATE — LIVE HANDOFF POINTER

Last full control-plane reconciliation: **2026-08-27T17:12:40+02:00**.

## Authoritative current state

- entity epoch: `HS_ENTITY_EPOCH_2026-08-25_E4`
- physical HOTELS lineage rows: **690**
- superseded duplicate aliases: **4**
- active canonical entities: **686**
- CP-0750: **686 / 750 ACTIVE**
- remaining to CP-0750: **64**
- next physical hotel ID: **H-0691**
- active Intelligence denominator: **686**
- active Graph V2 denominator: **686**
- current L4: **105 / 686**
- hotels below L4: **581**
- G-0700 L9: **0 / 2050**
- outbound: **CLOSED**
- `send_allowed = 0`

## E4 delta

Batch04 admitted `H-0678..H-0690` as 13 current T1 **regional-association-support** entities. Their evidence scope is explicit and is **not** mislabeled as exact member-directory detail.

All thirteen are L1 Intelligence seeds with unresolved non-identity dimensions. They therefore increase canonical/Graph/Intelligence coverage but do not increase L4 or L9 completion.

## Operational shadow

Current constrained parent referenced by the authoritative E4 control plane:

`OPERATIONAL_DB_SHADOW_MANIFEST_V12`

The E4 snapshot records DB-first canary/restore PASS. Subsequent canonical commits must still independently satisfy integrity, FK, semantic, replay, mirror and active-set reconciliation gates.

## Alias lineage

Physical IDs remain immutable and are never reused:

```text
H-0610 → H-0656
H-0624 → H-0639
H-0629 → H-0638
H-0630 → H-0640
```

## Active execution frontier

`SV2-059 / CP0750-BATCH05`

Acquire a bounded 10–25 current T1 entity batch from `H-0691` onward. Prefer exact member/entity detail. Alternate current T1 support may promote only when source scope is explicit and constrained DB + mirror + graph + observability gates pass. Weaker evidence remains staged.

`SV2-058` is terminalized after the 13-entity E4 Batch04 commit so future batches cannot be absorbed into an unbounded task.

## Source precedence

```text
PHYSICAL + CONSTRAINED DATA
> live Sheets registries / active control plane
> latest validated operational manifest
> repository STATE.md
> release prose / historical handoffs
```

GitHub stores public-safe executable contracts and handoff state only. Operational SQLite payloads, people/channels, candidate private data and raw evidence stay outside the public repository.

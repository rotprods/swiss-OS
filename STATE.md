# STATE — LIVE HANDOFF POINTER

Last full control-plane reconciliation: **2026-08-27T17:12:40+02:00**.  
Latest constrained physical verification: **2026-08-27T18:13:00+02:00**.

## Authoritative current state

The authoritative state remains the last fully synchronized Drive/Sheets/Graph/control-plane commit:

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

No later canary may advance these counters until DB, Sheets mirror, Graph/Intelligence, metrics, scheduler, checkpoints and persistent handoff all reconcile.

## E4 delta

Batch04 admitted `H-0678..H-0690` as 13 current T1 **regional-association-support** entities. Their evidence scope is explicit and is **not** mislabeled as exact member-directory detail.

All thirteen are L1 Intelligence seeds with unresolved non-identity dimensions. They increase canonical/Graph/Intelligence coverage but do not increase L4 or L9 completion.

## Operational shadow recovery

The E4 control plane referenced `OPERATIONAL_DB_SHADOW_MANIFEST_V12`, but no physical V12 SQLite/manifest artifact was discoverable in Drive during the 2026-08-27 recovery pass.

A deterministic constrained **V13** was therefore rebuilt from the last persisted V9 plus the authoritative E3/E4 hotel delta and the four explicit alias mappings.

Verified V13 state:

```text
physical hotels = 690
active canonical = 686
aliases = 4
integrity_check = ok
foreign_key_violations = 0
ID gaps = 0
active normalized name+city duplicates = 0
alias targets = valid
idempotency replay delta = 0
send_allowed = 0
```

V13 SHA-256:

`0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5`

V13 is the latest physically verified constrained parent for subsequent canonical work.

## V14 canary — validated, not authoritative

`SV2-059` produced a local constrained canary containing three exact-current-detail candidates:

```text
H-0691  Hotel City Inn — Basel
H-0692  Hotel City Zürich — Zürich
H-0693  Hotel City Lugano - Hospitality & design — Lugano
```

Candidate V14 state if committed:

```text
physical hotels = 693
active canonical = 689
aliases = 4
integrity_check = ok
foreign_key_violations = 0
ID gaps = 0
active normalized name+city duplicates = 0
active canonical-domain duplicates = 0
idempotency replay delta = 0
send_allowed = 0
external_actions = 0
```

SQLite backup restore was validated by **logical equivalence**, not binary-file SHA equality. The restore has identical schema and zero bidirectional table-content differences across all 63 operational tables. SQLite physical page layout is not an authority invariant.

**V14 is NOT promoted.** During the run, the Google Drive/Sheets connector became unavailable for new writes. Under `INV-025`, a DB-only candidate state cannot become authoritative without Sheets mirror, Graph/Intelligence, observability, scheduler and checkpoint synchronization.

Therefore the authoritative frontier remains **686 / H-0691**, not 689 / H-0694.

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

Resume from the authoritative **H-0691** frontier. Before promoting any staged V14 entity, re-read the live Drive control plane and anti-join the full active set. Then execute:

```text
DB CANARY / CONSTRAINED COMMIT
→ SHEETS PK MIRROR
→ INTELLIGENCE L1
→ GRAPH V2
→ ENTITY EPOCH
→ METRICS / HEALTH / SLO
→ CHECKPOINT / SCHEDULER
→ STATE TRANSITIONS / RUN LOG
→ PERSISTENT HANDOFF
```

If another agent has already committed H-0691+ in Drive, the local V14 allocation is stale and must be reallocated after anti-join. No ID reservation exists without the synchronized commit.

## Restore semantics

Restore PASS means logical operational equivalence:

- both databases pass `integrity_check`;
- both have zero FK violations;
- schema objects match;
- table sets and row counts match;
- `source EXCEPT restore = ∅` and `restore EXCEPT source = ∅` for every operational table.

Binary SHA equality is useful for transfer verification of the same artifact, but is **not** required for a valid SQLite backup/restore because physical page serialization may differ.

## Source precedence

```text
PHYSICAL + CONSTRAINED DATA
> live Sheets registries / active control plane
> latest validated operational manifest
> repository STATE.md
> release prose / historical handoffs
```

GitHub stores public-safe executable contracts and handoff state only. Operational SQLite payloads, people/channels, candidate private data and raw evidence stay outside the public repository.

# STATE — LIVE HANDOFF POINTER

Last full control-plane reconciliation: **2026-08-27T17:12:40+02:00**.  
Latest constrained local verification: **2026-08-27T18:13:00+02:00**.

## Authoritative current state

The authoritative state remains the last fully synchronized Drive/Sheets/Graph/control-plane commit:

- entity epoch: `HS_ENTITY_EPOCH_2026-08-25_E4`
- physical HOTELS lineage rows: **690**
- superseded duplicate aliases: **4**
- active canonical entities: **686**
- CP-0750: **686 / 750 ACTIVE**
- remaining to CP-0750: **64**
- next authoritative physical hotel ID: **H-0691**
- active Intelligence denominator: **686**
- active Graph V2 denominator: **686**
- current L4: **105 / 686**
- hotels below L4: **581**
- G-0700 L9: **0 / 2050**
- outbound: **CLOSED**
- `send_allowed = 0`

No canary advances these counters until DB, Sheets mirror, Graph/Intelligence, metrics, scheduler, checkpoints and persistent handoff reconcile under `INV-025`.

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

V13 remains the latest physically verified constrained **authoritative parent** until the next full control-plane commit.

## SV2-059 Batch05 local canary — complete, not authoritative

The bounded Batch05 local canary now contains **13 exact member/entity-detail candidates**:

```text
H-0691  Hotel City Inn — Basel
H-0692  Hotel City Zürich — Zürich
H-0693  Hotel City Lugano - Hospitality & design — Lugano
H-0694  Hotel Continental — Zermatt
H-0695  Hotel Crowne Plaza — Zürich
H-0696  Hotel Crusch Alba — Zernez
H-0697  Hotel Crusch Alva — Zuoz
H-0698  Hotel Crystal — Interlaken
H-0699  Hotel Crystal — St. Moritz
H-0700  Hotel Crystal Engelberg — Engelberg
H-0701  Hôtel d'Allèves — Genève
H-0702  Hotel Daniela — Zermatt
H-0703  Hotel David 22 — St. Gallen
```

The first three originated in V14; V15 added ten more exact-detail entities. The local database explicitly marks these rows and their migration records as **CANARY**, not authoritative canonical state.

Candidate V15 state if a later synchronized commit revalidates the same allocation:

```text
physical rows = 703
candidate entities excluding 4 aliases = 699
Batch05 exact candidates = 13
integrity_check = ok
foreign_key_violations = 0
physical ID gaps = 0
normalized name+city duplicates = 0
non-empty canonical-domain duplicates = 0
idempotency replay new inserts = 0
external_actions = 0
send_allowed = 0
restore tables compared = 63
restore logical differences = 0
next ID if synchronized commit succeeds = H-0704
remaining to CP-0750 if synchronized commit succeeds = 51
```

V15 SQLite SHA-256:

`3aeeddfc6819c7ffd0ce8f118d3d08db0089ac42544eceb333d016dce6691c5f`

The restore artifact has a different physical SHA but zero logical differences across all 63 operational tables; binary page serialization is not the restore authority invariant.

### Field-level quarantine

HotellerieSuisse localized pages for **Hotel Crowne Plaza Zürich** exposed conflicting room counts. The entity itself remains exact-detail validated, while the conflicting room-count field is quarantined/omitted. Field disagreement must never invalidate an otherwise resolved identity or silently choose one value.

## Exact-detail reserve pool — no IDs reserved

After completing the 13-entity bounded canary, further discovery stays staged without physical-ID reservation while the Drive/Sheets authority plane is unavailable:

- `Hôtel D'Angleterre — Genève`: `READY_EXACT_CURRENT`; no name+city collision in V15.
- `Hotel Croix d'Or & Poste — Münster VS`: `STAGED_REFRESH_REQUIRED`; current directory presence corroborated but exact-detail crawl is older than the local freshness threshold.
- `Hotel Dakota — Meiringen`: `STAGED_REFRESH_REQUIRED`; same freshness rule.

No reserve-pool item owns `H-0704+`. Rehydrate live authority first.

## Why V15 is not promoted

During this execution, the Google Drive/Sheets write plane became unavailable. Under `INV-025`, DB-only work cannot become authoritative because the following chain has not been proven as one reconciled state:

```text
DB
→ SHEETS PK MIRROR
→ INTELLIGENCE L1
→ GRAPH V2
→ ENTITY EPOCH
→ METRICS / HEALTH / SLO
→ CHECKPOINT / SCHEDULER
→ STATE TRANSITIONS / RUN LOG
→ PERSISTENT HANDOFF
```

Therefore the authoritative frontier remains **686 / H-0691**. The local 699 candidate state is a validated acceleration artifact, not a canonical claim.

If another agent commits H-0691+ before the Drive plane is re-read, the local allocations must be discarded/reallocated after anti-join. No local canary reserves IDs.

## Alias lineage

Physical IDs remain immutable and are never reused:

```text
H-0610 → H-0656
H-0624 → H-0639
H-0629 → H-0638
H-0630 → H-0640
```

## Restore semantics

Restore PASS means logical operational equivalence:

- both databases pass `integrity_check`;
- both have zero FK violations;
- schema objects match;
- table sets and row counts match;
- `source EXCEPT restore = ∅` and `restore EXCEPT source = ∅` for every operational table.

Binary SHA equality remains appropriate for verifying transfer of the **same artifact**, but it is not required for a valid SQLite backup/restore because physical page serialization may differ.

The executable contract is implemented in `swiss_os.db.sqlite_logical_differences()` and covered by tests.

## Active execution frontier

`SV2-059 / CP0750-BATCH05`

The bounded local canary is complete. The next authoritative action is **not** another blind DB append. It is:

1. re-read live Drive/Sheets authority;
2. anti-join all 13 local candidates and the reserve pool against any intervening canonical IDs/names/domains/aliases;
3. reallocate physical IDs only from the live frontier;
4. perform the constrained DB commit;
5. complete the full synchronization chain above;
6. only then advance CP-0750.

## Source precedence

```text
PHYSICAL + CONSTRAINED DATA
> live Sheets registries / active control plane
> latest validated operational manifest
> repository STATE.md
> release prose / historical handoffs
```

GitHub stores public-safe executable contracts and handoff state only. Operational SQLite payloads, people/channels, candidate private data and raw evidence stay outside the public repository.

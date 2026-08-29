# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T19:24:00Z**. Current wave parent main SHA: **`625012ebb724365324118247fd098904bbcc1342`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

## Authority — unchanged / locked

```text
physical HOTELS rows            690
active canonical                690
persisted H-ID alias edges        0
ASR-1.0                         EXACT
HOTEL_INTELLIGENCE_V1           690 / 690
Graph HOTEL / INTEL / edges     690 / 690
next physical ID                H-0691 UNALLOCATED
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, ECV, SRR, SMO, RAGR, cache and canary remain non-authoritative. HOTELS_MASTER was reread this activation and H-0691 is absent.

## CRM universe / effective pre-authority source-mapping frontier

```text
source pages / records              172 / 2061
ACTIVE_MATCH / TRUE_MISSING          623 / 1438
base terminal mappings                    624
base RECONCILE_REQUIRED                  1437
cumulative SMO terminal deltas              14
effective terminal mappings                638
RECONCILE_REQUIRED                         1423
RAGR covered active canonicals              638
RAGR reverse gaps                            52
RAGR gaps with same-city candidate           37
RAGR gaps without same-city candidate        15
candidate records                           1438
candidate records SHA               34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0
ECV verified frontier              1438 / 1438
ECV remaining never verified          0
ECV pending requeue                   0
```

`effective terminal mappings=638` is the validated SMO-1.0 **pre-authority** frontier over base candidate SHA `2f9413318c410eb0f0443de260213d31e9ab2bdc1058581c0fa9c0340474aa27`. It does not mutate operational authority.

## Durable recovery inputs

- qualified member-directory fallback artifact `9700376482`: 2061 records, records SHA `62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`; qualified fallback only, **not** SSR-1.0 API equivalence.
- candidate export workflow `33266739167`, artifact `9718866661`, digest `d58c57c5a83cd2ff740f0ec900163f5c7aa795b032045cf9d30ffd194733465e`: 1438 records, SHA `34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0`.
- cumulative SMO overlay SHA `280b34924567f360af0122275493474ab61e59902ea2f50b95863f31e2fd1add`.
- HOTELS_MASTER Drive ID `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`.

## RAGR-1.0 — deterministic 52-gap queue materialized

The reverse authority/source coverage gate was rebuilt from the exact 2061-record source universe, a live 690-active canonical projection and 638 source→canonical terminal coverage rows (624 unique exact normalized name+city matches + 14 validated SMO deltas).

```text
source records SHA              62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2
catalog projection SHA          a0d9c97105f106b50a5636d21bb2d40d7333b60af6228b8c6ac8521d8aa1245b
terminal coverage SHA           b0cb512d56497fd90d52e2303c56e7de72d875314ab178de4685e24156564823
RAGR queue SHA                  1c75e431fc6aba869053e062cf95fc222d2cdddd60f0c05d2684ef21c05834bc
covered active canonicals       638 / 690
reverse gaps                    52
with same-city source candidate 37
without same-city candidate     15
```

The exact gap set is persisted in `docs/state/RAGR_REVIEW_QUEUE_52_33206402141.json`. RAGR remains review-only: suggestions reduce search space but encode no terminal decision, authority mutation, canonical reservation or deletion inference.

The highest-value next evidence batch is pinned to eight same-city identity variants: H-0001/Hotel Matthiol, H-0020/Grand Hotel Zermatterhof, H-0021/Hotel Alpenroyal, H-0025/Hotel Sonne, H-0453/Hotel Valaisia Crans-Montana, H-0685/Aspen alpin lifestyle, H-0687/Hotel Seepark Thun and H-0688/Hotel Alpenruhe. Candidate source keys and original offsets are durable in the RAGR attestation; they are **not mappings yet**.

CMRQ safe MATCH proposals are closed at the current 14-delta overlay. `MD-034c1c3b0f7ba9d69c80` ibis budget Zürich City West remains a distinct nonterminal `NEW_CANONICAL` candidate and no H-ID is reserved.

The `cwp-materialize-next` phase-transition fix from PR #251 is healthy on main; both repo-guard and CWP no-op workflow passed on merge SHA `625012ebb724365324118247fd098904bbcc1342`.

## NEXT — strict ECV reverify of RAGR high-confidence 8, then explicit SRR/SMO only

1. Stage the eight pinned RAGR source records through strict exact-current verification; do not pre-bind their H-IDs in the CMI packet.
2. Accept a MATCH_EXISTING review only when the exact-current item is terminal verified and same-property identity evidence is sufficient; otherwise keep the gap unresolved.
3. Recompute RAGR from the resulting overlay and continue bounded evidence waves over the remaining reverse gaps.
4. In parallel, continue CP-R01/CP-R02 toward a complete 2061-record SMC/SRR rebuild; no fuzzy auto-binding.
5. Keep ibis budget Zürich City West nonterminal until an authority-eligible `NEW_CANONICAL` transaction; never reserve H-0691 from staging.
6. Final authority promotion remains ineligible until source-resolution conservation and SSR-1.0 are both satisfied.

SSR-1.0 remains blocked on the missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. MEP fallback remains qualified member-directory + exact-current without claiming API equivalence. Issues #240, #239 and #14 remain the execution, resolver-safety and structured-source boundaries.

Drive recovery doc: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. Private review doc: `1Ktlvg04MbDrgZ0LD0wGYrpz65xTHBRyiNdD8KWLxNhk`. File Library remains cold recovery and may lag GitHub/Drive state.

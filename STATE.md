# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T19:06:00Z**. Current wave parent main SHA: **`0056c0f80b8c5a894ab4f32bac21353bafcfe025`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging/materialization/ECV/review/overlay/cache/canary remain non-authoritative. Native HOTELS_MASTER was reread this activation: H-0690 is present and H-0691 is absent.

## CRM universe / effective pre-authority source-mapping frontier

```text
source pages / records              172 / 2061
ACTIVE_MATCH / TRUE_MISSING          623 / 1438
base terminal mappings                    624
base RECONCILE_REQUIRED                  1437
cumulative SMO terminal deltas              13
effective terminal mappings                637
RECONCILE_REQUIRED                         1424
exact name+city reverse-gap metric           66
overlay-aware reverse-gap candidates         53
candidate records                           1438
candidate records SHA               34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0
ECV verified frontier              1438 / 1438
ECV remaining never verified          0
ECV pending requeue                   0
```

`effective terminal mappings=637` is the validated SMO-1.0 pre-authority source-mapping frontier over pinned base candidate SHA `2f9413318c410eb0f0443de260213d31e9ab2bdc1058581c0fa9c0340474aa27`; it is not an operational authority mutation. The exact-name+city reverse-gap metric remains 66 by definition and is overlay-insensitive. The overlay-aware residual is 53 because 13 of those reverse-gap identities now have validated pre-authority MATCH_EXISTING mappings.

## Recovery inputs

Qualified member-directory fallback snapshot: Actions artifact `9700376482`, 2061 records, records SHA `62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`. This is coherent fallback evidence and is **not** SSR-1.0 API equivalence.

Current candidate export: workflow run `33266739167`, artifact `9718866661`, artifact digest `d58c57c5a83cd2ff740f0ec900163f5c7aa795b032045cf9d30ffd194733465e`, 1438 records, records SHA `34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0`.

Current active canonical catalog: 690 rows, derived projection SHA `091a2b1d4f95bc0035135c848104666cf9fca5c4a9e1d691a8a6e16b20e52b99`.

## CMRQ → SRR/SMO wave 0002 — 10 additional safe matches terminalized pre-authority

CMRQ-1.0 remains a 16-source / 16-pair deterministic review queue with queue SHA `06d550e3be5bc12e32e67d2d89f6000e1b882b3e3bcacf4e049e4b851f79b11a`.

`docs/state/SOURCE_RESOLUTION_REVIEW_BATCH_0002_33206402141.json` now carries a cumulative 13-review `MATCH_EXISTING` packet: the prior 3 validated matches plus 10 additional exact-current, same-locality identity reviews. Every new item was recovered from its durable ECV Actions artifact and checked `CURRENT_DETAIL_VERIFIED`, HTTP 200, `name_match=true`, `city_match=true`, with pinned response SHA. Public identity corroboration was also attached for the new reviews, including official/property sources where available.

`docs/state/SOURCE_MAPPING_OVERLAY_SRR_BATCH_0002_33206402141.json` materializes the cumulative 13 deltas under SMO-1.0:

```text
overlay SHA                  16db2ef17ee66c49fbaba9a54a9ef4182fa14bf660994b44dcdab40c3e44c718
base terminal / reconcile    624 / 1437
terminal deltas               13
effective terminal/reconcile 637 / 1424
H-ID allocations               0
authority advanced          FALSE
OUTBOUND                    CLOSED
send_allowed                    0
```

CMRQ disposition after this wave: 13 MATCH_EXISTING identities are represented in the cumulative overlay; Grace La Margna / H-0088 was already terminal in the base exact mapping; ibis budget Zürich City West remains `NEW_CANONICAL` pre-authority and therefore unresolved with **no H-ID reservation**; La Couronne / H-0024 remains the only CMRQ MATCH proposal not yet added to the overlay because its item-level durable ECV evidence packet has not yet been recovered in this activation.

Meta Graph delta: `docs/state/META_GRAPH_DELTA_SRR_BATCH_0002_2026-08-29.json`.

## NEXT — recover La Couronne item evidence, then bounded RAGR

1. Recover or regenerate strict item-level exact-current evidence for `MD-ff70cabc95a4a2ea61a1` (`La Couronne | Hotel & Spa`, Zermatt) and, only if it passes the same evidence contract, extend the cumulative SMO overlay to 14 deltas.
2. Recompute overlay-aware reverse-gap candidates; a valid La Couronne match would move the residual from 53 to 52 while leaving the exact-name+city diagnostic metric at 66.
3. Execute bounded RAGR evidence review across the remaining reverse-gap candidates; no fuzzy auto-binding.
4. Harden/execute CP-R01/CP-R02 until ambiguous source records are explicitly classified and the full 2061-record SMC/SRR materialization is rebuilt and validated.
5. Keep ibis budget Zürich City West as a nonterminal `NEW_CANONICAL` candidate until an authority-eligible transaction; never reserve `H-0691` from staging.
6. Final authority promotion remains ineligible until all source-resolution gates and SSR-1.0 are satisfied.

SSR-1.0 remains blocked on the missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. MEP fallback remains qualified member-directory + exact-current without claiming API equivalence. Issue #240 is the execution program; issues #239 and #14 govern resolver safety and source-scope completion.

Drive recovery doc: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. HOTELS_MASTER: `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`. Private review doc: `1Ktlvg04MbDrgZ0LD0wGYrpz65xTHBRyiNdD8KWLxNhk`. File Library remains cold recovery and may lag GitHub/Drive state.

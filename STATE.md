# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T19:14:00Z**. Current wave parent main SHA: **`ce9c2e194dce02c345e221d14120eebb2855d854`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging/materialization/ECV/review/overlay/cache/canary remain non-authoritative. Native HOTELS_MASTER was reread in this activation: H-0024 is `Hotel La Couronne`, Zermatt, official website `https://www.hotel-couronne.ch`; H-0691 remains absent.

## CRM universe / effective pre-authority source-mapping frontier

```text
source pages / records              172 / 2061
ACTIVE_MATCH / TRUE_MISSING          623 / 1438
base terminal mappings                    624
base RECONCILE_REQUIRED                  1437
cumulative SMO terminal deltas              14
effective terminal mappings                638
RECONCILE_REQUIRED                         1423
exact name+city reverse-gap metric           66
overlay-aware reverse-gap candidates         52
candidate records                           1438
candidate records SHA               34d9aa9cfa4fe896bf1dbf2e135b847101904644d16bba0
ECV verified frontier              1438 / 1438
ECV remaining never verified          0
ECV pending requeue                   0
```

`effective terminal mappings=638` is a validated SMO-1.0 **pre-authority overlay** over pinned base SMC candidate SHA `2f9413318c410eb0f0443de260213d31e9ab2bdc1058581c0fa9c0340474aa27`. It does not mutate operational authority. The exact-name+city reverse-gap diagnostic stays 66 by definition; the overlay-aware residual is now 52.

## Recovery inputs

Qualified member-directory fallback snapshot: Actions artifact `9700376482`, 2061 records, records SHA `62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`. It is coherent fallback evidence and is **not** SSR-1.0 API equivalence.

Current candidate export: workflow run `33266739167`, artifact `9718866661`, artifact digest `d58c57c5a83cd2ff740f0ec900163f5c7aa795b032045cf9d30ffd194733465e`, 1438 records, records SHA `34d9aa9cfa4fe896bf1dbf2e135b847101904644d16bba0`.

Current active canonical catalog: 690 rows, derived projection SHA `091a2b1d4f95bc0035135c848104666cf9fca5c4a9e1d691a8a6e16b20e52b99`.

## La Couronne ECV recovery — terminal green

The single-record exact-current re-verification packet for `MD-ff70cabc95a4a2ea61a1` (`la couronne | hotel & spa`, Zermatt) completed green:

```text
Actions run                         33270154075
job                                 99147080326
artifact                            9719850886
artifact ZIP SHA256                 de71b2921c895d753a2facaa788f36ca97e7913d9ce86c01eb611d2ee81246f7
normalized ECV packet SHA256        af3b4ed6ee2dc6a0d62e1634a4ee033133f822d9635232212864178ca7637809
raw packet SHA256                   963f5c30a4ba37b4325a83dc0d166d7e49b5c0e693cc96013d29fd49362cb75e
response SHA256                     d17a9dff160ca11d7603b66484e51992fef0f2c6a30d9a7dd2bb8439005cb873
HTTP / name / city                  200 / true / true
verification_state                  CURRENT_DETAIL_VERIFIED
provider record changes             0
validator violations                0
```

The current official property site independently corroborates `Hotel la couronne` at Kirchstraße 17, CH-3920 Zermatt. This evidence is sufficient for the existing explicit CMRQ proposal to be applied through SRR/SMO as a pre-authority source mapping to `H-0024`; it is not an authority mutation.

## CMRQ → SRR/SMO wave 0003 — all 14 safe MATCH_EXISTING overlays complete

`docs/state/SOURCE_RESOLUTION_REVIEW_BATCH_0003_33206402141.json` carries the cumulative 14 evidence-backed `MATCH_EXISTING` reviews. `docs/state/SOURCE_MAPPING_OVERLAY_SRR_BATCH_0003_33206402141.json` materializes them through SMO-1.0:

```text
overlay SHA                  50d32c180bfa5b16643df8bcfb24b0cf64e5dea513067096e79c2145fbc02647
base terminal / reconcile    624 / 1437
terminal deltas               14
effective terminal/reconcile 638 / 1423
H-ID allocations               0
authority advanced          FALSE
OUTBOUND                    CLOSED
send_allowed                    0
```

CMRQ disposition is now closed for `MATCH_EXISTING`: 14 proposal identities are represented in the cumulative overlay, Grace La Margna / H-0088 was already terminal in the base exact mapping, and ibis budget Zürich City West (`MD-034c1c3b0f7ba9d69c80`) remains `NEW_CANONICAL` pre-authority with **no H-ID reservation**.

Meta Graph delta: `docs/state/META_GRAPH_DELTA_SRR_BATCH_0003_2026-08-29.json`.

## NEXT — bounded RAGR across 52, then full SMC/SRR materialization

1. Materialize the exact source artifact, E4/690 canonical projection and **effective 638-row terminal coverage** bound to their hashes.
2. Execute RAGR-1.0 over the 52 overlay-aware reverse gaps; use same-city suggestions only to reduce review space. No fuzzy auto-binding.
3. Persist a private evidence-backed reverse-gap queue/review packet and public-safe counts/hashes.
4. Apply only independently demonstrated terminal identities through SRR/SMO; treat source-directory absence as non-deletion evidence.
5. Rebuild and validate the full 2061-record SMC/SRR materialization against the pinned source/canonical/evidence lineage. `RECONCILE_REQUIRED` must reach zero before source-resolution completion.
6. Keep ibis budget Zürich City West nonterminal until an authority-eligible transaction; never reserve `H-0691` from staging.
7. SSR-1.0 remains blocked on the absent discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. Continue the qualified member-directory + exact-current MEP fallback without claiming API equivalence.
8. Authority promotion remains forbidden until source-resolution, SSR-1.0 and cross-plane exact reconciliation gates are all satisfied.

Drive recovery doc: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. HOTELS_MASTER: `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`. Private review doc: `1Ktlvg04MbDrgZ0LD0wGYrpz65xTHBRyiNdD8KWLxNhk`. File Library remains cold recovery and may lag GitHub/Drive state.

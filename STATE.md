# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-08-31 current-source entity-resolution B03**. Verified bootstrap main parent: **`bc33616bbb7964c2dac2d2783f3506a4c04c4438`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

## Authority — unchanged / locked

```text
physical HOTELS rows            690
active canonical                690
persisted H-ID alias edges        0
next physical ID                H-0691 UNALLOCATED
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Live Drive `HOTELS_V2` was re-read through row 691 during this activation: `H-0690` is the physical frontier and `H-0691` is absent/unallocated. No staging, cache, canary, CI artifact, candidate export, SRR/ECV result or source crawl can become authoritative or advance this authority.

## Current coherent source universe

```text
HotellerieSuisse snapshot        HS-MEMBER-DE-33339392661
GitHub Actions run              33339392661
artifact                        9740219406
records / pages                 2061 / 172
coverage_complete               TRUE
source records SHA256           b16fdb63a01149e10feb4d506f38301644b73a612f898ce72567ec4fa92da404
terminal source mappings         658
unique canonical targets         656
RECONCILE_REQUIRED              1403
reverse authority source gaps     34
```

The earlier `HS-MEMBER-DE-33206402141` capture remains historical lineage only. Current coherent-source candidate continuity is fully accounted: 1436 exact unchanged identities plus two changed Gonten identities. Historical completed prioritized SRR/RAGR work remains monotonic and non-authoritative.

## Entity-resolution frontier

```text
historical candidate records                    1438
candidate lineage accounted                     1438 / 1438
ECV verified frontier                           1438 / 1438
ECV remaining never verified                    0
prior >=0.60 review                              20 / 20
prior 0.50–0.599999 review                       46 / 46
prior lower49 ordinary review                    47 / 47
lower49 typed SRR materialized                   47 / 47
RAGR evidence-classified                         34 / 34
cumulative NEW_CANONICAL preauthority             144
historical <0.35 previously unreviewed tail     1289
zero-same-city conservative sub-lane             485
current <0.35 reviewed cumulative                 30
current <0.35 B03 reviewed                        10
current <0.35 B03 NEW_CANONICAL preauthority      10
historical <0.35 tail remaining                 1259
zero-same-city lane remaining                    455
H-ID allocations                                   0
canonical ID reservations                          0
```

`docs/state/CRM_CURRENT_UNRESOLVED_LT350_B03_2026-08-31.json` records the third bounded current-source continuation. Ten more deterministic zero-same-city records were independently verified and cross-city collision reviewed. All ten are `NEW_CANONICAL_PREAUTH`, remain `RECONCILE_REQUIRED`, and create no terminal mapping or authority effect. `Weinhaus am Bach - Landhotel Hirschen` is explicitly handled under EGR-1.0 as an accommodation component of Landhotel Hirschen Erlinsbach; the parent/component relationship is preserved as metadata and is not converted into an alias merely from shared operator/property context.

## Capability / provider frontier

```text
GitHub read/write/branch/PR/CI       YES
GitHub Actions artifacts/logs        YES
Drive native Sheets read/write       YES
web current-source research          YES
File Library read                    YES
File Library write                   NO
discover.swiss runtime key           ABSENT
capture-valid discover manifest      ABSENT
durable DB-first E4 egress           BLOCKED_FILE_REFERENCE_DO_NOT_REPEAT
```

The coherent HotellerieSuisse source keeps provider-neutral entity resolution productive. Structured discover.swiss SSR-1.0 is an optional accelerator only when a runtime subscription credential and capture-valid manifest become available. Do not retry the blocked generated-file egress family.

## Open P0 / highest-value safe bottleneck

`CRM_UNIVERSE_COMPLETE` remains **FALSE** because **1403 current coherent source records remain `RECONCILE_REQUIRED`**. Preacthority `NEW_CANONICAL` dispositions deliberately do not reduce that terminal mapping count or reserve IDs. The highest-value safe route is to keep typing the exact-current unresolved tail in bounded evidence-backed waves while authority remains locked.

## NEXT

Execute **`CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B04`** over:

```text
MD-0ec9184e0553996c8017
MD-11392326bb8d2e36b225
MD-12012a3229867154fec7
MD-12981db89c28b8b3af89
MD-12ddaa1053593368724c
MD-13927887bbb57d617e5e
MD-139b78cdebb6cec44ad5
MD-147ce42ea282ff9d8373
MD-14b893f819ede5ee43f9
MD-14f0349e0f07cd0d3ae0
```

Continue exact current-source identities from the previously unreviewed `<0.35` lineage tail, prioritizing the conservative zero-same-city lane. Require current independent evidence and cross-city collision/granularity review. Similarity may rank review order only; fuzzy autobind is forbidden. Never reserve/allocate H-IDs from staging, never create authority from review/cache/canary state, and keep `OUTBOUND=CLOSED` / `send_allowed=0`.

Recovery inputs and exact blockers are persisted in `docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B03.json` and `docs/handoffs/META_20260831_CRM_CURRENT_LT350_B03.md`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

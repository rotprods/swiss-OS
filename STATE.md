# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T19:33:00Z**. Current wave parent main SHA: **`f099fce7ae823a55c2c9156003b7ac8c9b16bd7d`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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
cumulative SMO terminal deltas              22
effective terminal mappings                646
RECONCILE_REQUIRED                         1415
RAGR covered active canonicals              646
RAGR reverse gaps                            44
RAGR gaps with same-city candidate           29
RAGR gaps without same-city candidate        15
candidate records                           1438
candidate records SHA               34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0
ECV verified frontier              1438 / 1438
ECV remaining never verified          0
ECV pending requeue                   0
```

`effective terminal mappings=646` is the validated SMO-1.0 **pre-authority** frontier over base candidate SHA `2f9413318c410eb0f0443de260213d31e9ab2bdc1058581c0fa9c0340474aa27`; it does not mutate operational authority.

## Durable recovery inputs

- qualified member-directory fallback artifact `9700376482`: 2061 records, records SHA `62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`; qualified fallback only, **not** SSR-1.0 API equivalence.
- candidate export workflow `33266739167`, artifact `9718866661`, digest `d58c57c5a83cd2ff740f0ec900163f5c7aa795b032045cf9d30ffd194733465e`: 1438 records, SHA `34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0`.
- cumulative SMO overlay SHA `7a98c1b34da7bc996ceac31b1f236ae8aa18657dfba201f3036fcc0b1fd3d4b2`.
- RAGR terminal coverage SHA `594c6167d1984bbe78f25241795103c5c602a248a3520d8591faa1484153577d`.
- RAGR-44 queue SHA `5f1d4d828292dc7718f388377e538780f72142f21a64e2ed9c63f7a181cc485d`.
- HOTELS_MASTER Drive ID `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`.

## Wave 0004 — RAGR high-confidence 8 verified and terminalized pre-authority

Strict exact-current workflow run `33270992647`, artifact `9720099550`, artifact digest `c075b2862c46b5e4d3ad3419207662578a830b368e173cdcca615192ebc037ff`, packet SHA `9cca54e884971e3a71fe21f387d2f83395f7d1ca75f8faf0160c462ecfee30cf` completed **8/8 CURRENT_DETAIL_VERIFIED**. Every item returned HTTP 200 with `name_match=true`, `city_match=true`, provider-change count 0, and a pinned response SHA.

The eight identity reviews were additionally corroborated against current official/public property identity evidence and are now explicit SRR-1.1 `MATCH_EXISTING` reviews only:

- H-0001 ← Hotel Matthiol / Matthiol current property identity.
- H-0020 ← Grand Hotel Zermatterhof; the canonical group suffix is corroborated by the official property/group page.
- H-0021 ← Hotel Alpenroyal, Zermatt.
- H-0025 ← Hotel Sonne, Zermatt.
- H-0453 ← Valaisia Crans-Montana; current Faern rebrand identity corroborated.
- H-0685 ← Aspen Alpin Lifestyle Hotel, Grindelwald.
- H-0687 ← Hotel Seepark Thun.
- H-0688 ← Hotel Alpenruhe / Vintage Design Hotel, Wengen.

Durable files:
- `docs/state/ECV_BATCH_0003_SUB0001_RESULT.json`
- `docs/state/SOURCE_RESOLUTION_REVIEW_BATCH_0004_33206402141.json`
- `docs/state/SOURCE_MAPPING_OVERLAY_SRR_BATCH_0004_33206402141.json`
- `docs/state/RAGR_REVIEW_QUEUE_44_33206402141.json`

Cumulative overlay:

```text
overlay SHA                  7a98c1b34da7bc996ceac31b1f236ae8aa18657dfba201f3036fcc0b1fd3d4b2
base terminal / reconcile    624 / 1437
terminal deltas               22
effective terminal/reconcile 646 / 1415
H-ID allocations               0
authority advanced          FALSE
OUTBOUND                    CLOSED
send_allowed                    0
```

RAGR was recomputed over 646 unique covered canonicals: **44 reverse gaps remain**, 29 with same-city source candidates and 15 requiring locality/global identity recovery. RAGR remains review-only and cannot create terminal mappings by itself.

CMRQ is closed for all safe MATCH proposals. `MD-034c1c3b0f7ba9d69c80` ibis budget Zürich City West remains a distinct nonterminal `NEW_CANONICAL` candidate and **no H-ID is reserved**.

## NEXT — strict ECV of seven locality/name variants, then explicit SRR only

Pinned evidence-only review candidates:

1. H-0002 Hotel Europa Suites AG ← `MD-fed86d7933175b3cb112` Hotel Europa Suites, Champfèr; locality is a subset of `Champfèr / St. Moritz`.
2. H-0681 Seehotel Wilerbad Seminar & Spa ← `MD-70fee4f734bf530fb6fd` Seehotel Wilerbad, Wilen (Sarnen).
3. H-0063 Appenzeller Huus, Huus Quell ← `MD-418c10f59064a67a4ffb` HUUS QUELL, Gonten; do **not** bind the sibling Huus Bären/Löwen suggestions.
4. H-0474 Hotel Schweizerhof, Sils Maria, a Faern Collection Hotel ← `MD-615a31fb4402ea4abf2e` Hotel Schweizerhof, Sils/Segl Maria.
5. H-0478 Hôtel-Restaurant Les Cernets ← `MD-1e66aa8d213855517131` Hôtel Les Cernets “Val-de-Travers”, Les Verrières.
6. H-0652 Sedartis Swiss Quality Hotel ← `MD-d09653a62d86bff5e672` Lifestyle Hotel Sedartis Lake Zurich, Thalwil.
7. H-0060 Apart Hotel Wetterhorn ← `MD-466d0a46fe05df051926` Wetterhorn Apartments, Hasliberg Hohfluh.

Stage these without target H-IDs, run strict exact-current evidence, accept only independently corroborated same-property identities, recompute RAGR, and continue bounded waves. In parallel continue CP-R01/CP-R02 toward a complete 2061-record SMC/SRR rebuild; no fuzzy auto-binding.

SSR-1.0 remains blocked on the missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. MEP fallback remains qualified member-directory + exact-current without claiming API equivalence. Issues #240, #239 and #14 remain the execution, resolver-safety and structured-source boundaries.

Drive recovery doc: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. Private review doc: `1Ktlvg04MbDrgZ0LD0wGYrpz65xTHBRyiNdD8KWLxNhk`. File Library remains cold recovery and may lag GitHub/Drive state.

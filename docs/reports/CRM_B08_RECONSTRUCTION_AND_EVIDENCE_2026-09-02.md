# CRM B08 — deterministic reconstruction + current-evidence pre-review

Status: **RESEARCH_ONLY / NON-AUTHORITATIVE**  
Project: `SWITZERLAND_JOB_OS`  
Source snapshot: `HS-MEMBER-DE-33339392661` / Actions `33339392661` / artifact `9740219406` / 2061 records / 172 pages  
Authority observed for comparison: `HS_ENTITY_EPOCH_2026-08-25_E4` / 690 canonical / `H-0691_UNALLOCATED`  
Authority effect: **NONE**  
Terminal mapping delta: **0**  
H-ID allocations/reservations: **0 / 0**  
Outbound: **CLOSED** / `send_allowed=0`

## Why this report exists

PR #404 preserved a stale-but-semantically-useful B07 result and an exact recovery rule for B08: reconstruct the historical `<0.35 + zero-canonical-city` lineage from pinned artifacts, subtract reviewed B01..B07, and take the next ten in the original deterministic order. The PR was superseded because its coordination projections/ancestry became stale, not because B07 evidence was rejected.

This report recovers only the **read-only research facts**. It does not revive token7, stale `STATE/NEXT`, or any authority mutation.

## Reconstruction proof

Inputs used:

- current coherent source artifact `9740219406` (`HS-MEMBER-DE-33339392661`);
- Drive `HOTELS_V2` read-only E4 projection (690 rows);
- `SOURCE_RESOLUTION_REVIEW_UNRESOLVED_1403_33206402141.json` anti-join contract;
- `FULL_SOURCE_MAPPING_REBUILD_658_ATTESTATION_33206402141.json` exceptional terminal mappings;
- published B01/B02/B03/B07 selections as regression checkpoints.

Historical selection semantics:

1. normalize city using NFKD ASCII fold + lowercase/casefold + non-alphanumeric collapse;
2. evaluate candidate similarity only against canonical hotels in the same normalized city;
3. select the historical `<350000 ppm` band;
4. for this sublane require zero canonical rows in the normalized source city;
5. transfer unchanged identities to the current coherent source;
6. order by current source record key;
7. remove already reviewed B01..B07 keys.

The reconstructed current zero-city set contains 487 records versus the original 485 population because the current source is a later coherent snapshot. This does **not** affect the B08 prefix. Regression checks reproduce:

- B01 positions 1–10 exactly;
- B02 positions 11–20 exactly;
- B03 positions 21–30 exactly;
- B07 positions 61–70 exactly.

Therefore B08 is positions 71–80. Canonical JSON SHA-256 of the exact B08 key list: `c16a129aaf9a0aa02cc078afbd6e008e28ad83c18a685cac51da8680cdd12b99`.

## Exact B08 source keys

1. `MD-26e7c28b41181b3f61d3` — Herisau Swiss Quality Hotel — Herisau
2. `MD-27224563cb53290593d0` — Parkhotel Gunten — Gunten
3. `MD-27a401c5e00f91073a6c` — Tresa Bay Hotel — Ponte Tresa
4. `MD-27cb7654c25138f8566a` — Beatus Wellness- & Spa-Hotel — Merligen
5. `MD-281e7be2c117561bb57e` — See & Park Hotel Feldbach — Steckborn
6. `MD-284d08ed79e92ca9633a` — Restaurant & Hotel Rheingerbe — Stein am Rhein
7. `MD-2855ae3538687dc08390` — L'Auberge — Baulmes
8. `MD-29ca94166046fcd921f5` — lofthotel am Walensee — Murg
9. `MD-2b51224ee38c42763d77` — Los Lorentes Residences und Hotel du Cheval Blanc — Bulle
10. `MD-2c5ff2038682379edd93` — Hotel Restaurant Schönbühl — Hilterfingen

All ten have `same_city_canonical_count=0` under the E4 city projection, so no existing same-city target is proven.

## Current evidence + comparator/EGR pre-review

| Source key | Current evidence | Global comparator signal | Research-only pre-review |
|---|---|---|---|
| `MD-26e7c28b41181b3f61d3` | `https://hotelherisau.ch/` — active Hotel Herisau at Bahnhofstrasse 14, CH-9100 Herisau, 33 rooms and current booking/contact surfaces. | Max name Jaccard 600000 against multiple *Swiss Quality Hotel* properties in other cities. This is brand/consortium overlap, not property identity. | `NEW_CANONICAL_PREAUTH_CANDIDATE` + `BRAND_RELATIONSHIP_REVIEW` |
| `MD-27224563cb53290593d0` | `https://www.parkhotel-gunten.swiss/` — current Parkhotel Gunten, Seestrasse 90, CH-3654 Gunten, active hotel/spa/contact. | Max 333333 vs `H-0218 Parkhotel Beatenberg`; other Parkhotel tokens are generic and cross-city. | `NEW_CANONICAL_PREAUTH_CANDIDATE` |
| `MD-27a401c5e00f91073a6c` | `https://tresabay.ch/` — current Tresa Bay Hotel, Via Lugano 18, CH-6988 Ponte Tresa, 40 rooms and active booking. | Max 250000; no meaningful canonical identity candidate. | `NEW_CANONICAL_PREAUTH_CANDIDATE` |
| `MD-27cb7654c25138f8566a` | `https://www.beatus.ch/` — current BEATUS Wellness- & Spa-Hotel, Seestrasse 300, 3658 Merligen, active hotel/spa. Imprint identifies LUVITA Hotels & Spa AG. | Max 400000 from generic wellness/spa/hotel tokens across other cities. | `NEW_CANONICAL_PREAUTH_CANDIDATE` + optional operator/group discovery |
| `MD-281e7be2c117561bb57e` | `https://hotel-feldbach.ch/` — current See & Park Hotel Feldbach AG, Im Feldbach 10, CH-8266 Steckborn; 36 rooms. | Max 500000 vs generic `Park-Hotel` names in other cities. | `NEW_CANONICAL_PREAUTH_CANDIDATE` |
| `MD-284d08ed79e92ca9633a` | `https://rheingerbe.ch/` — current Rheingerbe hotel/restaurant in Stein am Rhein with active room booking. | Max 500000 vs `H-0234 Restaurant Hotel Baseltor`; overlap is generic restaurant/hotel wording. | `NEW_CANONICAL_PREAUTH_CANDIDATE` |
| `MD-2855ae3538687dc08390` | `https://www.lauberge.ch/` — current L'Auberge café-restaurant-hôtel, Rue de l'Hôtel de Ville 16, 1446 Baulmes; four bookable hotel rooms. | Max 250000 against cross-city Auberge names. | `NEW_CANONICAL_PREAUTH_CANDIDATE`; preserve small-inn accommodation granularity |
| `MD-29ca94166046fcd921f5` | `https://lofthotel.ch/` — current 3-star-superior lofthotel in Murg with rooms/suites and active accommodation. | Max 200000; no meaningful identity collision. | `NEW_CANONICAL_PREAUTH_CANDIDATE` |
| `MD-2b51224ee38c42763d77` | `https://loslorentes.com/hotel-du-cheval-blanc-bulle/` — current Hôtel du Cheval Blanc plus Los Lorentes furnished studios/apartments at multiple Bulle addresses, shared reception at Rue de Gruyères 18. | Max 222222; no name identity collision. Main risk is entity granularity, not similarity. | `EGR_REQUIRED_MULTI_COMPONENT_ACCOMMODATION_PORTFOLIO`; do **not** coerce multi-address portfolio into one physical hotel without explicit model decision |
| `MD-2c5ff2038682379edd93` | `https://www.schoenbuehl.ch/` / current destination material — Hotel-Restaurant Schönbühl, Dorfstrasse 47, 3652 Hilterfingen, 19 rooms. | Max 500000 vs `H-0577 Hotel Landgasthof Schönbühl` in Urtenen-Schönbühl and `H-0234 Restaurant Hotel Baseltor`; distinct locality/property. | `NEW_CANONICAL_PREAUTH_CANDIDATE` with explicit Schönbühl-name collision guard |

## Proposed formal B08 decision envelope

When a valid CRM/domain fencing claim becomes available, the formal writer should independently re-read E4 and the current source, then evaluate:

- 9 conventional/new accommodation-property candidates;
- 1 explicit EGR multi-component portfolio (`Los Lorentes Residences + Hôtel du Cheval Blanc`);
- Swiss Quality as a brand/affiliation relationship, never alias proof;
- LUVITA Hotels & Spa AG as an optional group/operator discovery edge;
- cross-city Parkhotel / Restaurant-Hotel / Schönbühl lexical collisions as non-binding.

Similarity remains review-space reduction only.

## Hard locks

```text
authority_advanced = false
terminal_mapping_delta = 0
canonical_id_reservations = 0
h_id_allocations = 0
H-0691 = UNALLOCATED
CRM_UNIVERSE_COMPLETE = false
OUTBOUND = CLOSED
send_allowed = 0
irreversible_external_actions = 0
```

This report is a recoverable research packet, not CRM authority.
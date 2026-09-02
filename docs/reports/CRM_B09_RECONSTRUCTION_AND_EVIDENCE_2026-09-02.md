# CRM B09 — deterministic reconstruction + identity pre-review

Status: **RESEARCH_ONLY / NON-AUTHORITATIVE**  
Project: `SWITZERLAND_JOB_OS`  
Observed base: `71010e0c8d983a2641253455e97777c25f65e887`  
Source: `HS-MEMBER-DE-33339392661` / artifact `9740219406` / 2061 records / 172 pages  
Authority read-only: E4 / 690 canonical / `H-0691_UNALLOCATED`  
Authority effect: **NONE** / Drive writes: **0** / outbound: **CLOSED**

## Deterministic selection

Uses the same zero-canonical-city lineage already regression-validated against B01, B02, B03 and B07 and used for B08. B09 is positions 81–90 after the current identity transfer.

Exact key-list SHA-256: `171fce26002d8b19a07e02e63dc1526a656d913297db17d6e0ee22f8896ea01e`

1. `MD-2c965eba36d2e32e14b6` — Albergo Ristorante Svizzero — Capolago
2. `MD-2e8edf3b3a5b6d30c48d` — Moxy Rapperswil — Rapperswil SG
3. `MD-2e94b51deff4b930852b` — Hotel 1802 — Schlatt TG
4. `MD-2fddbfbe76a514a94bfe` — Haus Surval — Flerden
5. `MD-30049898b6933d37f8ed` — B&B Hotel Geneva Airport — Vernier
6. `MD-30b31ab8d1f66bab5fcf` — Seehotel Wilerbad — Wilen (Sarnen)
7. `MD-30fa87b1899965855d0c` — La Val Hotel & Spa — Breil/Brigels
8. `MD-310fdead9d1b018a63fd` — HABITAT Lago Maggiore — Piazzogna
9. `MD-31202790b99ef13dd806` — Hotel Mulin by Amanthos — Breil/Brigels
10. `MD-3146a6879d30c3ba40de` — Alp Art Hotel — Collombey

## Research findings

### 1 — Albergo Ristorante Svizzero / Capolago

Current qualified tourism sources identify a 2-star, 23-room hotel at Via Famiglia Avvocato Scacchi 13, 6825 Capolago with the same operator/contact.

Evidence:
- https://www.myswitzerland.com/de-ch/unterkuenfte/albergo-ristorante-svizzero/
- https://www.ticino.ch/it/hotels/details/Albergo-Ristorante-Svizzero/12298.html

E4 normalized-city count = 0. No meaningful global identity collision.

Research disposition: `NEW_CANONICAL_PREAUTH_CANDIDATE`.

### 2 — Moxy Rapperswil

Marriott's current first-party page identifies Moxy Rapperswil at Neue Jonastrasse 66, 8640 Rapperswil.

Evidence:
- https://www.marriott.com/en-us/hotels/zrhox-moxy-rapperswil/rooms/

E4 normalized-city count = 0.

Research disposition: `NEW_CANONICAL_PREAUTH_CANDIDATE` + `BRAND_RELATIONSHIP_REVIEW(MOXY/MARRIOTT)`. Brand membership is not alias proof and does not imply shared recruiting without evidence.

### 3 — Hotel 1802 / Schlatt TG

Current first-party surface shows Hotel 1802 as an active hotel at Klostergutstrasse 8a, 8252 Schlatt, within the broader Klostergut Paradies complex (restaurant, hotel, seminar center, Iron Library and ferry service).

Evidence:
- https://www.1802.ch/en.html
- https://www.1802.ch/en/directions-contact.html

Research disposition: `NEW_CANONICAL_PREAUTH_CANDIDATE` + `COMPLEX_COMPONENT_RELATIONSHIP_REVIEW`.

Do not collapse Hotel 1802 into the broader Klostergut complex.

### 4 — Haus Surval / Flerden

The current municipality accommodation page lists Haus Surval with 14 beds for holiday guests plus 2 rooms for assisted living.

Evidence:
- https://www.flerden.ch/beherbergung-gastronomie

This is a mixed accommodation/care use, not a conventional hotel-only entity.

Research disposition: `EGR_REQUIRED_MIXED_ACCOMMODATION_ASSISTED_LIVING`.

### 5 — B&B HOTEL Geneva Airport / Vernier

Current B&B HOTELS first-party page identifies the 3-star property at 73 Avenue de l'Etang, 1219 Vernier, with 288 rooms and 24-hour reception.

Evidence:
- https://www.hotel-bb.com/en/hotel/geneva-airport

Cross-city lexical matches such as Lake Geneva Hotel and other Airport Hotels are generic. E4 normalized-city count for Vernier = 0.

Research disposition: `NEW_CANONICAL_PREAUTH_CANDIDATE` + `BRAND_RELATIONSHIP_REVIEW(B&B_HOTELS)`.

### 6 — Seehotel Wilerbad / Wilen (Sarnen)

**Important locality-normalization false negative.**

Current first-party evidence identifies Seehotel Wilerbad at Wilerbadstrasse 6, 6062 Wilen am Sarnersee.

Evidence:
- https://www.wilerbad.ch/en
- https://www.wilerbad.ch/en/contact

E4 already contains:

```text
H-0681
canonical_name = Seehotel Wilerbad Seminar & Spa
city = Wilen
canton = Obwalden
identity_confidence = 0.95
state = CANONICAL_CURRENT_RECONCILED_SUPPORT
```

Source city `Wilen (Sarnen)` failed the strict normalized-city equality against canonical `Wilen`, but name similarity is 0.5 and the current property identity is consistent.

Research disposition: `MATCH_EXISTING_CANDIDATE(H-0681)` with `LOCALITY_VARIANT_WILEN_SARNEN`.

This is the strongest B09 candidate for a future terminal mapping. A formal CRM writer must prove detail/contact identity before terminalization.

### 7 — La Val Hotel & Spa / Breil-Brigels

Current first-party site identifies La Val Hotel & Spa at Via Palius 18, 7165 Breil/Brigels, with active rooms/suites and 680 m² spa.

Evidence:
- https://www.laval.ch/en

E4 contains no exact La Val property; `Hôtel La Vallée` in Lourtier is a different cross-city lexical candidate.

Research disposition: `NEW_CANONICAL_PREAUTH_CANDIDATE`.

### 8 — HABITAT Lago Maggiore / Piazzogna

Current first-party site states that HABITAT Lago Maggiore consists of six dwelling units in Piazzogna and explicitly says it **is not a hotel** and goes beyond a family hotel or B&B model.

Evidence:
- https://www.habitatlagomaggiore.ch/
- https://www.habitatlagomaggiore.ch/en

Research disposition: `EGR_REQUIRED_NON_HOTEL_ACCOMMODATION`.

Do not coerce the provider membership record into conventional `HOTEL` entity type.

### 9 — Hotel Mulin by Amanthos / Breil-Brigels

Current first-party surface is now branded simply **Hotel Mulin Brigels**, at the same Brigels property; current qualified listings still expose the historical `Hotel Mulin by Amanthos` name.

Evidence:
- https://hotelmulin.ch/
- https://www.myswitzerland.com/en-us/accommodations/mulin-berglodge-1/

No Mulin entity exists in E4.

Research disposition: `NEW_CANONICAL_PREAUTH_CANDIDATE` + `CURRENT_NAME_LINEAGE_REVIEW` (`Hotel Mulin by Amanthos` → current `Hotel Mulin`).

Do not preserve a stale brand suffix as canonical truth without current operator evidence.

### 10 — Alp Art Hotel / Collombey

Current first-party site identifies a modern 3-star hotel in Collombey with 105 rooms/apartments and active direct booking.

Evidence:
- https://www.alparthotel.ch/
- https://www.alparthotel.ch/about-us

Global `Art Hotel` collisions are generic and cross-city; E4 normalized-city count = 0.

Research disposition: `NEW_CANONICAL_PREAUTH_CANDIDATE`.

## B09 disposition summary

```text
NEW_CANONICAL_PREAUTH_CANDIDATE                    7
MATCH_EXISTING_CANDIDATE                           1  # Seehotel Wilerbad → H-0681
EGR_REQUIRED_MIXED_ACCOMMODATION_ASSISTED_LIVING  1  # Haus Surval
EGR_REQUIRED_NON_HOTEL_ACCOMMODATION               1  # HABITAT Lago Maggiore
```

Additional relationship reviews:
- Moxy → Moxy/Marriott brand;
- B&B Geneva Airport → B&B HOTELS brand;
- Hotel 1802 → Klostergut Paradies complex component;
- Hotel Mulin → current-name/brand lineage.

## Formal gate

A future CRM/domain claim must independently reread current E4/source evidence before any decision. Only then may it persist MATCH/NEW/EGR dispositions. `MATCH_EXISTING_CANDIDATE(H-0681)` is not yet a terminal mapping.

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
```

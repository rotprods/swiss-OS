# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T19:48:00Z**. Current wave parent main SHA: **`44a4377c641032951c959006265437ea64f4ec54`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, ECV, SRR, SMO, RAGR, cache and canary remain non-authoritative. HOTELS_MASTER was reread during this activation and H-0691 is absent.

## CRM universe / effective pre-authority source-mapping frontier

```text
source pages / records              172 / 2061
candidate records                           1438
candidate records SHA               34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0
base terminal mappings                    624
base RECONCILE_REQUIRED                  1437
cumulative SMO terminal deltas              29
effective terminal mappings                653
RECONCILE_REQUIRED                         1408
RAGR covered active canonicals              653
RAGR reverse gaps                            37
RAGR gaps with same-city candidate           24
RAGR gaps without same-city candidate        13
ECV verified frontier              1438 / 1438
ECV remaining never verified          0
ECV pending requeue                   0
```

`653 / 1408` is a validated **pre-authority** source-resolution frontier. It does not mutate operational authority.

## Durable lineage

- source artifact `9700376482`: 2061 records, SHA `62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`.
- candidate artifact `9718866661`: 1438 records, SHA `34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0`.
- base SMC candidate SHA `2f9413318c410eb0f0443de260213d31e9ab2bdc1058581c0fa9c0340474aa27`.
- cumulative overlay materialization SHA `845cfb0d5faf4dd01d097f69ee9bb8f0a82045f558235ad80e5d8191d10a054a`.
- RAGR terminal coverage SHA `2689c30f6d3854c3e74abe15951964e0510bfe7973bee49259b03e9ace62660f`.
- RAGR-37 queue SHA `01b5106010506d31da220552dffc178378cc38791c81b1b4a7c3e837e4665dfa`.
- HOTELS_MASTER Drive ID `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`.

## Wave 0005 — RAGR variant 7 verified and terminalized pre-authority

Strict exact-current workflow run `33271527080`, artifact `9720247842`, digest `403a23ff4b52c2396cacd7cdb7aaaa7e4bd4f50a4745b44cc261548c8a2eba5f`, packet SHA `ed6c5611030422c571a6a5068a617fc5c6738c180260654c706e5683544e77d7` completed **7/7 CURRENT_DETAIL_VERIFIED** with HTTP 200, `name_match=true`, `city_match=true`, and provider-change count 0.

The seven independently corroborated same-property reviews are persisted in `docs/state/SOURCE_RESOLUTION_REVIEW_BATCH_0005_33206402141.json`: H-0002 Hotel Europa Suites, H-0681 Seehotel Wilerbad, H-0063 Appenzeller Huus / Huus Quell, H-0474 Hotel Schweizerhof Sils Maria / Faern, H-0478 Les Cernets, H-0652 Sedartis, and H-0060 Wetterhorn. Huus Bären/Löwen siblings were deliberately not bound.

The cumulative 29-delta materialization is attested by `docs/state/SOURCE_MAPPING_OVERLAY_SRR_BATCH_0005_ATTESTATION_33206402141.json`; full deterministic materialization hashes to `845cfb0d5faf4dd01d097f69ee9bb8f0a82045f558235ad80e5d8191d10a054a`. RAGR recomputation over 653 covered canonicals leaves **37** reverse gaps. The compact deterministic queue is `docs/state/RAGR_REVIEW_QUEUE_37_33206402141.json`.

`MD-034c1c3b0f7ba9d69c80` ibis budget Zürich City West remains a distinct nonterminal `NEW_CANONICAL` candidate. **No H-ID is reserved.**

## NEXT — strict ECV for cross-locality/name trio, then explicit SRR only

Pinned review-only trio:

1. H-0019 `Schweizerhof Zermatt` ← `MD-7db3357bbcfbad01a7ec` Hotel Schweizerhof, Zermatt, candidate offset 733.
2. H-0121 `Hotel Albatros` ← `MD-9e3233153af5ab2e8c01` Boutique Hotel Albatros Zermatt, offset 913.
3. H-0242 `Riders Hotel` ← `MD-aabf05311b7763fe5929` Riders Hotel, `Laax GR 2`, offset 981; locality variant requires explicit corroboration.

Stage the trio with `matched_hotel_id=""`, run strict exact-current verification, accept only independently corroborated same-property identities, recompute RAGR, and keep chaining bounded evidence waves. In parallel continue CP-R01/CP-R02 toward the complete 2061-record SMC/SRR rebuild.

SSR-1.0 remains blocked on the missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. MEP fallback remains qualified member-directory + exact-current and is not API-equivalent. Issues #240, #239 and #14 remain the execution, resolver-safety and structured-source boundaries.

Drive recovery doc: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. Private review doc: `1Ktlvg04MbDrgZ0LD0wGYrpz65xTHBRyiNdD8KWLxNhk`.

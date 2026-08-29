# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T20:37:00Z**. Current wave parent main SHA: **`55b8e6cf570cc603018b92f36de97b07995b7f3a`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, ECV, SRR, SMO, RAGR, SRET, provider-enrichment, cache and canary remain non-authoritative. HOTELS_MASTER remains 690 rows and H-0691 remains absent. No H-ID has been allocated or reserved.

## Effective source-resolution frontier

```text
source pages / records              172 / 2061
candidate records                           1438
base terminal mappings                    624
cumulative SMO terminal deltas              32
effective terminal mappings                656
RECONCILE_REQUIRED                         1405
ECV verified frontier              1438 / 1438
ECV remaining never verified              0
RAGR residual reverse gaps                  34
```

Pinned lineage: source records SHA `62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`; candidate records SHA `34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0`; base SMC candidate SHA `2f9413318c410eb0f0443de260213d31e9ab2bdc1058581c0fa9c0340474aa27`; cumulative 32-delta materialization SHA `e8a6da1bfe5e585807e41f91db9ecccb507c60140366e9dab7f36290c613a368`; terminal coverage SHA `95c48f65fbf67c2fb2c284c9ba603be03d706d2f46ef7373dc8ebb7272b3c176`; RAGR-34 queue SHA `cf47dc91057df8653cd75729cb39320605e193e476c6828f24956b69e2848b9c`.

## SRET-1.0 — full source triage + provider identity wave

Full SRET remains review-only: 656 carried terminal mappings plus 1405 triage records. Full items SHA `b15ed2d019759b3730a225207cdb1ba674b16b93ac925b74dbabff2d495aecf6`; triage SHA `e82127ea2abc0ac68ef194496cd0de6bfddab2596a9dda15bf13411316d6f790`. Corrected ambiguity queue SHA `1fdf800a0b7bd9ad64a7a47c9c9c41c87c2c38a3d4b91e1fea2b54c93230cee8`.

The eight exact-name/locality ambiguities have now been independently checked against current property identity fields. All eight source properties have address/domain/phone identity distinct from every exact-name canonical signal. Evidence packet: `docs/state/SRET_PROVIDER_IDENTITY_AMBIGUITY8_33206402141.json`; items SHA `609f622584d1283714f7cf409ba933782984a7ecdd662dbcf4ea34e1d1a9ca21`; packet SHA `ee1ee5c753f568ee03d61c1b7de8140af43cf90e440702eb4c350f27802afb6c`.

Evidence outcomes, all **review-only / no H-ID**:
- Hotel De la Paix / Interlaken is a current Bernastrasse 24 property on `hotel-de-la-paix.ch`, distinct from H-0600 Hôtel de la Paix / Lausanne at Avenue Benjamin-Constant 5 on `hoteldelapaix.net`.
- Hotel Du Lac / Därligen is a current Dorfstrasse 76 property on `dulac-thunersee.ch`, distinct from exact-name properties H-0505 Villars-sur-Ollon/Bretaye, H-0506 Interlaken and H-0507 Crans-Montana.
- Hôtel Du Port / Villeneuve is a current Rue du Quai 6 property on `duport.ch`, distinct from H-0620 Lausanne at Place du Port 5 on `hotel-du-port.ch`.
- Hotel Astoria / Luzern is the current Pilatusstrasse 29 property on `astoria-luzern.ch`, distinct from the exact-name canonical set in Samnaun-Ravaisch, Leukerbad, Zermatt, Genève and Arosa.
- Hotel Silberhorn / Wengen is the current Wengiboden 1347 property on `silberhorn.ch`, distinct from H-0151 Lauterbrunnen at Bir Zuben 465 on `silberhorn.com`; the within-region locality overlap is therefore explicitly resolved by address/domain/phone rather than city strings.
- Hotel De la Paix / Luzern is the current Museggstrasse 2 property on `de-la-paix.ch`, distinct from H-0600 Lausanne.
- Hotel Allegra / Pontresina is the current Via Maistra 171 property on `allegrahotel.ch`, distinct from H-0382 Zuoz on `allegra-zuoz.ch`.
- Hotel Drei Könige / Einsiedeln is the current Paracelsuspark 1 property on `hotel-dreikoenige.ch`, distinct from H-0650 Luzern on `drei-koenige.ch` and H-0677 Chur on `dreikoenige.ch`.

This closes the **ambiguity classification** for those eight into `NOVELTY_REVIEW_DISTINCTNESS_CORROBORATED`; it does not create canonical records, terminal source mappings or authority actions. The source-mapping frontier therefore remains 656 terminal / 1405 `RECONCILE_REQUIRED`.

## NEXT — attack highest-risk novelty tail

The next safe bottleneck is the highest-risk subset of the 1397 novelty records, beginning with the **116 same-city similarity-hint records** and prioritizing the 20 records at Jaccard ≥0.60. Similarity remains review-space reduction only; independently corroborate provider identity fields before any explicit resolution decision. The known-distinct ibis budget Zürich City West versus ibis Zürich City West case remains an adversarial control against fuzzy auto-binding.

No remaining ambiguity record should be bound to an existing canonical from name/locality. For distinctness-proven new-property candidates, keep `canonical_hotel_id` empty and H-0691 unallocated until a separately authorized authority transaction becomes eligible. Authoritative cross-plane reconciliation remains blocked while 1405 source decisions remain nonterminal.

SSR-1.0 remains provider-boundary blocked on the missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. Continue the qualified HotellerieSuisse member-directory + exact-current MEP fallback without claiming structured API equivalence.

Drive HOTELS_MASTER: `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`. Private review: `1Ktlvg04MbDrgZ0LD0wGYrpz65xTHBRyiNdD8KWLxNhk`. Recovery: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. RAGR recovery: `12X7sQZDWIFm8Ss9DyxYYzvit6zSKq6ZeAliM6lEvNVg`.

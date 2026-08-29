# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T20:24:00Z**. Current wave parent main SHA: **`22d2d57ab22c227b1781f6705f851871667f1bb3`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, ECV, SRR, SMO, RAGR, SRET, cache and canary remain non-authoritative. HOTELS_MASTER remains 690 rows and H-0691 remains absent. No H-ID has been allocated or reserved.

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

## SRET-1.0 — full 2061-record evidence triage materialized

SRET-1.0 remains strictly review-only. The deterministic full frontier is 656 carried terminal mappings plus 1405 triage records: `MATCH_EXISTING_REVIEW=0`, `AMBIGUOUS_REVIEW=8`, `NOVELTY_REVIEW=1397`, `EVIDENCE_PENDING=0`; 116 novelty records have same-city similarity hints used only to reduce review space. Full items SHA `b15ed2d019759b3730a225207cdb1ba674b16b93ac925b74dbabff2d495aecf6`; triage SHA `e82127ea2abc0ac68ef194496cd0de6bfddab2596a9dda15bf13411316d6f790`.

A post-merge lineage audit caught that the first public ambiguity-queue projection was not selected directly from those hashed SRET items: several source keys/localities were stale. It was fail-closed and never used for a terminal decision. The queue is now regenerated directly by `triage_state == AMBIGUOUS_REVIEW`, includes the source detail URLs, and hashes to **`1fdf800a0b7bd9ad64a7a47c9c9c41c87c2c38a3d4b91e1fea2b54c93230cee8`**. This correction changes review lineage only; all SRET counts, full items/triage hashes, authority state, and mapping frontier remain unchanged.

Correct ambiguity records are: Hotel De la Paix / Interlaken; Hotel Du Lac / Därligen; Hôtel Du Port / Villeneuve VD; Hotel Astoria / Luzern; Hotel Silberhorn / Wengen; Hotel De la Paix / Luzern; Hotel Allegra / Pontresina; and Hotel Drei Könige / Einsiedeln. Each remains ambiguity-only; exact global-name collisions do not authorize mapping.

Public-safe summary: `docs/state/SRET_FULL_2061_SUMMARY_33206402141.json`. Corrected ambiguity queue: `docs/state/SRET_AMBIGUITY_QUEUE_0001_33206402141.json`.

## NEXT — provider identity enrichment before further terminal resolution

The shallow deterministic identity surface is exhausted. Enrich bounded SRET records with current provider identity fields that can disambiguate variants: external property-domain candidates and structured postal/location identity where available. Compare those fields to HOTELS_MASTER current official domains/locations. Exact independently corroborated agreement may justify an explicit SRR review; **absence or difference of a domain is not proof of a new canonical**.

Start with the corrected 8 ambiguity records, then a bounded highest-value subset of the 116 same-city similarity hints. Persist enrichment evidence/hashes, keep target IDs out of staging, and apply only independently demonstrated SRR decisions. Records lacking sufficient identity evidence remain `NOVELTY_REVIEW` or `AMBIGUOUS_REVIEW`.

The dominant P0 remains `RECONCILE_REQUIRED=1405`. `MD-034c1c3b0f7ba9d69c80` ibis budget Zürich City West remains a distinct nonterminal new-canonical review candidate; **H-0691 is not reserved**.

SSR-1.0 remains provider-boundary blocked on the missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. Continue the qualified HotellerieSuisse member-directory + exact-current MEP fallback without claiming structured API equivalence.

Drive HOTELS_MASTER: `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`. Private review: `1Ktlvg04MbDrgZ0LD0wGYrpz65xTHBRyiNdD8KWLxNhk`. Recovery: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. RAGR recovery: `12X7sQZDWIFm8Ss9DyxYYzvit6zSKq6ZeAliM6lEvNVg`.

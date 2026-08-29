# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T20:02:00Z**. Current wave parent main SHA: **`89757b2b679d95b728a391ece2686dbbe1cf97a3`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

## Authority — unchanged / locked

```text
physical / active HOTELS          690 / 690
next physical ID                  H-0691 UNALLOCATED
CRM_UNIVERSE_COMPLETE             FALSE
OUTBOUND                          CLOSED
send_allowed                      0
H-ID / canonical reservations     0 / 0
```

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, ECV, SRR, SMO, RAGR, cache and canary remain non-authoritative.

## Effective pre-authority CRM frontier

```text
source records                    2061
candidate records                 1438
base terminal / reconcile         624 / 1437
cumulative explicit SMO deltas     32
effective terminal / reconcile    656 / 1405
RAGR covered active canonicals    656 / 690
RAGR reverse gaps                  34
same-city / no-same-city gaps      21 / 13
ECV current-detail verified       1438 / 1438
```

Lineage: source records SHA `62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`; candidate records SHA `34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0`; base SMC SHA `2f9413318c410eb0f0443de260213d31e9ab2bdc1058581c0fa9c0340474aa27`; cumulative 32-delta materialization SHA `e8a6da1bfe5e585807e41f91db9ecccb507c60140366e9dab7f36290c613a368`; RAGR terminal coverage SHA `95c48f65fbf67c2fb2c284c9ba603be03d706d2f46ef7373dc8ebb7272b3c176`; RAGR-34 queue SHA `cf47dc91057df8653cd75729cb39320605e193e476c6828f24956b69e2848b9c`.

## Wave 0006 — cross-locality trio terminalized pre-authority

Strict exact-current run `33272258669`, artifact `9720448254`, artifact digest `f618978efe01b9d73dc19cdf499d3badeb21f72d167231b04499ebcd5a19922f`, packet SHA `f314ba5d09a63608c5bef911f6c9993bf0ffebc6cc16b687298ca9c1d3d8bda8` completed **3/3 CURRENT_DETAIL_VERIFIED**, HTTP 200, name/city match true, provider-change count 0.

Explicit SRR-1.1 pre-authority matches:
- H-0019 ← `MD-7db3357bbcfbad01a7ec` Hotel Schweizerhof, corroborated by current Schweizerhof Zermatt official identity.
- H-0121 ← `MD-9e3233153af5ab2e8c01` Boutique Hotel Albatros Zermatt, corroborated by current official property identity.
- H-0242 ← `MD-aabf05311b7763fe5929` Riders Hotel, source locality `Laax GR 2`, corroborated by current Riders Hotel identity in Laax.

Durable evidence/review/overlay lineage: `docs/state/ECV_BATCH_0005_SUB0001_RESULT.json`, `docs/state/SOURCE_RESOLUTION_REVIEW_BATCH_0006_33206402141.json`, `docs/state/SOURCE_MAPPING_OVERLAY_SRR_BATCH_0006_ATTESTATION_33206402141.json`, and `docs/state/RAGR_REVIEW_QUEUE_34_33206402141.json`.

The remaining RAGR-34 set has no currently demonstrated safe fuzzy terminalization path; similarity-only candidates include cross-city duplicate names and resort/component ambiguities. RAGR therefore remains review-only and fail-closed.

`MD-034c1c3b0f7ba9d69c80` ibis budget Zürich City West remains a distinct nonterminal `NEW_CANONICAL` candidate. **No H-ID is reserved.**

## NEXT — full 2061-record SMC/SRR rebuild, no fuzzy auto-bind

1. Rebuild the complete 2061-record source mapping candidate from the pinned base SMC lineage plus the 32 validated explicit deltas; preserve conservation exactly.
2. Materialize all remaining 1405 records as explicit `RECONCILE_REQUIRED` / review-required unless stronger deterministic evidence exists; never infer terminal state from fuzzy RAGR suggestions.
3. Validate SRR-1.1 coverage, duplicate risk, target validity, evidence references and source-record conservation.
4. Recompute RAGR after any new evidence-backed decisions.
5. Keep ibis budget Zürich City West as nonterminal `NEW_CANONICAL`; never reserve H-0691 from staging.
6. Operational authority promotion remains forbidden until full source-resolution and SSR-1.0 gates pass.

SSR-1.0 remains blocked on the missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. MEP fallback remains qualified member-directory + exact-current and is not API-equivalent.

Recovery: source artifact `9700376482`; candidate artifact `9718866661`; HOTELS_MASTER Drive `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`; Drive recovery `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`; private review `1Ktlvg04MbDrgZ0LD0wGYrpz65xTHBRyiNdD8KWLxNhk`.

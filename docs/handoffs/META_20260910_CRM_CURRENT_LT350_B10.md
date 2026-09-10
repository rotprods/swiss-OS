# META — CRM CURRENT <0.35 B10 + locality guard — 2026-09-10

Status: **PREAUTH B10 COMPLETE / AUTHORITY UNCHANGED**

## Durable truth

- Authority: `HS_ENTITY_EPOCH_2026-08-25_E4` / `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`
- Canonical physical/current: `690`
- Next H-ID: `H-0691_UNALLOCATED`
- Source snapshot: `HS-MEMBER-DE-33339392661`, `2061 / 172`, SHA `b16fdb63a01149e10feb4d506f38301644b73a612f898ce72567ec4fa92da404`
- Terminal mappings: `658`
- `RECONCILE_REQUIRED`: `1403`
- `<0.35 reviewed`: `100 / 1289`
- `<0.35 remaining`: `1189`
- zero-city lane: `485`, reviewed `100`, remaining `385`
- cumulative `NEW_CANONICAL_PREAUTH`: `208`
- authority/H-ID/outbound mutation: `NONE / 0 / CLOSED`

## B10

State: `docs/state/CRM_CURRENT_UNRESOLVED_LT350_B10_2026-09-10.json`
Evidence: `docs/operations/CRM_CURRENT_UNRESOLVED_LT350_B10_EVIDENCE_PACKET_2026-09-10.json`

Disposition: 9 `NEW_CANONICAL_PREAUTH`, 1 `NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED` (`Vallombrosa`). No terminal source mapping was created.

## Locality failure-family repair

`src/swiss_os/locality_normalization_guard.py` generalizes the B09 Wilerbad failure. It expands locality comparison conservatively for accents/punctuation, parentheticals, canton suffixes, numeric district suffixes and airport qualifiers. Every finding is review-only; locality equivalence never proves identity.

The deterministic reconstruction proves:

`2061 source -> 1438 candidate -> 488 literal zero-city -> minus 3 exact-global-name locality conflicts -> 485 operational zero-city lane`.

The first 90 operational-lane keys reproduce B01..B09 exactly. Five of the 395 rows remaining after B09 require locality-expanded comparator review. See `docs/state/LOCALITY_NORMALIZATION_SCAN_LT350_REMAINING_2026-09-10.json`.

## Recovery

If Drive is unavailable, use:

1. frozen current source manifest `HS-MEMBER-DE-33339392661` / artifact lineage `9740219406`;
2. Library recovery `CRM_UNIVERSE_STAGING_2026-08-28_v10.xlsx`, sheet `Canonical_Current`, exactly 690 E4 identities;
3. `locality_normalization_guard.rebuild_zero_city_lane`;
4. verify `candidate=1438`, `raw_zero_city=488`, `exact_name_conflicts=3`, `lane=485`;
5. verify B01..B10 first 100 keys before deriving any later batch.

Do not infer a new hotel from literal city inequality alone.

## Next safe action

Consume `docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B10.json` exactly. Its B11 ten-key workset already excludes `MD-37df0d95a87f101c1916 Hotel Du Lac / Därligen`, which belongs to separate exact-global-name locality-conflict review.

Run locality guard -> current evidence -> canonical comparator -> operator/group/EGR review -> PREAUTH disposition. No H-ID allocation/reservation. No outbound.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

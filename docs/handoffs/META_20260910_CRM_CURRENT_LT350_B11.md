# META — CRM current `<0.35` B11 handoff

Authority: **PREAUTH handoff only**. This document never promotes hotel authority.

## Live parent

- project: `SWITZERLAND_JOB_OS`
- authority epoch: `HS_ENTITY_EPOCH_2026-08-25_E4`
- authority revision: `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`
- canonical: `690`
- next H-ID: `H-0691 UNALLOCATED`
- frozen snapshot: `HS-MEMBER-DE-33339392661`, 2061 records / 172 pages
- terminal mappings: `658`
- `RECONCILE_REQUIRED=1403`
- outbound: `CLOSED`, `send_allowed=0`

## Session / claim

B11 runs under `CLAIM-CRM-ENTITY-RESOLUTION-018`, fencing token `18`, with a PREAUTH-only ceiling. It may research, run locality/comparator/EGR review, persist PREAUTH dispositions and continuity artifacts. It may not mutate hotel authority, allocate/reserve H-IDs, terminalize source mappings, or execute outbound.

## B11 result

Exact B11 source keys are persisted in `docs/state/CRM_CURRENT_UNRESOLVED_LT350_B11_2026-09-10.json` and current evidence in `docs/operations/CRM_CURRENT_UNRESOLVED_LT350_B11_EVIDENCE_PACKET_2026-09-10.json`.

Disposition:

- 6 × `NEW_CANONICAL_PREAUTH`
- 4 × `NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED`
- 0 × `MATCH_EXISTING_PREAUTH`
- 0 terminal mapping delta
- 0 H-ID allocations/reservations

The four EGR cases are Whitepod Original, Casa High Life, La Villa - Studios & Rooms, and SWISSPEAK Resorts Zinal. Preserve their accommodation/component granularity; do not coerce them into a conventional single-building hotel ontology.

`Erlebnisland Grizzlybär` is current at review time but its first-party opening-hours page announces closure of the overall operation at the end of December 2026. Preserve this as a temporal risk and schedule a freshness check before authority promotion or L9.

## Reproducible locality result

B11 produces zero locality-variant comparator hits under `LOCALITY_NORMALIZATION_GUARD_V1`. Locality equivalence remains comparator expansion only and never property identity authority.

## Frontier after B11

```text
current <0.35 reviewed cumulative       110 / 1289
historical <0.35 tail remaining             1179
operational zero-city reviewed              110 / 485
zero-city lane remaining                     375
cumulative NEW_CANONICAL_PREAUTH             214
terminal mappings                            658
RECONCILE_REQUIRED                          1403
```

## NEXT — B12

Consume `docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B11.json` exactly. B12 is positions 111–120 of the deterministic operational zero-city lane:

1. Capsule Hotel Alpine Garden — Zürich-Flughafen
2. Zleep Hotel Zürich Kloten — Kloten
3. Hotel Gletscherblick — Hasliberg Goldern
4. Swiss Diamond Boutique Hotel La Romantica — Melide
5. La Réserve Genève Hotel, Spa and Villa — Bellevue
6. LA PALMA AU LAC HOTEL & SPA — Locarno
7. Jugendherberge Lugano — Lugano-Savosa
8. Reka-Feriendorf Zinal — Zinal
9. Hotel Kloster Fischingen — Fischingen
10. Appenberg - Hoteldorf, Seminare & Events — Zäziwil

Before any successor mutation: verify live main, replay claims/events, require token18 terminal/released with no active writer, and acquire a new globally unique session/fencing token >18. Keep `CRM_UNIVERSE_COMPLETE=FALSE`, `OUTBOUND=CLOSED`, `send_allowed=0`.

# META HANDOFF — FULL 657 REBUILD + RAGR REATTEST

## Live parent

- repo: `rotprods/swiss-OS`
- parent main: `d6c49f158c3691f44868cb9a55a52bc6c6aea225`
- authority epoch: `HS_ENTITY_EPOCH_2026-08-25_E4`
- authority materialization SHA: `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`
- snapshot: `HS-MEMBER-DE-33206402141`

## Wave result

The deferred full terminal coverage rebuild was executed from current pinned inputs rather than relabeling the previous 656-row hash.

- source: 2061, records SHA `62e26d62d8677a5437e081302b6b4d206c0d27a0fe268c6356aef01da5428dc2`
- candidate: 1438, records SHA `34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0`
- exact unique `(name, city)`: 623
- pinned exact correction: `MD-dd14bef2251b12ecd017 -> H-0088`
- explicit reviewed SRR deltas: 33
- terminal source mappings: **657**
- unresolved: **1404**
- terminal pair SHA: `5698591ab5c89bc8651dda6f7e2cfeba8c80312e3c19c78736adf1d0e521727e`
- unresolved-key SHA: `7285cbcd5936cfabd33ea6f1769cfbf99acd3639562306c0e1bf0632d5400323`

The rebuild exposes one expected many-to-one provider/component relation: H-0452 is reached by the pre-existing exact source record `MD-319d62613a484d48f48a` and Wave-15 `MD-7c70baeb19408c2e971b` FIVE Zürich - EAST WING. Therefore 657 source mappings cover 656 unique canonical targets.

RAGR recomputation remains **34** reverse gaps; gap-list SHA `bca692c105efac8c8929c1639e1ebe643dd03f0a6ecab4bb42d86e0acccba568`. This is a reconciliation result only, not authority promotion.

## Gauntlet

PASS:
- no fuzzy auto-binding;
- all 34 exceptional source keys are in the 1438 candidate side;
- all mapped H-IDs exist in the observed 690-row canonical projection;
- source terminal keys unique;
- H-0452 many-to-one relation explicitly typed rather than treated as a collision;
- authority unchanged;
- H-ID allocations/reservations = 0;
- `CRM_UNIVERSE_COMPLETE=false`;
- `OUTBOUND=CLOSED`;
- `send_allowed=0`.

A direct GitHub-Actions-artifact → Drive recovery upload was attempted and rejected by connector egress (`BLOCKED_FILE_REFERENCE_EGRESS`). MEP fallback is the compact GitHub recovery attestation plus pinned artifact IDs/hashes. Drive remains a projection/recovery plane, never silently promoted to authority.

## Durable recovery

Primary: `docs/state/FULL_SOURCE_MAPPING_REBUILD_657_ATTESTATION_33206402141.json`.

To reproduce: verify parent/descendant + E4; download source artifact 9700376482 and candidate artifact 9718866661; exact-match unique normalized name+city; apply the 34 exceptional mappings in the attestation; require 657 terminals / 1404 unresolved and terminal SHA `569859...`; recompute RAGR and require 34 gaps / gap SHA `bca692...`.

## NEXT

Route: `PROVIDER_IDENTITY_050_REMAINING_37`.

Dependency: read-only current provider identity evidence for the remaining 37 Jaccard-0.50 records. Apply explicit SRR only where independent same-property identity is proven. Distinctness/novelty review alone remains nonterminal and must not reduce 1404. After this bucket, process the lower-similarity tail of 49.

Persistent external blocker: discover.swiss structured SSR-1.0 cannot be claimed without the missing `Infocenter Open` subscription key and a capture-valid structured manifest. MEP remains qualified HotellerieSuisse member-directory + exact-current.

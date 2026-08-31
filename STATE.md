# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-08-31 current-source entity-resolution B04**. Verified bootstrap main parent: **`a3299117a0fa1168b0b36f4da4b2f95cb1ea7719`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

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

Live Drive `HOTELS_V2` was re-read through the physical frontier during this activation: `H-0690` remains the last canonical row and `H-0691` is absent/unallocated. No staging, cache, canary, CI artifact, candidate export, source-research decision or preauthority SRR/EGR result can become authoritative or allocate/reserve an H-ID.

## Current coherent source universe

```text
HotellerieSuisse snapshot        HS-MEMBER-DE-33339392661
GitHub Actions run              33339392661
artifact                        9740219406
records / pages                 2061 / 172
coverage_complete               TRUE
source records SHA256           b16fdb63a01149e10feb4d506f38301644b73a612f898ce72567ec4fa92da404
terminal source mappings         658
unique canonical targets         656
RECONCILE_REQUIRED              1403
reverse authority source gaps     34
```

The older `HS-MEMBER-DE-33206402141` capture is historical lineage only. Current candidate continuity remains fully accounted: 1436 exact unchanged identities plus two changed Gonten identities.

## Entity-resolution frontier

```text
historical candidate records                    1438
candidate lineage accounted                     1438 / 1438
ECV verified frontier                           1438 / 1438
ECV remaining never verified                    0
prior >=0.60 review                              20 / 20
prior 0.50–0.599999 review                       46 / 46
prior lower49 ordinary review                    47 / 47
lower49 typed SRR materialized                   47 / 47
RAGR evidence-classified                         34 / 34
cumulative NEW_CANONICAL preauthority             154
historical <0.35 previously unreviewed tail     1289
zero-same-city conservative sub-lane             485
current <0.35 reviewed cumulative                 40
current <0.35 B04 reviewed                        10
current <0.35 B04 NEW_CANONICAL preauthority      10
historical <0.35 tail remaining                 1249
zero-same-city lane remaining                    445
H-ID allocations                                   0
canonical ID reservations                          0
```

`docs/state/CRM_CURRENT_UNRESOLVED_LT350_B04_2026-08-31.json` records the fourth bounded exact-current continuation. Two Radisson high-similarity collisions were explicitly proved to be distinct properties from canonical `H-0222` rather than fuzzy-bound. `Solution-Grischun` is preserved under EGR-1.0 as a named operator managing multi-unit holiday accommodation, with legal seat Bonaduz and current accommodation inventory in Chur; no single-physical-hotel identity or alias collapse is inferred. All ten B04 rows remain `NEW_CANONICAL_PREAUTH` / `RECONCILE_REQUIRED`, with zero terminal mapping delta.

## Continuity / capability frontier

CSP-1.0 is active. `docs/continuity/CONTEXT_SURVIVAL.json` must validate before zero-context resumption and must be regenerated whenever a pinned survival file or latest domain NEXT changes.

```text
GitHub read/write/branch/PR/CI       YES
GitHub Actions artifacts/logs        YES
Drive native Sheets read/write       YES
web current-source research          YES
File Library read                    YES
File Library write                   NO
discover.swiss runtime key           ABSENT
capture-valid discover manifest      ABSENT
durable DB-first E4 egress           BLOCKED_FILE_REFERENCE_DO_NOT_REPEAT
```

Structured discover.swiss SSR-1.0 remains provider-blocked, but the provider-neutral current HotellerieSuisse entity-resolution route remains safe and productive. Do not retry the blocked exact E4 generated-file egress family.

## Open P0 / highest-value safe bottleneck

`CRM_UNIVERSE_COMPLETE` remains **FALSE** because **1403 current coherent source records remain `RECONCILE_REQUIRED`**. Preacthority NEW_CANONICAL typing is review progress only; it neither terminalizes source mappings nor advances the authority denominator. Continue bounded evidence-backed resolution while E4 remains locked.

## NEXT

Execute **`CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B05`** over:

```text
MD-1523bc8c54a8f80c63a1
MD-15328beab2813a777e0d
MD-1679afa763ce7de7c324
MD-16d503bef0fa48f1d44d
MD-172e10497469ac29259e
MD-17a059dc9632c6ff4d1d
MD-17af64859ef43e875027
MD-1855265ec07d6b3c1a40
MD-18cbb9206e15539f177d
MD-18ddf5bd589df297650d
```

Reconstruct live ancestry, validate CSP-1.0, and re-read E4 first. Continue current identity/accommodation evidence review, explicit canonical-collision review where similarity is material, and EGR-1.0 where operator/property granularity is ambiguous. Similarity is rank-only; fuzzy autobind is forbidden. Keep `OUTBOUND=CLOSED` / `send_allowed=0`.

Recovery inputs and exact blockers are persisted in `docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B04.json` and `docs/handoffs/META_20260831_CRM_CURRENT_LT350_B04.md`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

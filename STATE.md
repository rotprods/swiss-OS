# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-08-31T02:30:00Z**. Verified main parent: **`02dad1a5bd82219b34430b5fd1cee3ee088642b6`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

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

Live Drive `HOTELS_V2` was re-read through row 691: `H-0690` is the physical frontier and `H-0691` is absent/unallocated. No staging, cache, canary, CI artifact, candidate export, SRR/ECV result or source crawl can become authoritative or advance this authority.

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

The earlier `HS-MEMBER-DE-33206402141` capture remains historical partial lineage only. The coherent current source differs by exactly two renamed Gonten identities; PR #382 re-anchored those reviewed preauthority decisions without a terminal mapping delta.

## Candidate / ECV continuity

```text
historical candidate records    1438
exact unchanged current lineage 1436
changed Gonten lineage              2
candidate lineage accounted     1438 / 1438
ECV verified frontier            1438 / 1438
ECV remaining never verified        0
lower49 typed SRR materialized     47 / 47
RAGR evidence-classified           34 / 34
cumulative NEW_CANONICAL preauthority 114
H-ID allocations                    0
canonical ID reservations           0
```

`docs/state/CRM_EXACT_CURRENT_CANDIDATE_LINEAGE_33339392661.json` deterministically transfers 1436 unchanged historical candidate identities onto the current coherent source by exact detail URL + normalized exact name/city. The two changed Gonten identities are handled by `CRM_CURRENT_GONTEN_ECV_SRR_LINEAGE_33339392661.json`. These are lineage and preauthority review products only. Historical completed SRR/RAGR frontiers above are preserved monotonically; they do not grant authority and are not reopened by the current-source re-anchor.

## Capability / provider frontier

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

The coherent HotellerieSuisse source repaired the acquisition P0. Structured discover.swiss SSR-1.0 remains unavailable until a subscription/capture-valid manifest exists, but it is no longer a global blocker: provider-neutral current-source entity resolution can continue safely.

## Open P0 / highest-value safe bottleneck

`CRM_UNIVERSE_COMPLETE` remains **FALSE** because **1403 current coherent source records remain `RECONCILE_REQUIRED`**. Issue #89 / ASR-1.0 recovery is closed and the cross-plane E4 authority remains exact at 690; it must not be reopened as a current blocker.

## NEXT

Execute **`CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION`** in bounded evidence-backed batches.

Rules:

- rank-only similarity is allowed for triage; fuzzy auto-bind is forbidden;
- current first-party / current HotellerieSuisse evidence can support preauthority SRR decisions;
- never reserve or allocate H-IDs from staging;
- never advance authority from CI/cache/canary/source artifacts;
- any later authority promotion must use exact-current DB-first cross-plane reconciliation;
- keep `OUTBOUND=CLOSED` and `send_allowed=0`.

Recovery inputs and exact blockers are persisted in `docs/state/NEXT.json` and `docs/handoffs/META_20260831_CRM_CURRENT_SOURCE_CONTINUITY.md`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

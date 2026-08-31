# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-08-31 current-source entity-resolution B05**. Verified bootstrap main parent: **`06af39bb00bc50c6b76f5d68f42c7966d8306229`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

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

Live Drive `HOTELS_V2` was re-read in this activation: `H-0690` remains the last physical/canonical row and `H-0691` is absent/unallocated. No staging/cache/canary/source-review result may reserve an ID or advance authority.

## Current coherent source universe

```text
snapshot                         HS-MEMBER-DE-33339392661
Actions run                      33339392661
artifact                         9740219406
records / pages                  2061 / 172
coverage_complete                TRUE
records SHA256                   b16fdb63a01149e10feb4d506f38301644b73a612f898ce72567ec4fa92da404
terminal source mappings          658
unique canonical targets          656
RECONCILE_REQUIRED               1403
reverse authority/source gaps      34
```

## Entity-resolution frontier

```text
candidate lineage accounted                    1438 / 1438
ECV verified frontier                           1438 / 1438
ECV remaining never verified                    0
prior >=0.60 review                              20 / 20
prior 0.50–0.599999 review                       46 / 46
prior lower49 ordinary review                    47 / 47
lower49 typed SRR materialized                   47 / 47
RAGR evidence-classified                         34 / 34
historical <0.35 previously unreviewed tail     1289
zero-exact-city conservative lane                485
current <0.35 reviewed cumulative                 50
cumulative NEW_CANONICAL preauthority             164
historical <0.35 tail remaining                 1239
zero-exact-city lane remaining                   435
H-ID allocations                                   0
canonical ID reservations                          0
```

B05 is persisted in `docs/state/CRM_CURRENT_UNRESOLVED_LT350_B05_2026-08-31.json`. It explicitly catches two fast-lane exceptions: `St. Moritz-Bad` is reconciled against the existing St. Moritz locality cluster before keeping Jugendherberge St. Moritz preauthority-new; `Hôtel Magrappé` and separately listed `Hôtel Chalet Royal` retain a shared-reception sibling relationship under EGR-1.0 rather than being collapsed. All ten B05 rows remain `RECONCILE_REQUIRED`; terminal mapping delta is zero.

## Continuity / capability

CSP-1.0 is active and must validate before zero-context resumption. GitHub/CI, Drive Sheets and current-source research are available. File Library is read-only. Structured discover.swiss remains blocked by the absent runtime subscription key/capture-valid manifest, but that is not a global blocker. Exact E4 generated-file egress remains `BLOCKED_FILE_REFERENCE_DO_NOT_REPEAT`.

## NEXT

Execute **`CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B06`** over the exact keys in `docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B05.json` after live main, CSP and E4 reconstruction. Similarity is review-space reduction only; re-check locality variants and property/operator granularity before any preauthority disposition. Never reserve/allocate H-IDs here. Keep `OUTBOUND=CLOSED` / `send_allowed=0`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

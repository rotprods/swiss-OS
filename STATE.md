# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-08-31 current-source entity-resolution B06**. Verified bootstrap main parent: **`1bbabe457d8ec561249b2bb52b862096df900d42`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

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

The **authoritative** operational ceiling is E4/690 only. Every current source-review, staging, cache, CI and **canary** artifact is non-authoritative until a separately eligible cross-plane authority transaction passes all gates.

Live Drive `HOTELS_V2` was re-read after B05: `H-0690` remains the last physical/canonical row and `H-0691` is absent/unallocated. No staging/cache/canary/source-review result may reserve an ID or advance authority.

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
current <0.35 reviewed cumulative                 60
cumulative NEW_CANONICAL preauthority             174
historical <0.35 tail remaining                 1229
zero-exact-city lane remaining                   425
H-ID allocations                                   0
canonical ID reservations                          0
```

B06 is persisted in `docs/state/CRM_CURRENT_UNRESOLVED_LT350_B06_2026-08-31.json`. It explicitly reconciles `Montreux-Territet` against the current Montreux cluster before preserving Jugendherberge Montreux as a distinct preauthority entity; Chante-Joux is preserved under EGR-1.0 as a group-accommodation facility rather than being coerced into a conventional hotel identity; generic name/token collisions for Gasthof Bären, Hotel & Restaurant Promenade and Hotel Restaurant Badhof remain non-binding. All ten B06 rows remain `RECONCILE_REQUIRED`; terminal mapping delta is zero.

## Continuity / capability

CSP-1.0 is active and must validate before zero-context resumption. GitHub/CI, Drive Sheets and current-source research are available. File Library is read-only. Structured discover.swiss remains blocked by the absent runtime subscription key/capture-valid manifest, but that is not a global blocker. Exact E4 generated-file egress remains `BLOCKED_FILE_REFERENCE_DO_NOT_REPEAT`.

## NEXT

Execute **`CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B07`** over the exact keys in `docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B06.json` after live main, CSP and E4 reconstruction. Similarity is review-space reduction only; re-check locality variants, generic collisions, accommodation type and EGR relationships before any preauthority disposition. Never reserve/allocate H-IDs here. Keep `OUTBOUND=CLOSED` / `send_allowed=0`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

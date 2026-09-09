# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-09-10 current-source entity-resolution B09**. Coordination claim used for this bounded wave: **`CLAIM-CRM-ENTITY-RESOLUTION-016`**, fencing token **16**, PREAUTH SRR decision scope only. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

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

The authoritative operational ceiling remains E4/690. Every current source-review, staging, cache, CI, preauthority decision and canary artifact is non-authoritative until a separately eligible cross-plane authority transaction passes all gates. No source-review result may reserve an H-ID or advance hotel authority.

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
current <0.35 reviewed cumulative                 90
cumulative NEW_CANONICAL preauthority             199
historical <0.35 tail remaining                 1199
zero-exact-city lane remaining                   395
H-ID allocations                                   0
canonical ID reservations                          0
```

B07 and B08 both resolved ten zero-city candidates each as preauthority-only decisions. B09 is persisted in `docs/state/CRM_CURRENT_UNRESOLVED_LT350_B09_2026-09-10.json` and adds a critical locality-normalization finding: source `Seehotel Wilerbad` / `Wilen (Sarnen)` is the same-property candidate as canonical `H-0681 Seehotel Wilerbad Seminar & Spa` / `Wilen`, so the zero-city anti-join false negative is not treated as a new hotel. B09 otherwise yields seven `NEW_CANONICAL_PREAUTH` and two `NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED` records. All ten remain `RECONCILE_REQUIRED`; terminal mapping delta remains zero.

## Coordination / capability

The bounded token16 writer is excluded from hotel authority mutation, H-ID allocation/reservation and outbound. Drive became unavailable during comparator reread; this wave therefore used the frozen 2061-record Actions artifact plus the Library recovery workbook `CRM_UNIVERSE_STAGING_2026-08-28_v10.xlsx/Canonical_Current` containing all 690 E4 hotel identities. The recovery algorithm reproduced the exact B01..B08 ordered selection before deriving B09, providing a deterministic regression check on the lane reconstruction.

## NEXT

Execute **`CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B10`** from the validated recovery lane: select the next 10 sorted source keys after the first 90, capture exact-current evidence, explicitly test locality aliases before interpreting `same_city=0`, perform generic-name/brand/operator/EGR comparison, and persist PREAUTH decisions only.

Before any new authority transaction, first materialize any reviewed `MATCH_EXISTING_PREAUTH` decisions (including B09 Wilerbad→H-0681) through the separately governed source-mapping terminalization path; do not silently treat a PREAUTH match as a terminal source mapping.

Never reserve/allocate H-IDs here. Keep `OUTBOUND=CLOSED` / `send_allowed=0`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

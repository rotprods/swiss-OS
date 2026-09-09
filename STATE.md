# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-09-10 current-source entity-resolution B07**. Coordination claim: **`CLAIM-CRM-ENTITY-RESOLUTION-016`**, fencing token **16**, PREAUTH SRR decision scope only. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

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

The **authoritative** operational ceiling is E4/690 only. Every current source-review, staging, cache, CI, preauthority decision and canary artifact is non-authoritative until a separately eligible cross-plane authority transaction passes all gates. No source-review result may reserve an H-ID or advance hotel authority.

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
current <0.35 reviewed cumulative                 70
cumulative NEW_CANONICAL preauthority             183
historical <0.35 tail remaining                 1219
zero-exact-city lane remaining                   415
H-ID allocations                                   0
canonical ID reservations                          0
```

B07 is persisted in `docs/state/CRM_CURRENT_UNRESOLVED_LT350_B07_2026-09-10.json`. It consumes `docs/operations/CRM_CURRENT_UNRESOLVED_LT350_B07_EVIDENCE_PACKET_2026-09-01.json` plus `docs/reports/CRM_B07_PREAUTH_COMPARATOR_REVIEW_2026-09-02.md`. Nine rows are typed `NEW_CANONICAL_PREAUTH`; Ô Pied-à-Terre is typed `NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED`; Mövenpick Genève and Hotel Nessi preserve group/operator relationships separately from property identity. All ten remain `RECONCILE_REQUIRED`; terminal mapping delta remains zero.

## Coordination / capability

`CLAIM-CRM-SRR-SPECIAL-006` is superseded. The active bounded writer for this wave is token16 and is explicitly excluded from hotel authority mutation, H-ID allocation/reservation and outbound. GitHub/Actions/current-source research are available. Drive became unavailable during the latest E4 comparator reread, so B08 keys must not be guessed from lexical source ordering alone. The frozen source artifact remains durable and recoverable.

## NEXT

Execute **`RECOMPUTE_CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B08_FROM_FROZEN_SNAPSHOT_AND_E4_CATALOG`**. Reconstruct the remaining zero-exact-city lane deterministically from the frozen 2061-record snapshot anti-joined against the E4/690 canonical catalog, subtract B01..B07, select the next 10 keys, capture current evidence, perform comparator/locality/EGR review and persist PREAUTH decisions only. Never reserve/allocate H-IDs. Keep `OUTBOUND=CLOSED` / `send_allowed=0`.

If Drive remains unavailable, recover an exact E4 catalog from a durable recovery/export artifact; do not infer B08 keys from source-key ordering alone.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

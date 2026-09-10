# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-09-10 current-source entity-resolution B10**. B10 executed under **`CLAIM-CRM-ENTITY-RESOLUTION-017`**, fencing token **17**, PREAUTH locality/SRR decision scope only; token17 is now **RELEASED**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

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

The authoritative operational ceiling remains E4/690. Current-source review, locality normalization, evidence packets, PREAUTH decisions, staging, cache and CI are non-authoritative. They may not allocate/reserve H-IDs or advance hotel authority.

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
prior >=0.60 review                              20 / 20
prior 0.50–0.599999 review                       46 / 46
prior lower49 ordinary review                    47 / 47
lower49 typed SRR materialized                   47 / 47
RAGR evidence-classified                         34 / 34
historical <0.35 previously unreviewed tail     1289
operational zero-exact-city lane                 485
current <0.35 reviewed cumulative                100
cumulative NEW_CANONICAL preauthority             208
historical <0.35 tail remaining                 1189
zero-exact-city lane remaining                   385
H-ID allocations                                   0
canonical ID reservations                          0
```

B10 is persisted in `docs/state/CRM_CURRENT_UNRESOLVED_LT350_B10_2026-09-10.json`; evidence is in `docs/operations/CRM_CURRENT_UNRESOLVED_LT350_B10_EVIDENCE_PACKET_2026-09-10.json`. It yields nine `NEW_CANONICAL_PREAUTH` and one `NEW_ACCOMMODATION_PREAUTH_EGR_REQUIRED` (Vallombrosa). All ten remain `RECONCILE_REQUIRED`; terminal mapping delta remains zero.

## Locality normalization guard

The Wilerbad false-zero failure family is generalized in `src/swiss_os/locality_normalization_guard.py`. Deterministic recovery reconstructs `1438 candidates → 488 literal zero-city → minus 3 exact-global-name cross-locality conflicts → 485 operational zero-city`. Five of the 385 rows remaining after B10 require locality-expanded comparator review. Locality equivalence is review-space only and never auto-binds property identity.

## NEXT

Consume `docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B10.json` exactly for **B11**. It contains ten deterministic source keys and excludes `MD-37df0d95a87f101c1916 Hotel Du Lac / Därligen`, which belongs to the separate exact-global-name locality-conflict lane.

Before B11 begins, deterministic V2 coordination projections must show token17 released, zero token17 active writers, and fencing high-watermark at least 17. Any successor material writer must use a new globally unique session and fencing token >17.

Run locality guard → exact-current evidence → canonical comparator/locality review → operator/group/EGR review → PREAUTH disposition. Before any authority transaction, terminalize reviewed `MATCH_EXISTING_PREAUTH` records only through the separately governed source-mapping transaction. Never reserve/allocate H-IDs here. Keep `OUTBOUND=CLOSED` / `send_allowed=0`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

# STATE — LIVE HANDOFF POINTER

Latest reconstructed frontier: **2026-09-10 current-source entity-resolution B10**. B10 executed under **`CLAIM-CRM-ENTITY-RESOLUTION-017`**, fencing token **17**, with PREAUTH locality/SRR decision scope only. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Authority materialized SHA: **`70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`**.

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

The Wilerbad false-zero failure family is now generalized in `src/swiss_os/locality_normalization_guard.py` and protected by regression tests. Deterministic recovery from the current 2061-record source snapshot and the 690-row E4 canonical catalog reconstructs:

```text
candidate universe                         1438
raw literal zero-city                       488
exact-global-name locality conflicts          3
operational zero-city lane                   485
B01..B09 reproduced exactly                   90
remaining after B09                          395
locality-expanded review findings              5
```

The three exact-global-name locality conflicts are excluded from zero-city novelty and require a separate identity/locality review. The five remaining locality-expanded findings are review-space candidates only; locality equivalence never proves same-property identity and never auto-binds.

## Recovery / capability

Drive was intermittently unavailable during this wave. Reproducible recovery used the frozen current source snapshot plus Library workbook `CRM_UNIVERSE_STAGING_2026-08-28_v10.xlsx/Canonical_Current@690`. The reconstruction reproduces the historical 485 lane and B01..B09 ordering before deriving B10, so the fallback is evidence-backed rather than guessed.

## NEXT

The authoritative bounded next packet is:

`docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B10.json`

Execute **`CURRENT_UNRESOLVED_LT350000_ZERO_CANONICAL_CITY_B11`** over its exact ten source keys. Run the locality guard before interpreting zero-city, capture exact-current evidence, preserve operator/group/EGR relationships separately from property identity and persist PREAUTH decisions only.

`MD-37df0d95a87f101c1916` Hotel Du Lac / Därligen is intentionally excluded from B11 because it is an exact-global-name locality conflict and belongs to a separate conflict-review lane.

Before any authority transaction, terminalize reviewed `MATCH_EXISTING_PREAUTH` records (including B09 Wilerbad → H-0681) only through the separately governed source-mapping transaction. Never reserve/allocate H-IDs here. Keep `OUTBOUND=CLOSED` / `send_allowed=0`.

**VERIFY LIVE TRUTH BEFORE EXECUTION.**

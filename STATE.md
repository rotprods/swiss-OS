# STATE — LIVE HANDOFF POINTER

Latest manual chained Meta Execution reconciliation: **2026-08-29T00:36:00Z**.  
GitHub parent for this wave: **`e0729f8823c8bad78ddbfb3cd1f76f130534499b`**.  
Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**.  
Open GitHub issues labelled `P0`: **0**.  
Frozen current CRM source snapshot: **`HS-MEMBER-DE-33206402141`**.

## 1. Authoritative operational state — unchanged

```text
physical HOTELS rows            690
active canonical                690
persisted H-ID alias edges        0
ASR-1.0                         EXACT
HOTEL_INTELLIGENCE_V1           690 / 690
Graph HOTEL nodes               690 / 690
Graph INTEL nodes               690 / 690
HAS_INTELLIGENCE edges          690 / 690
L4                              105 / 690
CP-0750                         690 / 750
next physical ID                H-0691 UNALLOCATED
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Immutable V13 base SHA-256: `0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5`. Repaired constrained-parent SHA-256: `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, provider responses, canaries and recovery copies remain non-authoritative.

## 2. Qualified current source and immutable intake lineage

```text
snapshot                         HS-MEMBER-DE-33206402141
source pages                     172
source records                   2061
unique detail URLs               2061
CMI ACTIVE_MATCH                 623
CMI TRUE_MISSING                1438
CWP MATCHED_EXISTING             623
CWP VERIFY_NEW_ENTITY           1438
CWP packet SHA-256        2741ca3b870c83d5fe424243bb06f599a96517f5922ec13bdc6621252b3273c0
CWP JSON SHA-256          60ecb59fb8947aee90267c777792fa51238e4bd19bb6e6a993c64cdeb8587b1d
```

Deterministic reconstruction remains 623 exact matches / 1438 candidates / 0 conflicts. Persisted slices through SUB0014 are contiguous with the recovered immutable candidate ordering.

## 3. Source mapping frontier — pre-authority

```text
base terminal mappings                  624
base RECONCILE_REQUIRED                1437
SMO overlay terminal deltas               3
effective terminal mappings             627
effective RECONCILE_REQUIRED           1434
effective terminal coverage         30.422125%
reverse authority/source gaps            66
overlay SHA-256                  e5ed0c76dd84e630679007e9cf209c1239dc68660c1b2c5158798f1302d4aa87
```

The three evidence-reviewed MATCH_EXISTING overlays remain pre-authority source mappings only. Deterministic exact name+city/detail-slug checks across the first 260 verified candidates found no additional unambiguous existing-authority match; no heuristic mappings were created.

## 4. Exact-current verification frontier

SUB0014 completed successfully under GitHub Actions run `33223811133` / job `99023293128`:

```text
ECV verified frontier             280 / 1438
ECV remaining never verified     1158
pending requeue                     0
SUB0014 items                     20 / 20 CURRENT_DETAIL_VERIFIED
SUB0014 packet SHA-256     69b1c3ce896a09d665eec50631d62d49dbaba380fff0c87236c16438218978c4
SUB0014 artifact SHA-256   c63ad21e6e63c588b2e70e6774ff08f263041e28638ebb2040a8f74fd1370a4d
```

Durable summary: `docs/state/ECV_BATCH_0001_SUB0014_RESULT.json`.

SUB0015 is staged at original candidate offset 280..299, first key `MD-2cbc6e20f928c70951c5`, last key `MD-2fdd70a1747ea2bb590b`, items SHA `d96da1ed470698a492f7d0f5c61a0a8c8400a5cd630492b461a6f3af8ed021db`. It remains evidence-only until the live exact-current canary succeeds.

## 5. Protocol / capability state

```text
MEP-2.0 / COLETTE / WOP                  ACTIVE
ASR-1.0                                  EXACT
SSR-1.0 / SRR-1.1                        AVAILABLE
SMO-1.0                                  ACTIVE PRE-AUTHORITY
handoff frontier guard                   ACTIVE IN CI
GitHub branch/PR/CI/review/merge          AVAILABLE
Drive + native Sheets                     AVAILABLE
qualified current-source canary           AVAILABLE
discover.swiss subscription key           UNAVAILABLE / MEP FALLBACK ACTIVE
```

## 6. NEXT

```text
run ECV SUB0015
→ persist result and advance evidence frontier only if verification succeeds
→ continue bounded untouched CWP slices while provider pacing remains healthy
→ entity-resolve verified candidates and add only evidence-proven MATCH_EXISTING mappings
→ replay/materialize all 2061 source mappings
→ resolve reverse gaps 66
→ RECONCILE_REQUIRED = 0
→ SSR-1.0
→ only then construct an authority-eligible DB → HOTELS_MASTER → Intelligence → Graph transaction
```

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
CRM_UNIVERSE_COMPLETE = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```

Canonical continuation pointer: `docs/state/NEXT.json`.

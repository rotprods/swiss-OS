# STATE — LIVE HANDOFF POINTER

Latest manual chained Meta Execution reconciliation: **2026-08-29T00:24:00Z**.  
GitHub parent for this wave: **`00872281c4c6360e9fbfee8da8381c1dac810fee`**.  
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

Deterministic reconstruction remains 623 exact matches / 1438 candidates / 0 conflicts. Persisted slices through SUB0012 are contiguous with the recovered immutable candidate ordering.

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

The three evidence-reviewed MATCH_EXISTING overlays remain pre-authority source mappings only. SUB0012 verification did not itself create a terminal source mapping.

## 4. Exact-current verification frontier

SUB0012 completed successfully under GitHub Actions run `33223253058` / job `99021620627`:

```text
ECV verified frontier             240 / 1438
ECV remaining never verified     1198
pending requeue                     0
SUB0012 items                     20 / 20 CURRENT_DETAIL_VERIFIED
SUB0012 packet SHA-256     f747c586f6631908b8da3fe5b346759413b01c1e2bf3ae46ef0418f8ed48f4b8
SUB0012 artifact SHA-256   529dec141cb42ab6bf313ef2020654436c16325912cbb344de81ae736e562e51
```

Durable summary: `docs/state/ECV_BATCH_0001_SUB0012_RESULT.json`.

SUB0013 is staged at original candidate offset 240..259, first key `MD-26d6ac303682d57e316c`, last key `MD-29671ff37e9eb4c0f842`, items SHA `8b43efd4a1b3af46c4d6a830944b5bc8279f2c391ae36d01150b29e9cd9bf2b3`. It remains evidence-only until the live exact-current canary succeeds.

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
run ECV SUB0013
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

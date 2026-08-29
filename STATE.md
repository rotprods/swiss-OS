# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T01:58:00Z**.  
GitHub parent for this wave: **`b1ff292d4fadb886401a9eef3e500a4624bc41d6`**.  
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
next physical ID                H-0691 UNALLOCATED
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Immutable V13 base SHA-256: `0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5`. Repaired constrained-parent SHA-256: `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, provider responses, exact-current canary evidence and recovery copies remain non-authoritative. No canonical IDs have been reserved from staging.

## 2. Qualified current source / intake lineage

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

The recovered immutable CWP order is authoritative only for pre-authority work scheduling, never for H-ID allocation.

## 3. Source mapping frontier — pre-authority

```text
effective terminal mappings             627
effective RECONCILE_REQUIRED           1434
effective terminal coverage         30.422125%
reverse authority/source gaps            66
overlay SHA-256                  e5ed0c76dd84e630679007e9cf209c1239dc68660c1b2c5158798f1302d4aa87
```

Exact-current evidence alone never creates a terminal canonical mapping. Entity resolution may add only evidence-proven pre-authority mappings.

## 4. Exact-current verification frontier

The bounded SUB0018 requeue ran under GitHub Actions run `33227654867` / job `99034382133`, artifact `9707422829`. It reproduced the same deterministic provider-record evidence: ten detail URLs returned HTTP 404 on all three attempts and one current detail page matched name but not expected city.

```text
ECV verified frontier             349 / 1438
ECV remaining never verified     1089
CURRENT_DETAIL_NAME_ONLY            1
FETCH_FAILED                       10
all_verified                    FALSE
pending requeue                    0
pending provider-change review    11
next untouched offset            360
SUB0018 requeue packet SHA  4fd6827be5370dfd37b757bac45a757434093490de32a623493daf71ca751268
artifact ZIP SHA            6cc8789e4bae1d500517a9307851dc5f2cc2fadc7f8400d67841510827ff069b
```

Durable summary: `docs/state/ECV_BATCH_0001_SUB0018_REQUEUE01_RESULT.json`.

Blind requeue is exhausted. No hotel absence, novelty, exclusion, alias, terminal mapping, H-ID or authority inference is made from these states.

## 5. Provider-record-change semantics wave

A bounded system-definition change introduces `ECV-PROVIDER-EVIDENCE-1.0` after the raw exact-current fetch. It normalizes only repeated all-attempt HTTP 404 evidence to `CURRENT_DETAIL_URL_NOT_FOUND`; successful-page identity drift routes to `PROVIDER_RECORD_CHANGE_REVIEW`; mixed/transient failures remain `FETCH_FAILED` and requeueable.

The additive `all_terminal` field means every item has non-transient exact-current evidence. It is not equivalent to `all_verified`, source-to-canonical reconciliation, or authority eligibility.

One one-shot semantic canary is staged at `docs/state/CMI_WORK_BATCH_0001_SUB0018_RECLASSIFY01_33206402141.json`, containing exactly the same 11 source records, items SHA `6c8c3fb448f8710e5460e6a91fb538aacd311ef7a9820d31889f9342c2019e34`. It exists only to classify the already-bounded provider evidence under the new semantics after the defining PR passes CI/review and merges.

## 6. Protocol / capability state

```text
MEP-2.0 / COLETTE / WOP                  ACTIVE
ASR-1.0                                  EXACT
SSR-1.0 / SRR-1.1                        AVAILABLE
SMO-1.0                                  ACTIVE PRE-AUTHORITY
handoff frontier guard                   ACTIVE IN CI
GitHub branch/PR/CI/review/merge          AVAILABLE
Drive + native Sheets read plane          AVAILABLE
qualified HotellerieSuisse exact-current AVAILABLE
discover.swiss subscription key           UNAVAILABLE / MEP FALLBACK ACTIVE
```

Structured discover.swiss parity remains independently blocked by `DISCOVER_SWISS_SUBSCRIPTION_KEY`; productive MEP work continues through the qualified HotellerieSuisse directory and coherent 2061-record manifest.

## 7. Gauntlet decision

Repeated 404 is evidence that the recorded provider detail URL is not currently resolving; it is not evidence that the underlying hotel entity is absent. Name/city drift is provider identity-change evidence, not a reason for infinite network retries. Both remain pre-authority and require entity/provider-change review.

The normalizer rejects any packet that attempts `authority_advanced=true`, non-zero H-ID allocation, open outbound, or non-zero send permission. Existing exact-current packet validation runs after normalization and the canonical packet hash is recomputed.

## 8. NEXT

```text
PR/CI/adversarial review/merge ECV-PROVIDER-EVIDENCE-1.0
→ observe auto-triggered SUB0018:RECLASSIFY:0001 canary
→ inspect all_terminal as well as all_verified
→ if all 11 are terminal evidence: persist provider-change queue and continuity-verify/stage SUB0019 offset 360..379
→ if any transient non-terminal state remains: persist exact blocker; continue MEP entity resolution without blind retries
→ continue deterministic entity resolution / source mapping replay
→ resolve reverse gaps 66
→ RECONCILE_REQUIRED = 0
→ SSR-1.0
→ only then construct an authority-eligible DB → HOTELS_MASTER → Intelligence → Graph transaction
```

Recovery candidate for SUB0019 remains non-staged input from closed superseded PR #133 head `dd3d93f28a34b38c843fa93d8e5651bd3dd78dc8`: expected offset 360..379, first `MD-383f381de10462fb0875`, last `MD-3c8d2a88eedd678efa02`, historical items SHA `2e9da88fba2d5fefbc20dfd6fb3876e38823387e3af8262c7496d717c4b0241f`. It must be continuity-verified before reuse and relabelled SUB0019.

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
CRM_UNIVERSE_COMPLETE = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```

Canonical continuation pointer: `docs/state/NEXT.json`.

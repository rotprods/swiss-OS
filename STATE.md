# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-28T22:48:00Z**.  
GitHub parent at wave start: **`0c3770e6226074e846b7526dd521ef63040f85d9`**.  
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

Immutable V13 base SHA-256: `0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5`. Repaired constrained-parent SHA-256: `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. No source/ECV/SRR/overlay wave may advance authority from staging, cache, Library, provider response or canary state.

## 2. Qualified current source

```text
snapshot                         HS-MEMBER-DE-33206402141
Actions capture run             33206402141
artifact                        9700376482
artifact ZIP SHA-256            721f9ff9f84e2d5d9df62c6b22f12e7354cef3a298cb8990be66a202e1e769ce
pages                           172
records                         2061
unique detail URLs              2061
canonical MDM records SHA-256   b02c6fae1215643088eafec0af8b2b139506e4e46dec9e81277a1a9e5e4e897f
canonical MDM manifest SHA-256  e5c7e2d52eed1dd585a9a00f1bd98015997ec902e8890d0abcb89cdc87aeb74f
CMI records SHA-256             22bfc4ee304b37b426e6e8f4da03ca73febc7d2283882caf58fd13edaee5081f
```

Raw pagination metadata drift remains preserved as an observation; HPCB/PCCN/PCF qualified the coherent 2061-record source. discover.swiss subscription access is unavailable, so HotellerieSuisse remains the MEP fallback source rather than idling.

## 3. Source mapping frontier

Pinned base mapping candidate:

```text
source records                         2061
base terminal mappings                  624
base RECONCILE_REQUIRED                1437
base terminal coverage             30.2766%
base candidate SHA-256          2f9413318c410eb0f0443de260213d31e9ab2bdc1058581c0fa9c0340474aa27
anti-join SHA-256               c50a2b2b70677d6651f89e94fe19382d525c72c52111c91b8291c15887729d2a
CWP packet SHA-256              6ae41038683c185a51e482c2f979dc1a52b9348cc172a367bf5dc1311efd9249
reverse authority/source gaps           66  RECONCILE_REQUIRED_NOT_EXCLUSION
```

SMO-1.0 now persists the two previously reviewed `MATCH_EXISTING` transitions as a replayable, pre-authority terminal-mapping overlay:

```text
MD-025e7888dfc33e19723a -> H-0686
MD-0672b5697de8a818d65b -> H-0022
overlay SHA-256                 e966d5ab0e70ce92fc0a690409cd2e910281e3584d09aeb1a098f198bd5bc01e
effective terminal mappings             626
effective RECONCILE_REQUIRED            1435
effective terminal coverage         30.373605%
materialization state            OVERLAY_VALIDATED_BASE_REBUILD_PENDING
```

The overlay is terminal source-mapping state for its two exact source keys, but not canonical authority. The full 2061-record mapping must be replayed/materialized before SSR or authority eligibility.

## 4. Exact-current verification frontier

```text
ECV verified frontier             120 / 1437
ECV remaining never verified      1317
ECV pending requeue                  0
latest batch                       HS-MEMBER-DE-33206402141:WORK:0001:SUB:0006
latest packet SHA-256              9a97b4f1187a8c075e7a8d5c502adbfbf9eb4d76b921d1e1b570ef7ee3ab0308
```

All six persisted ECV waves are evidence-only and preserve `authority_advanced=false`, `h_id_allocations=0`, `OUTBOUND=CLOSED`, `send_allowed=0`.

## 5. CWP recovery diagnostic

The original raw source artifact and current E4 HOTELS_MASTER were physically recovered. Re-running the published `normalize_text` exact name+city semantics produces 623 current exact matches / 1438 candidate rows versus the pinned historical 624 / 1437. Crucially, the reconstructed first 100 candidate rows hash exactly to the historical batch-0001 SHA `458acbb69354bdb00ce4bbf82c6464f4bcb4ea5686919f3daffe6751ce8dabbe`, and all persisted first 120 candidate keys match reconstruction.

Because the single historical classification delta has not yet been identified, ECV SUB0007 is fail-closed: offset 120..139 may not be selected until the discrepancy is resolved or proved to occur after that slice. Durable diagnostic: `docs/state/CWP_RECOVERY_DIAGNOSTIC_2026-08-29.json`.

## 6. Protocol / capability state

```text
MEP-2.0 / COLETTE / WOP                  ACTIVE
ASR-1.0                                  EXACT
SSR-1.0 / SRR-1.1                        AVAILABLE
SMO-1.0                                  ACTIVE PRE-AUTHORITY
handoff frontier guard                   ACTIVE IN CI
GitHub branch/PR/CI/review/merge          AVAILABLE
Drive + native Sheets                     AVAILABLE
web/current-source research               AVAILABLE
discover.swiss subscription key           UNAVAILABLE / NON-BLOCKING FALLBACK
Library historical staging                NON-AUTHORITATIVE
```

## 7. NEXT

```text
identify the one-record 623/1438 vs 624/1437 anti-join delta
→ reproduce pinned CWP lineage or prove delta position
→ recover untouched CWP offset 120..139
→ ECV SUB0007
→ entity resolution / SMO terminalization
→ replay/materialize full source mapping
→ resolve reverse gaps 66
→ RECONCILE_REQUIRED = 0
→ SSR-1.0
→ only then construct an authority-eligible cross-plane candidate
```

If exact CWP lineage remains unavailable, continue safe entity resolution on already verified ECV records and persist further SMO overlays; do not idle and do not allocate H-IDs.

Canonical continuation pointer: `docs/state/NEXT.json`.

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
CRM_UNIVERSE_COMPLETE = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```

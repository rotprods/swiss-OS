# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-28T23:12:00Z**.  
GitHub parent for this wave: **`808a4097a4bdaa2b2dff77c3b779f576f72154a4`**.  
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

Immutable V13 base SHA-256: `0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5`. Repaired constrained-parent SHA-256: `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging, cache, provider response, Library and canary state are never authority parents.

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

discover.swiss subscription access remains unavailable. MEP therefore continues with the qualified HotellerieSuisse member-directory source instead of idling.

## 3. Immutable CMI/CWP lineage recovered

Durable Drive evidence plus deterministic replay establish the original intake frontier as:

```text
CMI ACTIVE_MATCH                        623
CMI TRUE_MISSING                      1438
CWP MATCHED_EXISTING                   623
CWP VERIFY_NEW_ENTITY                 1438
CWP packet internal SHA-256     2741ca3b870c83d5fe424243bb06f599a96517f5922ec13bdc6621252b3273c0
CWP JSON file SHA-256           60ecb59fb8947aee90267c777792fa51238e4bd19bb6e6a993c64cdeb8587b1d
```

The later 624/1437 source-mapping frontier is downstream reconciliation state and must not be used as immutable CWP ordering. A fresh replay of all 2061 source records against the 690-row E4 authority reproduces 623 exact matches / 1438 candidates / 0 conflicts. Reconstructed offset 100..119 hashes exactly to persisted SUB0006 (`085f20a4...`), proving offset 120..139 lineage-safe. Recovery proof: `docs/state/CWP_LINEAGE_RECOVERY_2026-08-29.json`.

## 4. Source mapping frontier — pre-authority

```text
base terminal mappings                  624
base RECONCILE_REQUIRED                1437
base candidate SHA-256          2f9413318c410eb0f0443de260213d31e9ab2bdc1058581c0fa9c0340474aa27
SMO overlay terminal deltas               2
effective terminal mappings             626
effective RECONCILE_REQUIRED           1435
effective terminal coverage         30.373605%
reverse authority/source gaps            66
```

Persisted SMO terminal overlays remain: `MD-025e7888dfc33e19723a -> H-0686` and `MD-0672b5697de8a818d65b -> H-0022`. They are source-mapping state only and do not mutate E4 authority.

## 5. Exact-current verification frontier

SUB0007 completed successfully under GitHub Actions run `33219437882`:

```text
ECV verified frontier             140 / 1438
ECV remaining never verified     1298
pending requeue                     0
SUB0007 items                     20 / 20 CURRENT_DETAIL_VERIFIED
SUB0007 packet SHA-256     27c38cef2683117a03eb12b763a8effe77fc7b8164f32c19ad15791b7f66f08a
SUB0007 artifact SHA-256   8506a4abda5040ee27ec40e0f95e56c3704529b0dce40ccf83ce2fe6ed9784d7
```

SUB0008 is staged at original candidate offset 140..159, first key `MD-168e2b3d43460de6bba5`, last key `MD-1a18386074be6c3b0ac5`, items SHA `c0d17f777222399794f2e92d628674967d6b3aa973b4a6eba351b2558e4ed436`. It remains evidence-only until the live exact-current canary succeeds.

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
discover.swiss subscription key           UNAVAILABLE / MEP FALLBACK ACTIVE
Library historical staging                NON-AUTHORITATIVE
```

## 7. NEXT

```text
run ECV SUB0008
→ persist ECV result and advance evidence frontier only if 20/20 verifies
→ continue bounded untouched CWP slices while provider pacing remains healthy
→ entity-resolve verified candidates and persist SMO terminal overlays
→ replay/materialize full 2061-record source mapping
→ resolve reverse gaps 66
→ RECONCILE_REQUIRED = 0
→ SSR-1.0
→ only then construct an authority-eligible cross-plane candidate
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

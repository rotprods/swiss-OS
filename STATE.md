# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-28T23:53:00Z**.  
GitHub parent for this wave: **`1a2b7f6d9e4e46e57ebd2e39cb17b29c30e98c0b`**.  
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

The later 624/1437 source-mapping frontier is downstream reconciliation state and must not be used as immutable CWP ordering. A fresh replay of all 2061 source records against the 690-row E4 authority reproduces 623 exact matches / 1438 candidates / 0 conflicts. Reconstructed offsets 100..179 hash exactly to persisted SUB0006..SUB0009, proving the current immutable continuation. Recovery proof: `docs/state/CWP_LINEAGE_RECOVERY_2026-08-29.json`.

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

SUB0009 completed successfully under GitHub Actions run `33221492594`:

```text
ECV verified frontier             180 / 1438
ECV remaining never verified     1258
pending requeue                     0
SUB0009 items                     20 / 20 CURRENT_DETAIL_VERIFIED
SUB0009 packet SHA-256     047e1f06dd924377104560cd3a6942f96e6147c7d524679c4fcbebd54dd6b79f
SUB0009 artifact SHA-256   7b4ae910716f3e3a7af88dbe4a646ec9146d0833f7da206816dd8423cd62ea2e
```

SUB0010 is staged at original candidate offset 180..199, first key `MD-1d9dde7e3f8c5fa1cbe0`, last key `MD-20a7100c59ab78d21080`, items SHA `71e775b1e87b5680dc59b7ce6fbc84245fb36539a1882cee53bd0c5b2bb37b81`. It remains evidence-only until the live exact-current canary succeeds.

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
run ECV SUB0010
→ persist ECV result and advance evidence frontier only if 20/20 verifies
→ continue bounded untouched CWP slices while provider pacing remains healthy
→ entity-resolve verified candidates and persist only base-membership-proven SMO terminal overlays
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

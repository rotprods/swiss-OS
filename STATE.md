# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-28T20:52:30Z**.  
Reconstructed GitHub `main`: **`7c667b94a7460ea2262dc0d12ba983eeb124863b`**.  
Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**.  
Open GitHub issues labelled `P0`: **0**.  
CRM source snapshot: **`HS-MEMBER-DE-33206402141`**.

## 1. Authoritative operational state

Issue #89 is recovered and closed. Authority remains the semantically reconciled E4 state established by ASR/ARR/CCP and the HOTELS_MASTER cross-plane transaction:

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

Immutable V13 base SHA-256 remains `0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5`; deterministic repaired constrained-parent materialization SHA-256 remains `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. No source/candidate/ECV wave below has allocated an H-ID or changed this authority.

## 2. Coherent current HotellerieSuisse source — QUALIFIED

PR #97 merged HSLCA/MDC/HPCB/PCCN source acquisition as `f4225a56ff431e5a92c98a104d4df418010a13d1`.

Live evidence:

```text
Actions run                     33206402141
job                             98968446260
artifact                        9700376482
artifact ZIP SHA-256            721f9ff9f84e2d5d9df62c6b22f12e7354cef3a298cb8990be66a202e1e769ce
capture_id                      HS-MEMBER-DE-33206402141
contiguous pages                172
materialized records            2061
unique detail URLs              2061
non-last partition size         12
terminal partition size           9
pagination observations         171×172 pages; page 170 alone reported 171
PCCN consensus                  171/172 = 99.4186%
```

Raw HSLCA correctly failed closed on `REPORTED_RECORDS_UNRESOLVED` + `PAGE_COUNT_DRIFT:171,172`. HPCB proved current-run checkpoint provenance. PCCN-1.0 accepted only the bounded one-page stale metadata shape while preserving the raw page-170 observation; PCF core then passed exact positions/cardinality/unique-detail checks. The temporary live push trigger was removed before merge.

Drive acceptance artifact: `HSLCA_LIVE_ACCEPTANCE_33206402141`, ID `1bcIj_Ab2ajjjND3n7p9ES2IDjp7_Jy81S-IFn9LtlCI`.

## 3. Canonical MDM + CMI — COMPLETE PRE-AUTHORITY

PR #99 merged HCMA-1.0 as `ec5201760f1c6fd7cb5f31f00e8b52935f0e0da3`. HCMA converts the qualified HSLCA/PCF bundle into the canonical `MEMBER-DIRECTORY-1.0` contract only after exact capture↔manifest lineage, page, URL, identity and HPCB timestamp checks.

Canonical MDM:

```text
snapshot_id                     HS-MEMBER-DE-33206402141
records_count                   2061
partitions                      172
coverage_complete               TRUE
duplicate record IDs              0
duplicate detail URLs             0
duplicate normalized name+city    0
post-observation records          0
records_sha256                  b02c6fae1215643088eafec0af8b2b139506e4e46dec9e81277a1a9e5e4e897f
manifest_sha256                 e5c7e2d52eed1dd585a9a00f1bd98015997ec902e8890d0abcb89cdc87aeb74f
```

CMI export:

```text
exported records                2061
records_sha256                  22bfc4ee304b37b426e6e8f4da03ca73febc7d2283882caf58fd13edaee5081f
attestation_sha256              e0e1bfa992c78e9b3eb080f24dbc6a53d36b39a66bdc2d7272a985efe1ddfea0
attestation state               DIRECTORY_COMPLETE_SSR_PENDING
```

Drive control summary: `CMI_HSLCA_2061_PREAUTH_SUMMARY_2026-08-28`, spreadsheet ID `1-n34KObY-1AUv6AB8Tm7Mzp2WHDk2f_d0OoVqeITm94`.

## 4. Current-authority anti-join + CWP

The 2,061-source-record CMI candidate universe was compared against the current E4 690-canonical HOTELS_V2 set without allocating IDs.

```text
source records                  2061
MATCH_EXISTING_CANONICAL         624
CANDIDATE_NEW_ENTITY_PREAUTH    1437
exact-match conflicts              0
anti-join payload SHA-256       c50a2b2b70677d6651f89e94fe19382d525c72c52111c91b8291c15887729d2a
```

The reverse anti-join finds **66** current E4 canonical identities without an exact current source match. They remain `RECONCILE_REQUIRED_NOT_EXCLUSION`; no absence from the new source snapshot is interpreted as an exclusion without entity/scope evidence.

CWP frontier:

```text
terminal exact existing matches  624
active VERIFY_NEW_ENTITY work    1437
batches at size 100                15
CWP packet SHA-256              6ae41038683c185a51e482c2f979dc1a52b9348cc172a367bf5dc1311efd9249
```

PR #101 merged CWP-1.1 on the concurrent ancestry before current `main`; it makes canonical CMI `TRUE_MISSING` directly executable as `VERIFY_NEW_ENTITY` while preserving the hard rule that this is routing only, never proof of a new canonical entity.

Source-mapping candidate state:

```text
ACTIVE_CANONICAL                 624
RECONCILE_REQUIRED              1437
terminal coverage          624 / 2061 = 30.2766%
unmapped source records            0
```

`unmapped=0` does not mean completion: `RECONCILE_REQUIRED` must also reach zero.

## 5. Exact-current verification frontier

PR #102 merged the reusable manual ECV runner and first CWP-derived subbatch as `7c667b94a7460ea2262dc0d12ba983eeb124863b`.

Live subbatch evidence:

```text
batch_id                        HS-MEMBER-DE-33206402141:WORK:0001:SUB:0001
records attempted                 20
CURRENT_DETAIL_VERIFIED           20
all_verified                    TRUE
input items SHA-256             82a58723a538e0c33c5e501f5896dad060f09fc37d775454f6d5b2e0b2b48f0c
ECV packet SHA-256              0b0d10ac7fbe118fcbdf434b89b298759e911dda3c9adf5d11124f462b435586
remaining unverified candidates 1417
```

Run `33209778218` / job `98979875797` passed ECV verification, packet validation and safety assertions. Its overall run was marked failed only by the final hidden-directory artifact upload; the merged workflow fixes retention with `include-hidden-files: true` and has no automatic push trigger.

`CURRENT_DETAIL_VERIFIED` is evidence, **not** a terminal source mapping. The 20 verified records remain in the 1,437-record entity-resolution frontier until proven existing, new, renamed/merged, or excluded with reason.

## 6. Parallel exact-current fallback evidence

Batches 01–08 remain read-only evidence debt reduction:

```text
records attempted                         96
current exact member detail               78
current non-exact support/scope            6
unresolved / stale refresh required       12
canonical H-ID reservations                0
authority advancement                      0
outbound                                    0
```

They may assist entity resolution but cannot supersede the coherent frozen source or independently promote authority.

## 7. Capability / blocker state

```text
GitHub read/write/CI                         AVAILABLE
web/current-source research                  AVAILABLE
Drive read/write                             AVAILABLE
native Google Sheets mutation                AVAILABLE
HOTELS_MASTER current E4                     AVAILABLE
coherent HotellerieSuisse capture            AVAILABLE / QUALIFIED
discover.swiss subscription key              UNAVAILABLE
open GitHub P0 issues                        0
```

The missing discover.swiss credential is now an alternate-source limitation, not a blocker on productive CRM work because the current HotellerieSuisse source universe is qualified.

## 8. Current MEP route

Highest-value safe route:

```text
ECV remaining 1417 candidate records
→ entity resolution against E4 + exact-current evidence
→ source-mapping terminalization
→ resolve 66 reverse anti-join authority/source discrepancies
→ ACTIVE_CANONICAL | ALIAS_TO_CANONICAL | EXCLUDED_WITH_REASON for every source record
→ RECONCILE_REQUIRED = 0
→ source-scope reconciliation / SRR
→ authority-eligible candidate only then
```

No source candidate may reserve `H-0691` or any later ID. A later authority mutation must be a new bounded transactional DB → HOTELS_MASTER → Intelligence → Graph → scheduler/checkpoint/metrics/SLO reconciliation with ASR and restore/replay/idempotency gates.

## 9. Durable NEXT

Canonical continuation pointer: `docs/state/NEXT.json`.

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
CRM_UNIVERSE_COMPLETE = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```

A subsequent activation must reread fresh `main`, verify E4 690/690/0 aliases, then continue ECV/entity-resolution/source-mapping work rather than restarting source acquisition.

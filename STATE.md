# STATE — LIVE HANDOFF POINTER

Latest Meta Execution reconciliation: **2026-08-28T18:52:00+02:00**.  
Latest reconstructed GitHub `main`: **`78816d0f53951db1d7e34d0d2ee47200e82bd271`**.  
Latest physically verified constrained parent: **`OPERATIONAL_DB_SHADOW_MANIFEST_V13`**.  
Latest Drive CRM staging: **v11**.  
Latest exact-current evidence frontier: **batch 12**.

## 1. Authoritative operational state

Authority is unchanged by this activation:

```text
entity epoch                    HS_ENTITY_EPOCH_2026-08-25_E4
constrained recovery parent     OPERATIONAL_DB_SHADOW_MANIFEST_V13
constrained parent SHA-256      0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5
physical HOTELS rows            690
superseded duplicate aliases      4
active canonical                686
next physical H-ID              H-0691
Intelligence                    686 / 686
Operational Graph               686 / 686
L4                              105 / 686
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

No historical cache, source capture, staging batch, CMI packet, ECV result, SMC candidate, SRR proposal or PCF source-denominator proof may advance these values by itself. Staging reserves **zero** canonical H-IDs.

## 2. Current P0

GitHub issue `#14` remains the active P0: complete the frozen CRM source universe before outbound can even be evaluated.

Required terminal state:

```text
one coherent frozen/versioned source universe
source scope = EXACT | evidence-backed EXPLAINED
every source record mapped exactly once
unmapped source records = 0
RECONCILE_REQUIRED = 0
unresolved duplicate conflicts = 0
invalid alias targets = 0
DB ↔ HOTELS_MASTER ↔ Intelligence ↔ Operational Graph exact
CRM_UNIVERSE_COMPLETE = TRUE
```

Outbound remains an independent later gate requiring explicit authorization.

The previous native HOTELS_MASTER writer blocker is resolved. Issue `#51` is closed after reversible in-place write/read/delete verification; writer capability does not bypass CUP/WOP authority gates.

## 3. Chained Meta Execution — executable pipeline now on main

This activation moved the source-to-resolution stack materially forward:

```text
MDC-1.0 / member-directory capture       PR #43  d5d5c73b75742f0a78b3fedc81d97e6e9bd48d4a
CWP-1.0 / CMI work packets              PR #46  857c26a3cf4fc73733030ee6187069f933ad5e10
ECV-1.0 / exact-current verification    PR #47  65f0e98cd82ff640022523a779b6785c4144dc85
CWP terminal-state compatibility        PR #77  09f95805e18b9c6847071f02b7129f367eed77c9
SMC-1.0 / exhaustive source mapping     PR #48  ccd15735e82fe22806f28b32ea548d7fc7822fae
SRR-1.0 / resolution review             PR #80  c57b0b391ac0744fd2b4dad082b31c2393295c40
HSLCA-1.0 / resumable live capture      PR #79  b1b0462689aa1a998e832040a37e9bb5a3679505
HSLCA-R1.0 / adaptive provider runtime  PR #82  727d465f86aaf7a23f91c76cd6a349c6d5e27134
SRR-1.1 / transfer hardening            PR #83  3a5b921e824c770480b23c57c43d6737c31f3fe3
MDC-1.1 / live card identity fix        PR #84  9e31fd9563007480a7153eac6166e6fecf0a5447
PCF-1.0 / partition-count finalizer     PR #85  78816d0f53951db1d7e34d0d2ee47200e82bd271
```

Every merged system-definition change passed repository guard, stable-contract guard, unit tests, manifest semantics canary and adversarial review.

Current pre-authority execution chain:

```text
HSLCA-R1.0 / MDC-1.1 current source acquisition
→ MDM complete coherent manifest
→ CMI anti-join
→ CWP deterministic work packets
→ ECV exact-current official verification
→ SMC exhaustive source accounting
→ SRR-1.1 deterministic resolution review
→ bounded authority transaction only after every gate passes
```

`NEW_CANONICAL` in SRR remains authority work only: no H-ID is allocated until the later bounded canonical transaction.

## 4. Live source acquisition findings

### discover.swiss

```text
DISCOVER_SWISS_SUBSCRIPTION_KEY     UNAVAILABLE
valid dsod-hs capture               NOT PRESENT
```

DSA-1.0 remains the preferred structured API path when the credential becomes available. No API data is fabricated.

### HotellerieSuisse live directory

Two real remote MDC canaries were executed.

First canary:

```text
run                              33187779427
result                           FAIL_CLOSED_PROVIDER_RATE_LIMIT
observed pages                   8 / 172
HTTP boundary                    429
```

This directly motivated the adaptive HSLCA-R1.0 provider runtime.

Second canary, using a conservative 3-second delay / 5 attempts:

```text
run                              33188955280
snapshot                         HS-DIRECTORY-DE-20260828T161347Z
robots_allowed                   TRUE
observed pages                   172 / 172
page errors                      0
empty pages                      0
non-last page-size mismatches    0
last page records                9
materialized records             2061
unique detail URLs               2061
duplicate detail URLs            0
card rejects                     0
provider aggregate count         not exposed in server-rendered response
```

The page/topology acquisition was structurally excellent, but artifact QA found an MDC-1.0 entity parser defect: the live cards render **city/locality first and property name last**, while MDC-1.0 assigned those fields in reverse. Therefore this 2061-record artifact is **diagnostic only** and is not accepted for entity resolution or authority.

MDC-1.1 fixes and regression-locks the live card order:

```text
first non-empty card text  → city
last non-empty card text   → property name
href                       → exact member-detail URL
```

## 5. Count-less coherent source support — PCF-1.0

The live directory may expose complete deterministic pagination without an aggregate server-rendered result count. PCF-1.0 now permits a materialized denominator only under strict fail-closed evidence:

```text
sole capture violation = REPORTED_RECORDS_UNRESOLVED
exact page positions = 1..N
same capture_id / locale
all page captured_at timestamps inside the current capture window
no reused stale checkpoint may satisfy a count-less completion claim
no page-count drift
no provider count evidence
all non-last pages share one stable inferred page size
last page contains 1..page_size records
all pages non-empty
unique detail URLs
name/city/evidence/detail fields complete
materialized record parity exact
MDM compiler independently returns coverage_complete=true
```

Provenance remains explicit:

```text
PROVIDER_REPORTED
vs
MATERIALIZED_PARTITION_TOTAL
```

PCF never pretends a materialized total came from the provider.

## 6. Exact-current evidence debt reduced

Batches `05..12` processed **90** additional staged historical identities:

```text
records attempted                                  90
CURRENT_EXACT_MEMBER_DETAIL                        72
exact member-detail identities needing live ECV     8
scope-reconcile / support-only cases               10
canonical H-ID reservations                         0
authority advancement                               0
outbound                                             0
```

Batch SHA-256 values:

```text
05  5ee2b6c4a8bc434b0a4dd9afef5c2f040e54ef0493a60fd5b48b4a57faf3adf1
06  e2e9a0dc3e0bc03139395e20e075d21e6338f43e53aa2ad92d80b84cf0eb91ec
07  ab363402e934edd757464669f6b1b1281af50cc38713e2aab8696c06bdf0ce6b
08  6509daa21cc78f4241b8909eb50c4cdcabefc38cbd310006145c9ad43a51aaf2
09  3bad3b5bf2d6691152814d80f6e7038eec2ab3400d59c6a14e28461a82d47975
10  d7687da0feca76a8e1f2fd4934227855aec86d59ac3da840de44f2a85930a1db
11  0b7b0b4da8cad38e74d34997600934a874bfd40b0959734952407addf0b54c36
12  4e054d6df87b09ea51312a7f44a7a24629d1acdd00f6cf24c8c628a7128f23e0
```

Blank worksheet rows are not inferred as missing hotels. Continue from actual populated unprocessed rows only.

## 7. Runtime capability

```text
GitHub read/write/CI                       AVAILABLE
web research                               AVAILABLE
authenticated Drive read                   AVAILABLE
Drive/Docs durable handoff writes          AVAILABLE
native HOTELS_MASTER in-place Sheets write AVAILABLE / reversible canary verified
HSLCA-R1.0 provider-aware acquisition      AVAILABLE
Library durable write                      not proven in this activation
```

Do not claim Library synchronization unless an actual write actuator is available and succeeds.

## 8. Current MEP route

The next highest-value safe route is:

```text
FRESH_HSLCA_COHERENT_CAPTURE
→ PCF-1.0 only if provider aggregate count remains absent
→ MDM
→ CMI
→ CWP
→ ECV
→ SMC
→ SRR-1.1
```

A fresh count-less PCF completion claim must use pages captured inside one current capture window; stale resume checkpoints are recovery/progress evidence but cannot silently become a coherent current denominator.

Because the provider was exercised heavily in this activation, the next source acquisition should re-enter through HSLCA-R1.0's provider-safe adaptive path rather than immediately hammering the directory again. Productive fallback remains exact-current/ECV/SRR evidence reduction.

SSR-1.0 still requires the structured discover.swiss side or another explicitly contract-valid evidence-backed source-scope path.

## 9. Durable NEXT

Canonical machine-readable pointer: `docs/state/NEXT.json`.

Permissions remain:

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
```

## 10. Production objective

```text
fresh coherent current HSLCA capture
→ provider count if present OR strict PCF materialized denominator
→ MDM coverage_complete=true
→ acquire discover.swiss dsod-hs when credential becomes available
→ SSR EXACT | evidence-backed EXPLAINED
→ CMI → CWP → ECV → SMC → SRR
→ unmapped=0
→ RECONCILE_REQUIRED=0
→ re-read live E4/V13-or-successor parent and concurrency anti-join
→ constrained DB authority transaction
→ HOTELS_MASTER by PK
→ Intelligence
→ Operational Graph
→ observability / scheduler / transitions / recovery
→ final exact reconciliation
→ CRM_UNIVERSE_COMPLETE=TRUE only when every gate passes
```

`OUTBOUND` remains separately CLOSED.

# STATE — LIVE HANDOFF POINTER

Latest Meta Execution reconciliation: **2026-08-28T18:24:00+02:00**.  
Latest reconstructed GitHub `main`: **`ccd15735e82fe22806f28b32ea548d7fc7822fae`**.  
Latest physically verified constrained parent: **`OPERATIONAL_DB_SHADOW_MANIFEST_V13`**.  
Latest Drive CRM staging: **v11**.  
Latest exact-current frontier in this activation: **batch 12**.

## 1. Authoritative operational state

Authority has **not** advanced during this activation:

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

No research batch, source canary, historical cache, CMI packet, ECV result or SMC candidate is authority by itself. Staging reserves **zero** H-IDs.

## 2. CRM-universe completion contract

Outbound cannot even be evaluated until one explicitly frozen/versioned source universe is fully reconciled and every source record maps exactly once to a terminal state.

```text
source scope = EXACT | evidence-backed EXPLAINED
unmapped source records = 0
RECONCILE_REQUIRED = 0
unresolved duplicate conflicts = 0
invalid alias targets = 0
DB / HOTELS_MASTER / Intelligence / Operational Graph = exact
CRM_UNIVERSE_COMPLETE = TRUE
```

Even after that, outbound remains independently gated and requires explicit authorization.

## 3. Meta Execution / executable source pipeline

Canonical continuity remains:

```text
MEP-2.0 → NPP-1.0 NEXT → WOP-1.1 → PRG gauntlet → persistence → NEXT → repeat
```

The executable pre-authority source pipeline materially advanced in this activation:

```text
MDC-1.0  PR #43 → d5d5c73b75742f0a78b3fedc81d97e6e9bd48d4a
CWP-1.0  PR #46 → 857c26a3cf4fc73733030ee6187069f933ad5e10
ECV-1.0  PR #47 → 65f0e98cd82ff640022523a779b6785c4144dc85
CWP compat PR #77 → 09f95805e18b9c6847071f02b7129f367eed77c9
SMC-1.0  PR #48 → ccd15735e82fe22806f28b32ea548d7fc7822fae
```

Each merged change passed repository guard, stable-contract guard, unit tests, manifest canary and adversarial review.

Pipeline semantics now exist end to end up to pre-authority exhaustive accounting:

```text
coherent member-directory capture (MDC)
→ MDM / source-scope evidence
→ CMI anti-join decisions
→ deterministic CWP work packets
→ exact-current official verification (ECV)
→ exhaustive source mapping candidate (SMC)
→ terminalization / constrained authority promotion only when all gates pass
```

SMC may legitimately reach `unmapped=0` while `RECONCILE_REQUIRED>0`; that state is still incomplete and cannot promote CRM authority.

## 4. Source acquisition capability

### discover.swiss structured path

```text
DISCOVER_SWISS_SUBSCRIPTION_KEY     UNAVAILABLE
valid dsod-hs capture               NOT PRESENT
```

DSA-1.0 remains preferred when the key becomes available. No API data is fabricated.

### HotellerieSuisse member-directory path

MDC-1.0 is now merged and a remote read-only actuator is under PR #78.

First live canary result:

```text
run                              33187779427
snapshot                         HS-DIRECTORY-DE-20260828T155917Z
robots_allowed                   TRUE
max_page                         172
observed_pages                     8
page_errors                      164
unique_records                    96
mdm_coverage_complete            FALSE
violation                        PARTITION_COVERAGE_MISMATCH
root cause                       provider HTTP 429 after page 8
manifest SHA-256                 48053c711e1b1e32e37ddcc7cabddd1514d92b8843760886000e0825962b65a6
```

This failed closed exactly as required: authority/H-ID/outbound values remained unchanged. The actuator was then adapted conservatively to a 3-second inter-request delay and 5 attempts.

Second rate-limit-aware canary:

```text
run                              33188955280
head                             44a2ee24a35931fb38fa940ef957f3171114c958
state at this handoff            IN_PROGRESS
```

Until that run finishes and its artifacts pass the MDC/MDM gauntlet, **no coherent complete member-directory snapshot is claimed**. PR #78 must not merge before the live result is reviewed and its branch-only push trigger is removed.

Current indexed directory observations remain evidence only. Different locale/cache epochs have exposed different denominators; page number is never source-record identity.

## 5. Drive / Sheets / persistence capability

```text
authenticated Drive read            AVAILABLE
Drive/Docs durable handoff writes   AVAILABLE
native HOTELS_MASTER Sheets write   AVAILABLE / reversible canary verified
GitHub read/write/CI                AVAILABLE
web research                        AVAILABLE
```

Native Sheets availability removes the old writer blocker but does not authorize promotion before CUP/WOP gates pass.

## 6. CRM staging v11 and exact-current evidence frontier

`CRM_UNIVERSE_STAGING_2026-08-28_v11.xlsx` remains non-authoritative. Direct materialization found **228** `Historical_Missing_Seed` data rows; this is staging observability, not a canonical denominator.

Batches 05–12 executed in this activation over staged historical identities:

```text
records attempted                                  90
CURRENT_EXACT_MEMBER_DETAIL                        72
exact member-detail identities needing live ECV     8
scope-reconcile / support-only cases               10
canonical H-ID reservations                         0
authority advancement                               0
outbound                                             0
```

Artifacts and SHA-256:

```text
batch05  5ee2b6c4a8bc434b0a4dd9afef5c2f040e54ef0493a60fd5b48b4a57faf3adf1
batch06  e2e9a0dc3e0bc03139395e20e075d21e6338f43e53aa2ad92d80b84cf0eb91ec
batch07  ab363402e934edd757464669f6b1b1281af50cc38713e2aab8696c06bdf0ce6b
batch08  6509daa21cc78f4241b8909eb50c4cdcabefc38cbd310006145c9ad43a51aaf2
batch09  3bad3b5bf2d6691152814d80f6e7038eec2ab3400d59c6a14e28461a82d47975
batch10  d7687da0feca76a8e1f2fd4934227855aec86d59ac3da840de44f2a85930a1db
batch11  0b7b0b4da8cad38e74d34997600934a874bfd40b0959734952407addf0b54c36
batch12  4e054d6df87b09ea51312a7f44a7a24629d1acdd00f6cf24c8c628a7128f23e0
```

The processed seed block is non-contiguous in the workbook; blank worksheet rows are not inferred as missing hotels. Later historical seed records remain and must be selected by actual populated rows, not row arithmetic.

## 7. Concurrency / stale-branch hygiene

Stale duplicate branches were removed from the active merge surface:

```text
PR #73 closed — superseded MEP implementation
PR #74 closed — superseded/stale MEP implementation
PR #75 closed — superseded by cleaner MDMA line
```

PR #76 (MDMA recovery adapter) remains open but is **not merge-ready** until strict integer coercion gaps are hardened and it is revalidated against current main. MDC-1.0 is the canonical current acquisition route.

## 8. Current MEP route

Until live canary `33188955280` reaches a terminal reviewed state:

```text
primary dependency     INSPECT_LIVE_MDC_CANARY_33188955280
productive fallback    EXACT_CURRENT_REFRESH
```

If the canary yields a coherent complete manifest:

```text
MDC coherent manifest
→ directory-to-CMI canary / mass anti-join
→ CWP
→ ECV
→ SMC
→ terminal mapping remainder
```

SSR remains blocked until a valid discover.swiss capture exists, unless an evidence-backed source-scope path explicitly satisfies the canonical contract.

If the canary again hits provider throttling, do not hammer the provider. Persist the typed rate-limit boundary and move to resumable/rate-aware acquisition engineering only if epoch coherence can still be proven; otherwise continue exact-current evidence reduction.

## 9. Durable NEXT

Machine-readable continuation pointer: `docs/state/NEXT.json`.

Hard permissions remain:

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
```

## 10. Next production objective

```text
inspect live MDC canary #33188955280
→ if coherent: validate manifest and execute pre-authority directory→CMI→CWP→ECV→SMC chain
→ if throttled: record provider boundary; avoid repeated aggressive capture; use safe acquisition fallback
→ continue exact-current work on populated unprocessed staging records
→ acquire discover.swiss structured snapshot when credential becomes available
→ source-scope reconciliation EXACT | evidence-backed EXPLAINED
→ terminal mappings: unmapped=0, RECONCILE_REQUIRED=0
→ bounded authoritative WOP promotion from current verified parent
→ DB ↔ HOTELS_MASTER ↔ Intelligence ↔ Operational Graph ↔ observability exact
→ CRM_UNIVERSE_COMPLETE=TRUE only after all gates pass
```

`OUTBOUND` remains CLOSED independently.

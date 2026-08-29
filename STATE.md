# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T16:54:00Z**. Parent main SHA: **`4b7a93007aa3cfd823d128e5175bfa92024f6334`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

## Authority — unchanged / locked

```text
physical HOTELS rows            690
active canonical                690
persisted H-ID alias edges        0
ASR-1.0                         EXACT
HOTEL_INTELLIGENCE_V1           690 / 690
Graph HOTEL / INTEL / edges     690 / 690
next physical ID                H-0691 UNALLOCATED
CRM_UNIVERSE_COMPLETE           FALSE
OUTBOUND                        CLOSED
send_allowed                      0
```

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging/materialization/ECV/cache/canary remain non-authoritative. Native Sheets tail rechecked this activation: H-0690 present; H-0691 absent; no authority effect.

## CRM universe / mapping frontier

```text
source pages / records              172 / 2061
ACTIVE_MATCH / TRUE_MISSING          623 / 1438
effective terminal mappings         627
RECONCILE_REQUIRED                  1434
reverse authority/source gaps        66
candidate records                   1438
candidate records SHA               34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0
```

## Exact-current durable frontier — SUB0072 green

SUB0072 ECV Actions `33263846243`, job `99130256763`, artifact `9718048577`, ZIP SHA `31ba2cb871b9832e13200e63fa7f9e1d263ed2c53c7f185c026f2a6ad9236387`; normalized packet SHA `3e10aabd865113adf957b6e7c186cc4b53529bb397c075edd9d4c020487150b2`; 20/20 `CURRENT_DETAIL_VERIFIED`, HTTP/name/city `20/20`, provider changes `0`, validator violations `0`.

```text
ECV verified frontier            1430 / 1438
ECV remaining never verified       8
ECV pending requeue                 0
contiguous candidate prefix       0..1420 (1421 records)
next untouched candidate offset    1421
```

## SUB0073 — final exact materialization verified and staged

Read-only CWP run `33264145969` / job `99131064859` succeeded from main `4b7a93007aa3cfd823d128e5175bfa92024f6334`. Artifact `9718117550`, ZIP SHA `788fa05c0c7f1b2e726c50fe6f7ff9979526d1fcb850eec873036b011a273338`; packet SHA `b34a03112b3d2c047b1685f469c4dbf9b3168820251ec99e2755fccc67efe285`; report SHA `03cd7cd08d2303b74feb890ce823010c1ac71514e9c5e0aa66d8bcd1e18ed0d6`; items SHA `d998657e8ea03c057d6a46af6366ddf5d1b890eab7592612729943e1aa0ffbdd`. Exact immutable offsets **1421..1428**, 8 items. All are `CANDIDATE_NEW_ENTITY_PREAUTH` / `VERIFY_NEW_ENTITY`; every `matched_hotel_id` is empty. `authority_advanced=false`, `h_id_allocations=0`, OUTBOUND=CLOSED, `send_allowed=0`.

## Hard gates / NEXT

After green CI + adversarial review, merge this staging only to trigger read-only SUB0073 ECV. Persist typed ECV evidence before any entity-resolution or terminal-mapping wave. SSR-1.0 remains blocked on missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. MEP fallback remains qualified member-directory + exact-current without claiming API equivalence. Issue #14 controls the P0. Before authority eligibility require SSR-1.0, `RECONCILE_REQUIRED=0`, reverse gaps=0, full 2061 terminal mappings and fresh DB↔Sheets↔Graph↔Intelligence reconciliation.

Drive recovery doc: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. HOTELS_MASTER: `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`. File Library is cold recovery and lags GitHub main.

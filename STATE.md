# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T04:47:25Z**. Parent main SHA: **`29812585f14b0793e9c65ac9dd1f6d20b1aaa4e0`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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

Authority parent SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`; authority workbook recovery SHA `434fab60a1260f08b647e9f6ed718575de195a11fc09177a4c42da84b66b920e`. Live Drive HOTELS_V2 was re-read in this activation: exactly 690 H-ID rows H-0001..H-0690, zero `SUPERSEDED_DUPLICATE`, H-0691 absent. ECV, staging, provider, cache and canary state remain non-authoritative.

## CRM universe / mapping frontier

```text
source pages / records              172 / 2061
ACTIVE_MATCH / TRUE_MISSING          623 / 1438
effective terminal mappings         627
RECONCILE_REQUIRED                  1434
reverse authority/source gaps        66
source artifact                     9700376482
source ZIP SHA                      721f9ff9f84e2d5d9df62c6b22f12e7354cef3a298cb8990be66a202e1e769ce
candidate records                   1438
candidate records SHA               34d9aa9cfa4fe896bf1db8fba4dedfded9a1dbf2e135b847101904644d16bba0
candidate gzip SHA                  071e2cf1b895b63457c56066de7d8653b3182a12d1260ff9be7709a684fcf194
```

The deterministic candidate export remains durable under `docs/state/CRM_CANDIDATE_EXPORT_33206402141.*`, guarded by pinned multipart/gzip and records digests. Discover.swiss structured parity remains blocked by missing `DISCOVER_SWISS_SUBSCRIPTION_KEY`.

## Exact-current frontier — SUB0024R1 green

Actions `33234381770`, job `99052661724`, artifact `9709457433`, artifact ZIP SHA `d58dae872067d9c76dafdfc72f83fb27f4cbb714395def56a6cdee695fda407e`; normalized ECV packet SHA `c02b1b320d9f179baf1ddbf033bd710518ba44b5c77fcdf328be824978726de6`; validator violations `0`.

```text
ECV verified frontier             470 / 1438
ECV remaining never verified     968
ECV pending requeue                 0
contiguous candidate prefix       0..460 (461 records)
```

SUB0024R1 is 1/1 `CURRENT_DETAIL_VERIFIED`, provider-record changes `0`. It verifies the previously skipped original candidate offset 453 (`MD-4ac3fbacbb0490ec9371`, Hotel Stern Chur | Chur). The CWP lineage hole is closed; already-valid offset 460 evidence remains preserved.

## Staged next bounded wave — SUB0025

`SUB0025` contains exact original candidate offsets **461..480** from the same frozen 1,438-record candidate export. Items count `20`; items SHA `15daa56019f9e6017a56338de32a088c33e82b534d41f62783d9edafca2319af`; next untouched forward offset `481`.

This staging reserves/allocates no H-ID, mutates no authority, and cannot be promoted from ECV evidence.

## P0 / NEXT

Open P0s are `EFFECTIVE_RECONCILE_REQUIRED_1434_NOT_ZERO`, `REVERSE_AUTHORITY_SOURCE_DISCREPANCIES_66_REQUIRE_RESOLUTION`, and discover.swiss provider-key absence.

```text
require green repo-guard + adversarial review
→ merge SUB0024R1 persistence / SUB0025 staging wave
→ observe auto SUB0025 ECV
→ validate/persist evidence with authority_advanced=false, h_id_allocations=0, OUTBOUND=CLOSED, send_allowed=0
→ if green, stage original offsets 481..500 as SUB0026
→ if ECV fails, MEP-route to terminal entity-resolution/reverse-gap work
→ require full 2061 mapping replay, RECONCILE_REQUIRED=0, reverse gaps=0 and SSR-1.0 before authoritative cross-plane reconciliation
```

Canonical recovery pointer: `docs/state/NEXT.json`. E4 remains `690/690/0`; `H-0691` remains unallocated.

# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T16:20:00Z**. Parent main SHA: **`caa1d19c869f5b16777965a238844b96e581e917`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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

Authority SHA `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`. Staging/materialization/ECV/cache/canary remain non-authoritative. Native Sheets tail remains H-0690; H-0691 absent; no authority effect.

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

## Exact-current durable frontier — SUB0070 green

SUB0070 ECV Actions `33262497347`, job `99126730847`, artifact `9717669409`, ZIP SHA `f25e4094e20a6ff2f253d9e7214c80e5f1e3ec058f3e60fcbfd10ef5c607f7f1`; normalized packet SHA `1eb2381001809cc88df208d6b0df8bc1b49a31a7b264937db3adc8eea16ab966`; 20/20 `CURRENT_DETAIL_VERIFIED`, HTTP/name/city `20/20`, provider changes `0`, validator violations `0`.

```text
ECV verified frontier            1390 / 1438
ECV remaining never verified      48
ECV pending requeue                 0
contiguous candidate prefix       0..1380 (1381 records)
next untouched candidate offset    1381
```

## NEXT bounded wave — SUB0071

Request immutable read-only CWP materialization for **SUB0071**, offsets **1381..1400**, 20 records. Do not reserve or allocate H-IDs. Validate artifact hashes, stage only through branch→CI→adversarial review→merge, then allow only read-only ECV to advance exact-current evidence.

## Hard gates

SSR-1.0 remains blocked on missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. MEP fallback remains qualified member-directory + exact-current, without claiming API equivalence. Issue #14 controls the P0. Before authority eligibility require SSR-1.0, `RECONCILE_REQUIRED=0`, reverse gaps=0, full 2061 terminal mappings and fresh DB↔Sheets↔Graph↔Intelligence reconciliation. OUTBOUND=CLOSED; send_allowed=0.

Drive recovery doc: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. HOTELS_MASTER: `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`. File Library remains cold recovery only.

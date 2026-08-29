# STATE — LIVE HANDOFF POINTER

Latest chained Meta Execution reconciliation: **2026-08-29T16:38:00Z**. Parent main SHA: **`14041743651b5d59d2408c02baa71edbc9276bca`**. Authority epoch: **`HS_ENTITY_EPOCH_2026-08-25_E4`**. Frozen CRM snapshot: **`HS-MEMBER-DE-33206402141`**.

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

## Exact-current durable frontier — SUB0071 green

SUB0071 ECV Actions `33262956564`, job `99127930033`, artifact `9717797052`, ZIP SHA `0a240300d92c08bf13300896eb51f60daabbdfa3233035684402318256322b20`; normalized packet SHA `e1738ddeb7ecd8f2c6fcf6cf4d496289c97aa7d30d27ed312d1c00abba48dd2d`; 20/20 `CURRENT_DETAIL_VERIFIED`, HTTP/name/city `20/20`, provider changes `0`, validator violations `0`.

```text
ECV verified frontier            1410 / 1438
ECV remaining never verified      28
ECV pending requeue                 0
contiguous candidate prefix       0..1400 (1401 records)
next untouched candidate offset    1401
```

## SUB0072 — exact materialization verified and staged

Read-only CWP run `33263167196` / job `99128476808` succeeded from main `14041743651b5d59d2408c02baa71edbc9276bca`. Artifact `9717836680`, ZIP SHA `b100b62aac8c5abdee42139c5d9b970ad093092ee4152c1870d291d163307fac`; packet SHA `e1c2c58f3b5ae0aca0a6b3afffc288ad9d73fb25f9c506de74b794152e7b9ccb`; report SHA `a72d650bddc9d3209cf179d7d4f2a513fd0931828e142339272b8bf9cd926cc6`; items SHA `fac7cc7446e29f05e1c38a9ed239c912739d67f5221aba8b6cd5ba31762df8de`. Exact immutable offsets **1401..1420**, 20 items. All are `CANDIDATE_NEW_ENTITY_PREAUTH` / `VERIFY_NEW_ENTITY`; every `matched_hotel_id` is empty. `authority_advanced=false`, `h_id_allocations=0`, OUTBOUND=CLOSED, `send_allowed=0`.

## Hard gates / NEXT

After green CI + adversarial review, merge this staging only to trigger read-only SUB0072 ECV. Persist typed ECV evidence separately before selecting the next immutable slice. SSR-1.0 remains blocked on missing discover.swiss `Infocenter Open` subscription key / capture-valid structured API manifest. MEP fallback remains qualified member-directory + exact-current without claiming API equivalence. Issue #14 controls the P0. Before authority eligibility require SSR-1.0, `RECONCILE_REQUIRED=0`, reverse gaps=0, full 2061 terminal mappings and fresh DB↔Sheets↔Graph↔Intelligence reconciliation.

Drive recovery doc: `1leVfYwda8g0B5Co5zaSUIpo245t37tpUEiTaYlLds_s`. HOTELS_MASTER: `1DsO0U4i7aUY4FOF-zldJONQN2StUK6MfvHu0TqbY84w`. File Library is cold recovery and lags GitHub main.

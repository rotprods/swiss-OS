# STATE — LIVE HANDOFF POINTER

Last full operational control-plane reconciliation: **2026-08-27T17:12:40+02:00**.  
Latest Drive-mount CRM staging: **2026-08-28 v6**.

## Authoritative operational state

```text
entity epoch                 HS_ENTITY_EPOCH_2026-08-25_E4
physical HOTELS rows         690
superseded duplicate aliases   4
active canonical             686
CP-0750                      686 / 750 ACTIVE
Intelligence                 686 / 686
Operational Graph            686 / 686
L4                           105 / 686
G-0700 L9                      0 / 2050 reference universe
CRM_UNIVERSE_COMPLETE        FALSE
OUTBOUND                     CLOSED
send_allowed                   0
```

No canary/cache staging value advances authority.

## CRM-universe rule

`CRM_UNIVERSE_COMPLETE = TRUE` is a mandatory precondition before the outbound stack may even be evaluated. CP-0750 and other numeric checkpoints are scale milestones only.

Contract: `docs/operations/CRM_UNIVERSE_PROTOCOL.md`.

## Drive capability

Google Drive is readable through the authenticated `/Google Drive` Library mount. `HOTELS_MASTER` can be listed/materialized and create-only artifacts can be uploaded into the real project folder. Native in-place Sheets mutation is unavailable; issue `#12` tracks that writer capability.

## Snapshot reference

Drive `HS_2026-08-19_WORKING` records a prior reference of **2050 entries / 171 pages**. Indexed HotellerieSuisse pages show different totals at different crawl dates, so final completion requires a freshly frozen/versioned snapshot.

## Authority parent

```text
V13 physical 690
V13 active   686
integrity    ok
FK           0
replay       0
SHA-256      0e605b412f29893ca1775f1e8fccd5987d0613baab4ac29b6699988cde0fdfe5
```

## V16 canary

25 exact-detail candidates remain **CANARY / NON-AUTHORITATIVE**. Previously proposed H-IDs are not reservations.

## CRM mass-ingestion staging v6

Latest artifact:

```text
CRM_UNIVERSE_STAGING_2026-08-28_v6.xlsx
SHA-256 b383847b6a224f3859c14ea0edcfde92639cea44d58239c391facd4199efdd07
Drive external-gdrive:file:1coRHt34VK6mTzIKcF8POK5r7qarVGjr1
```

Validated staging metrics:

```text
current Drive physical rows         690
V16 exact-detail canary               25
reserve candidates without ID          7
historical-cache missing staged      103
CRM import queue                     135
cache observations                   163
reference crawl pages queued         171
canonical H-ID reservations            0
formula errors                         0
```

All 103 cache-derived missing identities remain:

```text
HISTORICAL_CACHE_DISCOVERY_ONLY
→ REFRESH_EXACT_CURRENT_THEN_ENTITY_RESOLVE
→ NO_H_ID_RESERVED
```

Two distributed cache-harvest rounds added **69** missing identities beyond the first staging set while anti-joining observations already represented in CRM/staging.

Pointers/graph:

- Library: `/SWITZERLAND_JOB_OS/CRM_UNIVERSE_STAGING_LATEST.xlsx`
- Library: `/SWITZERLAND_JOB_OS/LATEST_CRM_UNIVERSE.json`
- Drive: `LATEST_CRM_UNIVERSE_2026-08-28_v6.json`
- Drive Context Hub + Library: `CRM_UNIVERSE_META_GRAPH_DELTA_2026-08-28_v6.json`
- production tracker: issue `#14`.

## Production priority

```text
FREEZE/REFRESH CURRENT DIRECTORY SNAPSHOT
→ ENUMERATE ALL SOURCE RECORDS
→ BULK NORMALIZE / ANTI-JOIN
→ ENTITY RESOLUTION
→ DB-FIRST CANONICAL / ALIAS / EXCLUSION COMMIT
→ SHEETS / CRM PK MIRROR
→ INTELLIGENCE SEEDS
→ OPERATIONAL GRAPH
→ COVERAGE RECOMPUTE
```

Deep enrichment may run after seeding but must not block CRM-universe coverage.

## Next authoritative wave

When native Sheets write returns, start `/wave recover`, re-read the live parent/frontier, anti-join all staging, allocate H-IDs only at commit time, and run the full DB → Sheets → Intelligence → Operational Graph → observability → recovery chain.

Only 100% mapped frozen-snapshot coverage may set `CRM_UNIVERSE_COMPLETE = TRUE`.

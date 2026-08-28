# STATE — LIVE HANDOFF POINTER

Last full operational control-plane reconciliation: **2026-08-27T17:12:40+02:00**.  
Latest Drive-mount CRM staging: **2026-08-28 v10**.

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

No cache/canary/staging value advances authority. `CP-0750` is an intermediate scale checkpoint only; it is not an outbound-readiness gate.

## CRM-universe hard gate

`CRM_UNIVERSE_COMPLETE = TRUE` is mandatory before the outbound stack may even be evaluated.

The final denominator is not a permanently hard-coded count. Completion requires one explicitly frozen/versioned HotellerieSuisse source snapshot whose raw source records are all mapped exactly once to:

```text
ACTIVE_CANONICAL
ALIAS_TO_CANONICAL
EXCLUDED_WITH_REASON
```

with `RECONCILE_REQUIRED = 0`, unmapped source records = 0 and all affected DB/CRM/Graph/Intelligence layers reconciled.

Contract: `docs/operations/CRM_UNIVERSE_PROTOCOL.md`.

## Drive capability

Google Drive is currently readable through the authenticated `/Google Drive` Library mount. `HOTELS_MASTER` can be listed/materialized and versioned create-only artifacts can be written into the real project folders.

Native in-place Google Sheets mutation remains unavailable in this runtime. Issue `#12` tracks that writer capability. This is no longer described as a total Drive outage.

## Snapshot semantics

Prior/currently indexed official surfaces disagree across locale/cache epochs:

```text
DE root cache       2050 / 171 pages
FR root cache       2052 / 171 pages
older page caches   2053–2114 / 172–177 pages observed
```

The same `hotel-page-N` can contain different entities across locale/cache epochs. Therefore **page number is not source-record identity**.

The final freeze must bind at minimum:

```text
snapshot_id
locale
source URL/surface
observed_at / epoch
source-record identity
```

Historical page caches remain discovery/anti-join evidence only.

## Constrained E4 recovery lineage

`OPERATIONAL_DB_SHADOW_MANIFEST_V12.json` and `switzerland_job_os_operational_shadow_v12.sqlite` are now physically discoverable in Drive under `11_OPERATIONAL_DB_SNAPSHOTS`.

Independent verification performed 2026-08-28:

```text
V12 declared epoch        HS_ENTITY_EPOCH_2026-08-25_E4
V12 active identities     686
V12 aliases                 4
V12 expected physical     690
V12 next physical ID      H-0691
V12 integrity             ok
V12 FK violations          0
V12 SHA-256               a5d979814ef6c4c9bf44566ec4577d94f6c2660f9ead9934f1173f2903e7fef6
manifest SHA match        TRUE
```

This corrects the earlier capability statement that V12 was not physically discoverable. V12 is a physically verified E4 constrained artifact; **its mere presence does not independently promote authority**. E4 remains the authority pointer. A future authoritative write wave must reconcile the selected constrained parent against live HOTELS_MASTER/control-plane state immediately before commit.

The V13 reconstruction remains valid historical recovery evidence but is no longer the only known physical representation of the E4 state.

## V16 canary

25 exact-detail candidates remain **CANARY / NON-AUTHORITATIVE**. Previously proposed H-IDs are not reservations.

## CRM mass-ingestion staging v10

Latest artifact:

```text
CRM_UNIVERSE_STAGING_2026-08-28_v10.xlsx
SHA-256 4d06a64e311c5b27f14ce2d3b0f28b219a4d2a26a247db9021f00af752430cf8
Drive external-gdrive:file:1RfeGCyuYiMvr-0OcfhosucrKls1sbxwM
```

Validated staging metrics:

```text
current Drive physical rows              690
current authoritative active             686
V16 exact-detail canary                    25
reserve candidates without ID               7
historical-cache missing staged           174
CRM import/staging queue                  240
cache observations                        605
reference crawl pages queued              171
pages with cache evidence                  55
pages pending refresh                     116
snapshot conflicts                          4
normalized name+city import duplicates      0
canonical H-ID reservations                 0
formula errors                              0
```

All historical-cache missing identities remain:

```text
HISTORICAL_CACHE_DISCOVERY_ONLY
→ REFRESH_EXACT_CURRENT_THEN_ENTITY_RESOLVE
→ NO_H_ID_RESERVED
```

A v8 canary exposed duplicate staging where a cached directory page repeated V16/reserve identities. v9 repaired the class with explicit precedence:

```text
V16 / current exact reserve
> historical cache staging
```

v10 preserves zero normalized name+city duplicates in the import queue.

Pointers / recovery:

- Library: `/SWITZERLAND_JOB_OS/CRM_UNIVERSE_STAGING_LATEST.xlsx`
- Library: `/SWITZERLAND_JOB_OS/LATEST_CRM_UNIVERSE.json`
- Library: `/SWITZERLAND_JOB_OS/CRM_UNIVERSE_META_GRAPH_DELTA_2026-08-28_v10.json`
- Library: `/SWITZERLAND_JOB_OS/CRM_UNIVERSE_WAVE_HANDOFF_2026-08-28_v10.md`
- Drive Hospitality: `CRM_UNIVERSE_STAGING_2026-08-28_v10.xlsx`
- Drive Context Hub: `LATEST_CRM_UNIVERSE_2026-08-28_v10.json`
- Drive Context Hub: `CRM_UNIVERSE_META_GRAPH_DELTA_2026-08-28_v10.json`
- Drive Context Hub: `CRM_UNIVERSE_WAVE_HANDOFF_2026-08-28_v10.md`
- production tracker: issue `#14`.

## Production priority

```text
CONTINUE MASS DIRECTORY HARVEST
→ SELECT / FREEZE COHERENT SOURCE SNAPSHOT
→ ENUMERATE SNAPSHOT-SCOPED SOURCE RECORDS
→ BULK NORMALIZE / ANTI-JOIN
→ EXACT-CURRENT REFRESH OF TRUE MISSING RECORDS
→ ENTITY / ALIAS / EXCLUSION RESOLUTION
→ DB-FIRST AUTHORITATIVE COMMIT
→ HOTELS_MASTER PK MIRROR
→ INTELLIGENCE SEEDS
→ OPERATIONAL GRAPH
→ COVERAGE RECOMPUTE
```

Deep enrichment may run after seeding but must not block CRM-universe coverage.

## Next authoritative wave

When native Sheets write is available, start `/wave recover`, re-read the live HOTELS_MASTER/control-plane parent/frontier, anti-join all staging, allocate H-IDs only at commit time, and execute the full DB → Sheets → Intelligence → Operational Graph → observability → recovery chain.

Only 100% mapped frozen-snapshot coverage may set `CRM_UNIVERSE_COMPLETE = TRUE`.

# STATE — LIVE HANDOFF POINTER

Last full operational control-plane reconciliation: **2026-08-27T17:12:40+02:00**.  
Latest Drive-mount CRM staging: **2026-08-28 v11**.  
Latest source-acquisition capability: **discover.swiss adapter DSA-1.0 / PR #20 merged**.

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

No API capture, cache, canary or staging value advances authority. `CP-0750` is an intermediate scale checkpoint only; it is not an outbound-readiness gate.

## CRM-universe hard gate

`CRM_UNIVERSE_COMPLETE = TRUE` is mandatory before the outbound stack may even be evaluated.

The final denominator is not a permanently hard-coded count. Completion requires one explicitly frozen/versioned HotellerieSuisse target snapshot whose raw source records are all mapped exactly once to:

```text
ACTIVE_CANONICAL
ALIAS_TO_CANONICAL
EXCLUDED_WITH_REASON
```

with `RECONCILE_REQUIRED = 0`, unmapped source records = 0, source scope reconciled and all affected DB/CRM/Graph/Intelligence layers reconciled.

Contract: `docs/operations/CRM_UNIVERSE_PROTOCOL.md` (CUP-1.1).

## Preferred source acquisition — discover.swiss API

PR `#20` merged at:

```text
1230add925c43597fb8d903c13b07ac12da9a5c4
```

The preferred primary bulk enumerator is now the structured discover.swiss Infocenter / AccommoDataHub lodging interface rather than web-page position crawling.

Canonical source-acquisition contract:

`docs/operations/DISCOVER_SWISS_SNAPSHOT_ADAPTER.md` (DSA-1.0).

Default adapter request semantics:

```text
/info/v2/lodgingbusinesses
project = dsod-hs
top = -1
first page includeCount = true
nextPageToken → continuationToken
```

The executable adapter captures and validates:

```text
discover.swiss identifier
official HotellerieSuisse hsId
HotellerieSuisse dataGovernance provenance
reported count vs materialized count
provider/source-key uniqueness
continuation-token integrity/cycle safety
deterministic records SHA-256
zero API-key leakage to manifests/GitHub
```

PR #20 CI:

```text
repo_guard                  PASS
system_contract_guard       PASS
unit tests                  44 / 44 PASS
manifest semantics canary   PASS
```

A successful `dsod-hs` API capture deliberately exits as:

```text
scope_state = HOTELLERIESUISSE_API_CAPTURED_MEMBER_DIRECTORY_RECONCILIATION_REQUIRED
member_directory_scope_reconciled = FALSE
crm_freeze_eligible = FALSE
```

until the structured API set is reconciled against the intended HotellerieSuisse public member-directory scope. Count equality alone is insufficient.

Live API execution requires a discover.swiss **Infocenter Open** subscription key. This is an external runtime secret, not repository state. The adapter reads it from:

```text
DISCOVER_SWISS_SUBSCRIPTION_KEY
```

The key must never be committed, logged into public artifacts or pasted into GitHub issues.

If no key is available, the member-directory harvest remains the safe fallback/reconciliation path and historical caches remain discovery-only.

## Drive capability

Google Drive is readable through the authenticated `/Google Drive` Library mount. `HOTELS_MASTER` can be listed/materialized and versioned create-only artifacts can be written into the real project folders.

Native in-place Google Sheets mutation remains unavailable in this runtime. Issue `#12` tracks that writer capability. This is not a total Drive outage.

## Snapshot semantics

Official indexed member-directory surfaces disagree across locale/cache epochs:

```text
DE root cache       2050 / 171 pages
FR root cache       2052 / 171 pages
older page caches   2053–2114 / 172–177 pages observed
```

The same `hotel-page-N` can contain different entities across locale/cache epochs. Therefore **page number is not source-record identity**.

The final target freeze must bind at minimum:

```text
snapshot_id
source provider / project
locale
source URL/surface
observed_at / epoch
stable provider/source-record identity
```

For API-backed HotellerieSuisse capture, prefer `hs:<hsId>` while retaining the discover.swiss identifier.

The current executable snapshot-freeze contract independently rejects incomplete page coverage, raw/materialized mismatch, duplicate source keys, unresolved snapshot conflicts and missing record identity.

Historical page caches remain discovery/anti-join evidence only.

## Constrained E4 recovery lineage

`OPERATIONAL_DB_SHADOW_MANIFEST_V12.json` and `switzerland_job_os_operational_shadow_v12.sqlite` are physically discoverable in Drive under `11_OPERATIONAL_DB_SNAPSHOTS`.

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

V12 is a physically verified E4 constrained artifact; **its presence does not independently promote authority**. E4 remains the authority pointer. A future authoritative write wave must reconcile the selected constrained parent against live HOTELS_MASTER/control-plane state immediately before commit.

The V13 reconstruction remains valid historical recovery evidence but is no longer the only known physical representation of the E4 state.

## V16 canary

25 exact-detail candidates remain **CANARY / NON-AUTHORITATIVE**. Previously proposed H-IDs are not reservations.

## CRM mass-ingestion staging v11

Latest artifact:

```text
CRM_UNIVERSE_STAGING_2026-08-28_v11.xlsx
SHA-256 97486f7e4ae176f447ab8b57ab5ec199cdf3eb5bba556dfb8569235a87f482a1
Drive external-gdrive:file:1kqKPZtWziaERbYbHbBBjPaFAbI_wGD-S
```

Validated staging metrics:

```text
current Drive physical rows              690
current authoritative active             686
V16 exact-detail canary                    25
reserve candidates without ID               7
historical-cache missing staged           182
CRM import/staging queue                  248
cache observations                        629
reference crawl pages queued              171
pages with cache evidence                  57
pages pending refresh                     114
snapshot conflicts                          4
normalized name+city import duplicates      0
canonical H-ID reservations                 0
formula errors                              0
```

The v11 fallback harvest added:

```text
page 94  DE  2067 / 173  → 12 observations → 8 true missing, 4 overlaps
page 145 FR  2060 / 172  → 12 observations → 0 true missing, 12 overlaps
```

The strong overlap on page 145 is positive anti-join evidence; it does not independently prove current snapshot completion.

All historical-cache missing identities remain:

```text
HISTORICAL_CACHE_DISCOVERY_ONLY
→ REFRESH_EXACT_CURRENT_THEN_ENTITY_RESOLVE
→ NO_H_ID_RESERVED
```

Staging precedence remains:

```text
V16 / current exact reserve
> historical cache staging
```

The import queue remains zero-duplicate by normalized name+city.

Pointers / recovery:

- Library: `/SWITZERLAND_JOB_OS/CRM_UNIVERSE_STAGING_2026-08-28_v11.xlsx`
- Library: `/SWITZERLAND_JOB_OS/CRM_UNIVERSE_STAGING_LATEST.xlsx`
- Library: `/SWITZERLAND_JOB_OS/LATEST_CRM_UNIVERSE.json`
- Drive Hospitality: `CRM_UNIVERSE_STAGING_2026-08-28_v11.xlsx`
- production tracker: issue `#14`.

## Production priority

Primary path when the Infocenter Open key is available:

```text
DISCOVER.SWISS dsod-hs FULL CAPTURE
→ CAPTURE QA / COUNT / TOKENS / hsId / PROVENANCE
→ MEMBER-DIRECTORY SCOPE RECONCILIATION
→ FREEZE VERIFIED TARGET SNAPSHOT
→ SNAPSHOT-SCOPED SOURCE RECORD IDs
→ BULK CRM ANTI-JOIN
→ EXACT-CURRENT REFRESH OF AMBIGUOUS / TRUE-MISSING RECORDS
→ ENTITY / ALIAS / EXCLUSION RESOLUTION
→ DB-FIRST AUTHORITATIVE COMMIT
→ HOTELS_MASTER PK MIRROR
→ INTELLIGENCE SEEDS
→ OPERATIONAL GRAPH
→ COVERAGE RECOMPUTE
```

Fallback while API access is unavailable:

```text
CONTINUE VALIDATED MEMBER-DIRECTORY HARVEST
→ CACHE = DISCOVERY ONLY
→ NO H-ID RESERVATION
→ FEED THE SAME SNAPSHOT/ANTI-JOIN CONTRACT
```

Deep vacancy/housing/people/channel enrichment may run after seeding but must not block CRM-universe coverage.

## Next authoritative wave

Before any canonical CRM promotion, both are required:

1. native HOTELS_MASTER write capability or an explicitly approved verified successor mirror path;
2. `/wave recover` re-reading live HOTELS_MASTER/control-plane authority and the chosen constrained parent.

Then anti-join all staging/API source records, allocate H-IDs only at commit time, and execute the full DB → Sheets/CRM → Intelligence → Operational Graph → observability → recovery chain.

Only 100% mapped frozen-snapshot coverage may set `CRM_UNIVERSE_COMPLETE = TRUE`.

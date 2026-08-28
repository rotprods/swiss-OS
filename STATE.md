# STATE — LIVE HANDOFF POINTER

Last full operational control-plane reconciliation: **2026-08-27T17:12:40+02:00**.  
Latest Drive-mount CRM staging: **2026-08-28 v11**.  
Latest source-acquisition capability: **discover.swiss adapter DSA-1.0 / PR #20 merged**.  
Latest source-scope capability: **SSR-1.0 + candidate-to-ingest bridge / PR #25 merged**.

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

A successful `dsod-hs` API capture deliberately remains non-authoritative until member-directory scope reconciliation completes. Count equality alone is insufficient.

Live API execution requires a discover.swiss **Infocenter Open** subscription key through `DISCOVER_SWISS_SUBSCRIPTION_KEY`; the key must never enter repository state, logs or public artifacts.

## SSR-1.0 source-scope reconciliation

PR `#25` passed CI and merged at:

```text
d77282ad12c718ce6091d436cc86be851aed18ce
```

Contract:

`docs/operations/SOURCE_SCOPE_RECONCILIATION.md`.

A valid discover.swiss capture can now be reconciled against one complete coherent member-directory evidence manifest using deterministic precedence:

```text
EXACT_HSID
→ EXACT_DETAIL_URL
→ EXACT_NAME_CITY
```

Ambiguity within either source is a typed conflict. Source-scope states are:

```text
EXACT
EXPLAINED
UNRESOLVED
```

`EXPLAINED` requires an evidence-backed reason for every unmatched source record. Unexplained deltas or conflicts fail closed.

Only a fully reconciled scope can emit:

```text
snapshot_state = FROZEN_CANDIDATE
crm_freeze_eligible = TRUE
```

This still means:

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
```

The candidate-to-ingest bridge now converts that reconciled candidate into the exact CMI-1.0 record schema and verifies snapshot lineage, capture validity, provider-key uniqueness and record-count parity before mass anti-join/scheduler execution.

## Drive capability

The authenticated Drive connector became unavailable during the latest wave. The previously verified v11/authority facts remain the last known persistent state, but the v11 workbook was not reread in that execution. Native in-place Google Sheets mutation remains tracked by issue `#12`.

No new Drive-dependent counter, authority transition or scope-completeness claim was made while the connector was unavailable.

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

Historical page caches remain discovery/anti-join evidence only.

## Constrained E4 recovery lineage

`OPERATIONAL_DB_SHADOW_MANIFEST_V12.json` and `switzerland_job_os_operational_shadow_v12.sqlite` were previously physically verified in Drive under `11_OPERATIONAL_DB_SNAPSHOTS`.

```text
V12 declared epoch        HS_ENTITY_EPOCH_2026-08-25_E4
V12 active identities     686
V12 aliases                 4
V12 expected physical     690
V12 next physical ID      H-0691
V12 integrity             ok
V12 FK violations          0
manifest SHA match        TRUE
```

V12 is constrained recovery evidence; its presence does not independently promote authority. E4 remains the authority pointer.

## V16 canary

25 exact-detail candidates remain **CANARY / NON-AUTHORITATIVE**. Previously proposed H-IDs are not reservations.

## CRM mass-ingestion staging v11

Last verified staging metrics:

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

Artifact last verified before Drive outage:

```text
CRM_UNIVERSE_STAGING_2026-08-28_v11.xlsx
SHA-256 97486f7e4ae176f447ab8b57ab5ec199cdf3eb5bba556dfb8569235a87f482a1
```

Historical-cache missing identities remain:

```text
HISTORICAL_CACHE_DISCOVERY_ONLY
→ REFRESH_EXACT_CURRENT_THEN_ENTITY_RESOLVE
→ NO_H_ID_RESERVED
```

## Production priority

Primary next milestone:

```text
FULL discover.swiss dsod-hs CAPTURE
+
COMPLETE COHERENT MEMBER-DIRECTORY MANIFEST
        ↓
SSR-1.0 SOURCE-SCOPE RECONCILIATION
        ↓
EXACT | EXPLAINED
        ↓
FROZEN_CANDIDATE
        ↓
CANDIDATE → CMI-1.0 EXPORT
        ↓
MASS CRM ANTI-JOIN + SCHEDULER
        ↓
EXACT-CURRENT REFRESH / ENTITY RESOLUTION / EXCLUSION REVIEW
        ↓
TERMINAL SOURCE MAPPINGS
        ↓
RECONCILE_REQUIRED = 0
UNMAPPED = 0
```

Then, before any canonical promotion:

1. restore native HOTELS_MASTER write capability or an explicitly approved verified successor mirror path;
2. `/wave recover` the live control-plane authority and constrained parent;
3. execute DB → Sheets/CRM → Intelligence → Operational Graph → observability → recovery atomically by bounded wave.

Only 100% mapped frozen-snapshot coverage may set `CRM_UNIVERSE_COMPLETE = TRUE`.

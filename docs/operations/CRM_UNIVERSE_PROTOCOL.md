# CRM UNIVERSE PROTOCOL — SWITZERLAND_JOB_OS

Version: **CUP-1.1**  
Status: **CANONICAL OPERATING CONTRACT**

## Purpose

The hotel CRM must represent **100% of the frozen target accommodation-directory snapshot before any outbound gate can open**.

Intermediate canonical checkpoints are throughput milestones only. They never imply CRM completeness or outbound readiness.

## Snapshot semantics

The universe denominator is versioned, never timeless:

```text
crm_snapshot_id
source_url
observed_at
source_crawl_at / retrieval_age when known
raw_directory_count
page_count / API-page count when applicable
source_scope
snapshot_state
```

A new official-source observation may supersede an older denominator. Historical counts remain observations and must not silently rewrite the active snapshot.

`raw_directory_count` is not automatically equal to active canonical hotel count because source entries may resolve to aliases, duplicates, out-of-scope records or superseded entities.

## Source acquisition precedence

Prefer the least ambiguous structured first-party acquisition path that preserves stable provider identity and provenance.

### A. discover.swiss / AccommoDataHub — preferred bulk enumeration

HotellerieSuisse lodging data is exposed through the discover.swiss Infocenter / AccommoDataHub interface. The preferred primary enumeration path is:

```text
Infocenter Open
→ /info/v2/lodgingbusinesses
→ project = dsod-hs
→ paged enumeration with nextPageToken / continuationToken
→ discover.swiss identifier + official hsId
→ dataGovernance provenance / licence
```

The adapter contract is `docs/operations/DISCOVER_SWISS_SNAPSHOT_ADAPTER.md`.

A structurally valid `dsod-hs` capture is **not automatically equivalent to the public member-directory universe**. It must exit source acquisition with member-directory scope reconciliation still required. Count equality alone never proves source-scope equality.

### B. HotellerieSuisse public member directory — reconciliation / fallback

Use the public member directory to:

- reconcile whether the structured API capture corresponds to the intended CRM member scope;
- verify current entity/detail evidence;
- detect additions/removals/scope conflicts;
- support acquisition when API access is unavailable;
- preserve historical snapshot/regression evidence.

Page number is never source-record identity. Page positions can shift across locale/cache epochs.

### C. Historical caches / index results — discovery only

Historical/cache/index observations may seed anti-join and refresh work, but cannot independently enter a frozen snapshot or canonical CRM state.

## Record model

Every source entry receives a stable snapshot record key before canonical ID allocation.

For discover.swiss HotellerieSuisse captures, prefer the provider key:

```text
hs:<official hsId>
```

while retaining the discover.swiss `identifier` as a second immutable source reference.

Each record must terminate in exactly one mapping state:

```text
ACTIVE_CANONICAL
ALIAS_TO_CANONICAL
EXCLUDED_WITH_REASON
RECONCILE_REQUIRED
```

Outbound completeness does not permit unresolved source records. Therefore `RECONCILE_REQUIRED = 0` at gate-open time.

## CRM_UNIVERSE_COMPLETE

`CRM_UNIVERSE_COMPLETE = TRUE` only when all are true:

```text
snapshot_state = FROZEN_VERIFIED
snapshot_raw_records = snapshot_mapped_records
snapshot_unmapped_records = 0
snapshot_reconcile_required = 0
unresolved_duplicate_conflicts = 0
invalid_alias_targets = 0
source-scope reconciliation = EXACT / EXPLAINED
all ACTIVE_CANONICAL entities exist in constrained CRM state
DB ↔ Sheets/CRM mapping reconciliation = EXACT
Operational Graph active denominator = active canonical denominator
Intelligence seed denominator = active canonical denominator
coverage metrics use the same snapshot_id
```

The accounting identity is:

```text
snapshot_raw_records
= active-canonical source mappings
+ alias-to-canonical source mappings
+ explicit excluded-with-reason source mappings
```

Canonical entity count can therefore be lower than the raw source count without losing 100% CRM coverage.

## Outbound dependency

The outbound engine adds a mandatory precondition:

```text
CRM_UNIVERSE_COMPLETE = TRUE
```

This is necessary but not sufficient. Candidate truth/assets, evidence freshness, channel policy, suppression, idempotency and explicit user authorization remain independent hard gates.

No partial checkpoint, high-priority shortlist, deeply enriched sample or local canary may bypass the full-CRM prerequisite.

## Ingestion strategy

Use bulk snapshot ingestion rather than deep research one hotel at a time:

```text
ACQUIRE STRUCTURED SOURCE SNAPSHOT
→ validate count / pagination / provider IDs / provenance
→ reconcile API scope against target member-directory scope
→ FREEZE VERIFIED SOURCE SNAPSHOT
→ assign snapshot_record_id (not canonical H-ID)
→ normalize name/city/source
→ anti-join canonical entities + aliases + groups + domains
→ stage all missing source records in CRM
→ entity-resolution batches
→ canonical/alias/exclusion mapping
→ DB-first constrained commit batches
→ Sheets/CRM PK mirror
→ Graph + Intelligence seed sync
→ recompute snapshot coverage from mappings
```

If API acquisition is unavailable, the member-directory crawler may execute the same snapshot contract, but it must reconstruct coherent source-record identity rather than treating page position as identity.

Deep vacancy/housing/people/channel enrichment can run in parallel after CRM seeding; it must not block ingestion of the remaining universe.

## Structured API capture invariants

An API-backed capture cannot enter the freeze stage if any applicable invariant fails:

```text
reported count missing or mismatched
duplicate discover.swiss identifier
duplicate official hsId
duplicate source_record_key
missing provider identity
missing HotellerieSuisse provenance
pagination token missing while hasNextPage=true
continuation-token cycle
source/project ambiguity
member-directory scope not reconciled
```

Subscription credentials are secret runtime inputs and never belong in GitHub, manifests, logs or recovery bundles.

## Concurrency

Snapshot record IDs are stable within one snapshot. Canonical hotel IDs are allocated only during an authority-eligible commit after re-reading the live frontier.

No local/canary H-ID is a reservation.

## Outage behavior

If Drive/Sheets write capability is unavailable:

- capture/freeze public or licensed-open source evidence where possible;
- build a mass staging/import queue without reserving canonical H-IDs;
- persist staging artifacts to private/recovery storage plus public-safe GitHub handoff;
- close `SAFE_STOP_CANARY`;
- on recovery, anti-join the full staging set before any bulk upsert.

If the discover.swiss API key is unavailable, continue member-directory discovery/reconciliation without weakening evidence state. API unavailability is not permission to mark cache data current.

## Required metrics

```text
crm_snapshot_raw
crm_snapshot_mapped
crm_snapshot_unmapped
crm_active_canonical
crm_alias_mapped
crm_excluded_with_reason
crm_reconcile_required
crm_coverage_pct
crm_universe_complete
source_capture_valid
source_scope_reconciled
source_duplicate_provider_ids
```

`crm_coverage_pct` is based on source-record mapping coverage, not simply canonical count / raw count.

## Definition of Done

The CRM-universe phase is complete when every record of the frozen verified target snapshot is present and deterministically mapped in CRM, source scope is reconciled, all mappings reconcile across constrained DB/Sheets/Graph/Intelligence, and `CRM_UNIVERSE_COMPLETE = TRUE`.

Only after this gate may the separate outbound gate even be evaluated.

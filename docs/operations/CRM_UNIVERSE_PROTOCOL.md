# CRM UNIVERSE PROTOCOL — SWITZERLAND_JOB_OS

Version: **CUP-1.0**  
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
page_count
source_scope
snapshot_state
```

A new official-directory observation may supersede an older denominator. Historical counts remain observations and must not silently rewrite the active snapshot.

`raw_directory_count` is not automatically equal to active canonical hotel count because source entries may resolve to aliases, duplicates, out-of-scope records or superseded entities.

## Record model

Every source-directory entry receives a stable snapshot record key before canonical ID allocation.

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

Canonical entity count can therefore be lower than the raw directory count without losing 100% CRM coverage.

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
FREEZE DIRECTORY SNAPSHOT
→ enumerate all directory pages/records
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

Deep vacancy/housing/people/channel enrichment can run in parallel after CRM seeding; it must not block ingestion of the remaining universe.

## Concurrency

Snapshot record IDs are stable within one snapshot. Canonical hotel IDs are allocated only during an authority-eligible commit after re-reading the live frontier.

No local/canary H-ID is a reservation.

## Outage behavior

If Drive/Sheets write capability is unavailable:

- freeze/collect public snapshot evidence where possible;
- build a mass staging/import queue without reserving canonical H-IDs;
- persist staging artifacts to Library/GitHub public-safe surfaces;
- close `SAFE_STOP_CANARY`;
- on recovery, anti-join the full staging set before any bulk upsert.

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
```

`crm_coverage_pct` is based on source-record mapping coverage, not simply canonical count / raw count.

## Definition of Done

The CRM-universe phase is complete when every record of the frozen verified directory snapshot is present and deterministically mapped in CRM, all mappings reconcile across constrained DB/Sheets/Graph/Intelligence, and `CRM_UNIVERSE_COMPLETE = TRUE`.

Only after this gate may the separate outbound gate even be evaluated.
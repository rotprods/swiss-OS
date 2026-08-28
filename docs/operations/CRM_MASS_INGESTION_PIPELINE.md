# CRM MASS INGESTION PIPELINE — SWITZERLAND_JOB_OS

Version: **CMI-1.0**  
Status: **PRE-AUTHORITY EXECUTION CONTRACT**

## Purpose

Turn snapshot-scoped directory records into deterministic, reviewable, non-authoritative staging decisions at scale without allocating canonical H-IDs or mutating outbound state.

## Input contract

Each record must carry enough data to derive a stable snapshot-scoped source identity under `snapshot_freeze.py`:

```text
provider_record_key
OR exact detail_url
OR source_url + normalized name/city fallback
```

Page position is evidence metadata only; it is never identity.

## Deterministic anti-join precedence

```text
1. EXACT_CANONICAL_DOMAIN
2. EXACT_CANONICAL_NAME_CITY
3. EXACT_ALIAS_NAME_CITY
4. NO_EXACT_IDENTITY_MATCH
```

A match layer that resolves to more than one distinct canonical hotel fails closed as `CONFLICT`.

## Staging classes

```text
ACTIVE_MATCH
ALIAS_MATCH
TRUE_MISSING
CONFLICT
EXCLUSION_CANDIDATE
```

These are staging classes, not final CRM source-mapping states and not authority transitions.

`TRUE_MISSING` means only that the deterministic exact anti-join found no canonical/alias match. It does **not** authorize a new canonical entity. Exact-current evidence and entity resolution are still required.

## Persistence

`crm_ingest_staging` is deliberately separate from:

```text
crm_snapshot_records
crm_source_mappings
canonical_hotels
```

A staging decision cannot become authority merely because it exists in SQLite.

Upsert identity is `snapshot_record_id`; replaying the same source record updates its staging decision instead of creating duplicate work.

## Hard invariants

```text
H_ID_ALLOCATIONS = 0
AUTHORITY_ADVANCED = FALSE
OUTBOUND = CLOSED
```

The mass-ingestion classifier must never allocate a canonical H-ID, create a canonical hotel, create a final CRM mapping, or open outbound.

## CLI

```bash
swiss-os crm-ingest stage DB_PATH SNAPSHOT_ID records.json \
  --observed-at 2026-08-28T13:30:00+02:00
```

The command returns classification metrics and per-record decisions.

## Downstream pipeline

```text
SOURCE RECORDS
→ MASS CLASSIFICATION
→ ACTIVE_MATCH / ALIAS_MATCH / TRUE_MISSING / CONFLICT / EXCLUSION_CANDIDATE
→ exact-current refresh where required
→ entity resolution
→ final ACTIVE_CANONICAL / ALIAS_TO_CANONICAL / EXCLUDED_WITH_REASON / RECONCILE_REQUIRED mapping
→ authority-eligible DB commit
→ Sheets/CRM PK mirror
→ Graph + Intelligence reconciliation
```

## Current production use

For the current v10 lineage, this engine is intended to process the full refreshed snapshot universe, not only the 240 existing staged rows. The current 116 pending reference pages must still be harvested/refreshed before a coherent freeze can pass.

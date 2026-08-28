# CRM MASS INGESTION PIPELINE — SWITZERLAND_JOB_OS

Version: **CMI-1.0**  
Status: **PRE-AUTHORITY EXECUTION CONTRACT**

## Pipeline

```text
discover.swiss / coherent source capture
→ snapshot-scoped record identity
→ deterministic anti-join
→ non-authoritative staging
→ scheduler work
→ exact-current refresh / entity resolution / exclusion review
→ final CRM source mapping
→ authority-eligible DB commit
→ Sheets/CRM mirror
→ Graph + Intelligence reconciliation
```

## Anti-join precedence

```text
EXACT_CANONICAL_DOMAIN
→ EXACT_CANONICAL_NAME_CITY
→ EXACT_ALIAS_NAME_CITY
→ TRUE_MISSING
```

Ambiguous matches fail closed as `CONFLICT`.

## Staging classes

```text
ACTIVE_MATCH
ALIAS_MATCH
TRUE_MISSING
CONFLICT
EXCLUSION_CANDIDATE
```

These are not final authority states. `TRUE_MISSING` means only that no exact deterministic match was found; it still requires exact-current evidence before canonical creation can be considered.

## Scheduler routing

```text
TRUE_MISSING        → REFRESH_EXACT_CURRENT     priority 900
CONFLICT            → ENTITY_RESOLUTION         priority 950
EXCLUSION_CANDIDATE → EXCLUSION_REVIEW          priority 850
ACTIVE_MATCH        → no redundant task
ALIAS_MATCH         → no redundant task
```

Tasks are idempotent by snapshot freshness key + snapshot record scope.

## Hard invariants

```text
H_ID_ALLOCATIONS = 0
AUTHORITY_ADVANCED = FALSE
OUTBOUND = CLOSED
```

`crm_ingest_staging` is deliberately separate from `canonical_hotels`, `crm_snapshot_records`, and `crm_source_mappings`.

## CLI

```bash
swiss-os crm-ingest stage DB_PATH SNAPSHOT_ID records.json --observed-at <ISO8601>
```

The output reports classification metrics, scheduler creation metrics, and per-record decisions.

## Current frontier

This engine can consume records from the newly added discover.swiss acquisition adapter or other snapshot-scoped sources. Scope reconciliation and coherent snapshot freeze remain independent gates; acquisition success alone does not imply CRM completeness or authority.

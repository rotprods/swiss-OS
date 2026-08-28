# STAGING EVIDENCE ADAPTER — SWITZERLAND_JOB_OS

Version: **SEA-1.0**  
Status: **EXECUTABLE EVIDENCE-BRIDGE CONTRACT**

## Objective

Convert the private CRM-universe staging workbook into deterministic, source-coherent MDM-1.0 evidence cohorts without treating workbook rows, page numbers, canary IDs or historical cache entries as canonical authority.

```text
CRM_UNIVERSE_STAGING.xlsx
→ read-only XLSX extraction
→ classify evidence by provider + locale + source epoch + scope
→ one partial MDM manifest per coherent cohort
→ STAGING_EVIDENCE_REGISTRY.json
→ exact-current / manifest completion / SSR work
```

The adapter exists to eliminate ad-hoc notebook scripts and mixed-source spreadsheets as an implicit execution contract.

## Input sheets

### `Directory_Cache_Observations`

Expected normalized fields:

```text
source_page
city
hotel_name
source_url
observed_count
cache_age
evidence_scope
```

Output semantics:

```text
source_provider = HOTELLERIESUISSE_INDEXED_CACHE
evidence_scope = HISTORICAL_CACHE_DISCOVERY_ONLY
H_ID_ALLOCATIONS = 0
SSR eligibility = FALSE
```

The directory-page URL is retained as evidence but is never relabeled as an exact hotel detail URL.

### `V16_Canary`

Expected normalized fields:

```text
proposed_id
name
city
evidence
```

Only an explicit HotellerieSuisse URL inside `evidence` can create a current-exact member-detail record. Rows without one are emitted as typed rejects:

```text
NO_EXACT_HOTELLERIESUISSE_DETAIL_URL
```

A `proposed_id` is historical/canary lineage only. It is not an H-ID reservation.

## Cohort boundary

Records are grouped by exactly:

```text
source_provider
locale
source_epoch
evidence_scope
```

The adapter never unions cohorts into a complete manifest.

Examples that must remain separate:

- DE vs FR locale;
- current member-detail vs historical indexed cache;
- different cache ages/count observations;
- V16 exact-current epoch vs later exact-current refresh;
- HotellerieSuisse member directory vs discover.swiss.

## XLSX safety

The adapter:

- reads XLSX with Python standard-library ZIP/XML parsing;
- never evaluates formulas;
- never modifies the input workbook;
- rejects blank/duplicate normalized headers;
- records workbook SHA-256;
- records sheet and row number in every `evidence_ref`;
- writes output JSON atomically.

The operational Sheet remains a separate authority plane.

## Outputs

Per cohort:

```text
<cohort>.records.json
<cohort>.manifest.json
```

Global registry:

```text
STAGING_EVIDENCE_REGISTRY.json
```

Registry includes:

```text
workbook_sha256
cohort_count
records_count
rejects_count
cohort provider/locale/epoch/scope
semantic violations
manifest + records file hashes
coverage_complete
SSR eligibility
authority_advanced
H-ID allocations
outbound/send lock
```

## Command

```bash
python -m swiss_os.staging_adapter extract-workbook \
  CRM_UNIVERSE_STAGING_LATEST.xlsx \
  --out-dir private/mdm-cohorts \
  --observed-at 2026-08-28T14:30:00+02:00 \
  --v16-epoch SV2-059-V16-CANARY-2026-08-27 \
  --expected-partitions 171 \
  --declared-raw-records 2050
```

## Hard invariants

```text
coverage_complete = FALSE for staging registry
partial cohort ≠ frozen snapshot
historical cache ≠ current membership
page URL ≠ exact detail URL
proposed_id ≠ canonical ID reservation
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND = CLOSED
send_allowed = 0
```

## Relationship to the execution stack

```text
SEA-1.0 staging workbook adapter
→ MDM-1.0 coherent partial manifests
→ exact-current refresh / missing-partition acquisition
→ one complete coherent directory manifest
→ SSR-1.0
→ FROZEN_CANDIDATE
→ CMI-1.0 mass staging
→ terminal source mappings
→ CUP-1.1
```

MEP-2.0 may repeatedly execute SEA extraction after a staging workbook changes, but must anti-join by workbook SHA and cohort fingerprint to avoid producing duplicate low-value waves.

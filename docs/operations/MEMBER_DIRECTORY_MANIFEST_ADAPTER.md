# MEMBER DIRECTORY MANIFEST ADAPTER

Version: **MDMA-1.0**  
Status: **EXECUTABLE PRE-AUTHORITY SOURCE ADAPTER**

## Objective

Build the coherent complete member-directory evidence manifest required by SSR-1.0 without depending on one connector, one page-cache epoch or the discover.swiss subscription key.

This adapter does not scrape by itself. It validates and canonicalizes one captured provider/surface/locale/epoch into a deterministic SSR-compatible manifest.

## Why it exists

Historical HotellerieSuisse directory observations have shown:

- locale roots with different reported totals;
- the same `hotel-page-N` containing different entities across locale/cache epochs;
- page counts shifting over time;
- query filters that materially change a directory surface;
- partial cache results that are useful for discovery but cannot prove coverage.

Therefore:

```text
page number ≠ source-record identity
partial cache ≠ coverage_complete
count equality ≠ source-scope proof
source-surface query ≠ disposable tracking query
```

Entity `detail_url` normalization removes query/fragment. Directory/evidence `source_url` normalization preserves and deterministically sorts query parameters because they may define scope.

## Capture contract

Input schema version:

```text
MEMBER_DIRECTORY_CAPTURE_V1
```

Top-level fields:

```text
capture_id
provider
surface
locale
capture_mode
coverage_claim
started_at
completed_at
expected_pages
reported_records
pages[]
```

Modes:

```text
LIVE_COMPLETE
LIVE_PARTIAL
RECOVERY_COMPLETE
HISTORICAL_CACHE
```

Only `LIVE_COMPLETE` or `RECOVERY_COMPLETE` may carry `coverage_claim=COMPLETE`.

Every page provides:

```text
page_id
page_position
source_url
capture_id
locale
surface
records[]
```

Every record provides:

```text
name
city
hs_id optional
detail_url optional
evidence_ref required
source_url optional
```

## Source-record identity precedence

```text
hs_id
→ normalized exact detail URL
→ normalized name + city hash
```

The adapter emits deterministic `record_id` and `source_record_key`. Neither is an OS canonical `H-ID`.

## Complete-capture gate

`coverage_complete=true` requires:

```text
valid schema and timezone-aware capture interval
one provider / one surface / one locale / one capture_id
capture mode permits completeness
observed pages = expected pages
page positions = exact 1..N set
unique page IDs, positions and source URLs
materialized records = reported records
unique source-record keys
name + city + evidence_ref on every record
zero violations
```

Historical/partial inputs are emitted as typed manifests, but return a blocked exit status and cannot freeze.

## CLI

```bash
PYTHONPATH=src python -m swiss_os.directory_manifest_cli build \
  capture.json --out member-directory-manifest.json

PYTHONPATH=src python -m swiss_os.directory_manifest_cli validate \
  member-directory-manifest.json

PYTHONPATH=src python -m swiss_os.directory_manifest_cli recovery-import \
  validated-member-directory-manifest.json \
  --out recovered-member-directory-manifest.json
```

Recovery import validates content hashes and copies only a valid manifest. It does not upgrade incomplete coverage.

## Output contract

The manifest is directly compatible with SSR-1.0 and includes:

```text
snapshot_id
observed_at
coverage_complete
records[]
records_count
records_sha256
manifest_sha256
violations
warnings
```

Hard outputs:

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
send_allowed = 0
```

## Route integration

```text
API_CAPTURE available
→ use discover.swiss structured capture

API_CAPTURE unavailable
→ RECOVERY_IMPORT if a validated manifest exists
→ DIRECTORY_MANIFEST via MDMA-1.0
→ CACHE_HARVEST only for discovery/anti-join
```

Then:

```text
member-directory manifest
+ discover.swiss manifest
→ SSR-1.0
→ FROZEN_CANDIDATE
→ candidate export
→ mass stage
```

MDMA does not bypass SSR-1.0, CUP-1.1, authoritative cross-plane reconciliation or outbound authorization.

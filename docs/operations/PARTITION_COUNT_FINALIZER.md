# PARTITION COUNT FINALIZER — SWITZERLAND_JOB_OS

Version: **PCF-1.0**  
Status: **EXECUTABLE PRE-AUTHORITY SOURCE-COMPLETENESS CONTRACT**

## Objective

Allow a coherent HSLCA member-directory capture to prove its raw-record denominator from the complete materialized partition set when the current public source does not expose an unambiguous server-rendered aggregate result count.

PCF does **not** weaken partition completeness. It is applicable only when the capture's sole blocker is:

```text
REPORTED_RECORDS_UNRESOLVED
```

and all source partitions are otherwise complete and internally coherent.

## Why this exists

A source may expose deterministic pagination and every current member-detail record while omitting the aggregate count from server-rendered HTML. In that case, requiring a UI count is redundant if the entire partition set is independently proven complete.

PCF distinguishes the two denominator provenance classes explicitly:

```text
PROVIDER_REPORTED
MATERIALIZED_PARTITION_TOTAL
```

It never labels a materialized total as provider-reported.

## Required input gates

The HSLCA capture must remain pre-authority and satisfy all of the following:

```text
schema = MEMBER_DIRECTORY_CAPTURE_V1
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
outbound_opened = FALSE
send_allowed = 0
reported_records absent / zero
capture_violations exactly REPORTED_RECORDS_UNRESOLVED
expected_pages positive integer
pages length = expected_pages
page positions exactly 1..expected_pages
capture_id / locale coherent on every page
no observed page-count drift
no provider count observed on any page
source_url present for every page
records non-empty on every page
name / city / evidence_ref / detail_url present on every record
detail_url unique across the complete partition set
materialized record parity exact
```

Any other source, parser, pagination, duplicate, evidence or lineage violation fails closed.

## Output

PCF emits a finalized pre-authority capture with:

```text
declared_raw_records = exact materialized unique record count
record_count_basis = MATERIALIZED_PARTITION_TOTAL
capture_mode = LIVE_COMPLETE_MATERIALIZED_COUNT
coverage_claim = COMPLETE
capture_violations = []
```

The finalized capture is then recompiled through the canonical MDM adapter. PCF returns success only if MDM independently reports `coverage_complete=true`.

## Command

```bash
python -m swiss_os.partition_count_finalizer build \
  capture.json \
  --out partition-count-finalized.json

python -m swiss_os.partition_count_finalizer validate \
  partition-count-finalized.json
```

## Relationship to HSLCA / MDM

```text
HSLCA complete partition acquisition
→ provider count present
   → normal MDM route

HSLCA complete partition acquisition
+ only REPORTED_RECORDS_UNRESOLVED
→ PCF-1.0
→ MDM complete materialized-count manifest
```

PCF is not applicable to a partial page crawl or a mixed-epoch/resume capture whose source coherence has not been proven.

## Hard locks

```text
CRM_UNIVERSE_COMPLETE unchanged
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND = CLOSED
send_allowed = 0
```

PCF establishes source-side denominator provenance only. It does not perform SSR, CMI, entity resolution, canonical allocation, HOTELS_MASTER writes or outbound actions.

# HSLCA → CANONICAL MDM ADAPTER — SWITZERLAND_JOB_OS

Version: **HCMA-1.0**  
Status: **PRE-AUTHORITY TRANSFER GATE**

## Purpose

The HSLCA/HPCB/PCCN/PCF source-acquisition stack produces a complete low-level current member-directory evidence bundle. The CRM transfer stack (`directory_export.py`) deliberately accepts a different, stricter canonical contract: `MEMBER-DIRECTORY-1.0`.

HCMA-1.0 is the deterministic bridge between those two contracts. It does not perform entity resolution, allocate canonical IDs or mutate operational authority.

## Required input

A PCF-1.0 finalizer bundle with:

```text
coverage_complete = true
record_count_basis = MATERIALIZED_PARTITION_TOTAL
authority_advanced = false
h_id_allocations = 0
outbound = CLOSED
send_allowed = 0
```

Its embedded low-level manifest must be complete, violation-free and safety-locked. Its finalized capture must be violation-free and every page must carry HPCB current-run provenance:

```text
captured_at
captured_at_basis = ATOMIC_CHECKPOINT_FILE_MTIME
```

## Transfer invariant

HCMA proves that the complete page materialization and low-level stable record registry are the same source universe:

```text
capture_id / snapshot_id exact
locale exact
page positions exactly 1..N
page count = expected_pages
materialized record count exact
low-level detail URLs unique
capture detail URLs unique
capture URL universe == manifest URL universe
name/city/evidence_ref/hs_id exact per detail URL
stable low-level record_id present for every capture record
```

Only then is each record mapped into canonical `DirectoryRecord` metadata:

```text
source_provider = HOTELLERIESUISSE_MEMBER_DIRECTORY
source_surface = member-directory
source_epoch = capture_id
partition_key = page-NNNN
observed_at = HPCB captured_at
evidence_scope = CURRENT_DIRECTORY_RECORD
```

The existing canonical `build_member_directory_manifest()` and `validate_member_directory_manifest()` remain the final validators. HCMA does not replace them.

## Output

A self-validating `MEMBER-DIRECTORY-1.0` manifest with:

```text
coverage_complete = true
violations = []
authority_advanced = false
h_id_allocations = 0
outbound_opened = false
send_allowed = 0
```

This output is eligible for `DIRECTORY-TO-CMI-1.0` export only.

## Forbidden implications

A canonical MDM manifest is still **pre-authority evidence**. It cannot by itself:

```text
reserve H-0691 or any H-ID
advance E4 or a later authority epoch
set CRM_UNIVERSE_COMPLETE
open outbound
send any application or message
```

The required downstream chain remains:

```text
HCMA canonical MDM
→ CMI export
→ current-authority anti-join / candidate work plan
→ exact-current validation
→ source mapping / entity resolution
→ terminal mapping for every frozen source record
→ unmapped = 0
→ RECONCILE_REQUIRED = 0
→ later atomic authority reconciliation if eligible
```

`OUTBOUND=CLOSED` and `send_allowed=0` remain independent hard gates.

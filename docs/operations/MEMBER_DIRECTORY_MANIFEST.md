# MEMBER DIRECTORY MANIFEST — SWITZERLAND_JOB_OS

Version: **MDM-1.0**  
Status: **PRE-AUTHORITY SOURCE CONTRACT**

Mutable coverage counts belong in `STATE.md` and current staging/evidence pointers, not this stable contract.

## Purpose

Compile member-directory observations into one coherent evidence manifest consumable by SSR-1.0. The compiler prevents partial caches, mixed locale/epoch slices, invalid page ranges, duplicate identities or record-count mismatch from being mislabeled as complete source coverage.

## MEP fallback

MDM evidence can be built before or in parallel with structured API acquisition. If structured source credentials are unavailable, MEP may continue coherent member-directory evidence acquisition without weakening SSR or authority gates.

## Stable identity

Record identity never uses page position. Priority:

```text
official hsId
→ exact normalized detail URL
→ normalized name + city
```

Page is coverage metadata only. When present, **page must be a strict positive integer**: booleans, floats, numeric strings, zero and negative values are rejected rather than coerced. An absent page remains `None` for evidence that is not tied to a paginated listing.

## Completion gate

`coverage_complete = true` only when:

```text
single locale
single epoch
observed page set exactly equals pages 1 through expected_pages
missing pages = 0
out-of-range pages = 0
materialized records = declared_raw_records
duplicate record IDs = 0
duplicate stable identity keys = 0
```

The number of distinct pages alone is insufficient. Inputs `expected_pages` and `declared_raw_records` are strict positive integers.

Historical/cache observations remain discovery evidence and cannot be promoted merely by compilation. Incompatible locale/cache epochs cannot be represented as one coherent complete snapshot.

## Hard pre-authority outputs

```text
authority_advanced = false
h_id_allocations = 0
outbound_opened = false
```

A complete MDM manifest proves directory evidence coverage only. It does not prove source-scope equivalence, CRM completeness, authority promotion or outbound eligibility.

## Pipeline

```text
member-directory observations
→ MDM-1.0 compiler
→ coherent directory manifest
+
valid structured source capture
→ SSR-1.0 reconciliation
→ EXACT | EXPLAINED | UNRESOLVED
→ FROZEN_CANDIDATE only when source scope is fully reconciled
```

PAB-1.0 may orchestrate MDM + coverage planning + SSR + candidate export as one fail-closed pre-authority bundle. MDM remains independently safe when consumed directly.

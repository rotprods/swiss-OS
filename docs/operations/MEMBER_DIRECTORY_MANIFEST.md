# MEMBER DIRECTORY MANIFEST — SWITZERLAND_JOB_OS

Version: **MDM-1.1**  
Status: **PRE-AUTHORITY SOURCE CONTRACT**

## Purpose

Compile member-directory observations into one coherent evidence manifest consumable by SSR-1.0. The compiler prevents partial caches, mixed locale/epoch slices, shifted page sets, duplicate identities or raw/materialized mismatch from being mislabeled as complete source coverage.

MDM is also the canonical no-key fallback when structured discover.swiss capture is not currently available. Building a coherent member-directory manifest remains productive without lowering any source-scope or authority gate.

## Stable identity

Record identity never uses page position. Priority:

```text
official hsId
→ exact normalized detail URL
→ normalized name + city
```

`page` is coverage metadata only.

## Required observation fields

```text
name
evidence_ref
locale
epoch
```

Optional:

```text
city
page
hs_id
detail_url
record_id
```

When present, `page` must be a strict positive JSON/Python integer. Booleans, floats, numeric strings, zero and negative values are rejected rather than coerced.

## Strict count inputs

```text
expected_pages
declared_raw_records
```

must be strict positive integers. The compiler rejects bool, float and string coercion.

## Completion gate

`coverage_complete = true` only when all hold:

```text
single locale
single epoch
observed page set = {1, 2, ..., expected_pages}
missing_pages = 0
out_of_range_pages = 0
materialized records = declared_raw_records
duplicate record IDs = 0
duplicate stable identity keys = 0
```

Equal page counts are insufficient. A shifted set such as `{2, ..., expected_pages + 1}` fails because page `1` is missing and one page is out of range.

Historical/cache observations remain discovery evidence and cannot be upgraded merely by compilation.

## Output safety

Every MDM manifest explicitly preserves:

```text
authority_advanced = false
h_id_allocations = 0
outbound_opened = false
```

A coherent MDM manifest is evidence input for SSR, not operational authority.

## Pipeline

```text
member-directory observations
→ MDM-1.1 compiler
→ coherent directory manifest
→ SSR-1.0 reconcile
→ EXACT | EXPLAINED | UNRESOLVED
→ FROZEN_CANDIDATE only when scope is fully reconciled
```

No MDM output allocates H-IDs, advances authority or opens outbound.

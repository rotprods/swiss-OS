# MEMBER DIRECTORY MANIFEST — SWITZERLAND_JOB_OS

Version: **MDM-1.0**  
Status: **PRE-AUTHORITY SOURCE CONTRACT**

## Purpose

Compile member-directory observations into one coherent evidence manifest consumable by SSR-1.0. The compiler prevents partial caches, mixed locale/epoch slices, duplicate identities or raw/materialized mismatch from being mislabeled as complete source coverage.

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

## Completion gate

`coverage_complete = true` only when all hold:

```text
single locale
single epoch
observed unique pages = expected_pages
materialized records = declared_raw_records
duplicate record IDs = 0
duplicate stable identity keys = 0
```

This gate is intentionally stronger than the current v11 fallback, where only 57/171 reference pages were last verified. Historical/cache observations remain discovery evidence and cannot be upgraded merely by compilation.

## Pipeline

```text
member-directory observations
→ MDM-1.0 compiler
→ coherent directory manifest
→ SSR-1.0 reconcile
→ EXACT | EXPLAINED | UNRESOLVED
→ FROZEN_CANDIDATE only when scope is fully reconciled
```

No MDM output allocates H-IDs, advances authority or opens outbound.

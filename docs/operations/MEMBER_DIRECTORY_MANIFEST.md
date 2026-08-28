# MEMBER DIRECTORY MANIFEST — SWITZERLAND_JOB_OS

Version: **MDM-1.0**  
Status: **PRE-SSR EVIDENCE CONTRACT**

Mutable coverage counts do not live in this stable contract. Read `STATE.md`, current evidence manifests and persistent staging pointers for live progress.

## Purpose

MDM-1.0 compiles one selected HotellerieSuisse public member-directory observation into a deterministic evidence manifest consumable by SSR-1.0.

It prevents partial caches, mixed locale/epoch slices, duplicate strong source identities or count/page mismatches from being mislabeled as complete source coverage.

## Independence from discover.swiss

The member-directory evidence set can be built before, after or in parallel with discover.swiss API acquisition.

When the discover.swiss subscription key is unavailable, MEP-2.0 may continue MDM evidence acquisition as the preferred safe fallback.

A missing API key never relaxes the directory coverage gate.

## Stable source identity

Record identity never uses page position.

When explicit `record_id` is absent, deterministic identity precedence is:

```text
official hs_id
→ exact normalized detail_url
→ normalized name + city
```

`page` is coverage metadata only and is not accepted as source-record identity.

## Input record schema

Input is a JSON array:

```json
[
  {
    "name": "Hotel Example",
    "city": "Bern",
    "hs_id": "optional",
    "detail_url": "optional exact member-directory detail URL",
    "evidence_ref": "required durable evidence reference",
    "record_id": "optional explicit snapshot-scoped ID"
  }
]
```

Hard requirements:

```text
name
 evidence_ref
```

A record lacking both `hs_id` and `detail_url` also requires non-empty city so deterministic normalized name+city identity can be formed.

## Build command

```bash
swiss-os member-directory build records.json \
  --snapshot-id <snapshot_id> \
  --observed-at <ISO8601> \
  --locale <locale> \
  --source-url <selected root/surface> \
  --declared-raw-records <n> \
  --expected-pages <n> \
  --observed-pages <n> \
  --coverage-complete \
  --out member-directory-manifest.json
```

Omit `--coverage-complete` while the evidence set is intentionally partial.

## Completion gate

`coverage_complete=true` is emitted only when the caller requests completeness and all executable checks pass:

```text
snapshot_id present
observed_at present
locale present
source_url present
declared_raw_records > 0
materialized_records = declared_raw_records
expected_pages > 0
observed_pages = expected_pages
duplicate record_id = 0
duplicate non-empty hs_id = 0
duplicate non-empty detail_url = 0
all records have name
all records have evidence_ref
records_sha256 deterministic
```

Count/page incompleteness remains a typed `coverage_violations` result and forces `coverage_complete=false`.

Strong-key duplication is rejected rather than silently deduplicated.

Normalized name+city ambiguity is reported because legitimately distinct properties can share the same normalized label when stronger identity exists. SSR-1.0 still fails closed if it would need an ambiguous name+city match.

## Validation

```bash
swiss-os member-directory validate member-directory-manifest.json
```

Require SSR-ready completeness:

```bash
swiss-os member-directory validate member-directory-manifest.json --require-complete
```

Validation recomputes:

```text
record identity uniqueness
strong source-key uniqueness
materialized count
page coverage
records_sha256
fail-closed authority/ID/outbound flags
```

## SSR-compatible output

A validated complete output directly provides the fields required by `SOURCE_SCOPE_RECONCILIATION.md`:

```json
{
  "snapshot_id": "...",
  "observed_at": "...",
  "coverage_complete": true,
  "records": [
    {
      "record_id": "...",
      "name": "...",
      "city": "...",
      "hs_id": "...",
      "detail_url": "...",
      "evidence_ref": "..."
    }
  ]
}
```

It can then be passed to:

```bash
swiss-os crm-scope reconcile api-manifest.json member-directory-manifest.json --out candidate.json
```

## Historical/cache evidence

Historical cache pages can feed discovery and anti-join work, but a mixed set of incompatible locale/cache epochs MUST NOT be labeled one complete coherent snapshot.

Before requesting `coverage_complete=true`, evidence collection must bind to one explicit:

```text
snapshot_id
locale
source URL/surface
observed_at/epoch
```

with complete materialized source-record coverage.

## Hard safety outputs

MDM always remains pre-authority:

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
```

A complete MDM manifest proves only directory evidence coverage for the selected snapshot. It does not prove API scope equivalence, CRM completeness, authority promotion or outbound eligibility.

## Pipeline

```text
MEP MEMBER_DIRECTORY_MANIFEST
→ MDM-1.0 build/validate
→ coverage_complete=true
+
DSA-1.0 valid discover.swiss capture
→ SSR-1.0
→ EXACT | EXPLAINED | UNRESOLVED
→ FROZEN_CANDIDATE only when scope is fully reconciled
→ candidate_export
→ CMI mass staging
```

MDM is a source-evidence contract, not an operational authority plane.
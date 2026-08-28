# DIRECTORY → CMI EXPORT — SWITZERLAND_JOB_OS

Version: **D2C-1.0**  
Status: **EXECUTABLE NON-AUTHORITATIVE BRIDGE**

## Objective

Transform one complete transfer-valid MDM-1.0 HotellerieSuisse member-directory manifest into the exact record array consumed by CMI-1.0.

```text
MDC complete capture
→ MDM-1.0 complete manifest
→ D2C-1.0 export
→ CMI non-authoritative anti-join / scheduler
```

This bridge allows the OS to reduce the CRM-universe bottleneck while discover.swiss/SSR remains pending. It does not weaken SSR or authority gates.

## Required input

D2C accepts only a manifest satisfying:

```text
schema_version = MEMBER-DIRECTORY-1.0
coverage_complete = TRUE
semantic violations = 0
transfer validation = PASS
source_provider = HOTELLERIESUISSE_MEMBER_DIRECTORY
record count parity = PASS
provider record keys unique
detail URLs unique
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
send_allowed = 0
```

Partial/historical/mixed manifests are rejected.

## Export record

```json
{
  "source_url": "https://...exact-member-detail...",
  "raw_name": "Hotel name",
  "raw_city": "City",
  "detail_url": "https://...exact-member-detail...",
  "provider_record_key": "directory:<snapshot-scoped-key>"
}
```

Records are sorted deterministically by `provider_record_key`.

## Attestation

D2C emits a sidecar containing:

```text
source snapshot ID
source manifest SHA-256
source records SHA-256
exported record count
exported records SHA-256
key/URL uniqueness
SSR_PENDING = TRUE
candidate state = DIRECTORY_COMPLETE_SSR_PENDING
allowed next use = CMI_NON_AUTHORITATIVE_ANTI_JOIN_AND_SCHEDULING
```

Forbidden next uses are explicit:

```text
AUTHORITATIVE_CANONICAL_PROMOTION
CRM_UNIVERSE_COMPLETE
OUTBOUND_OPEN
```

## Command

```bash
python -m swiss_os.directory_export \
  MEMBER_DIRECTORY_MANIFEST.json \
  --records-out CRM_INGEST_RECORDS.json \
  --attestation-out DIRECTORY_TO_CMI_ATTESTATION.json
```

Then:

```bash
swiss-os crm-ingest stage \
  V12_CANARY.sqlite \
  <snapshot_id> \
  CRM_INGEST_RECORDS.json \
  --observed-at <ISO8601>
```

## Hard invariants

```text
SSR_PENDING = TRUE
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND = CLOSED
send_allowed = 0
```

A successful CMI anti-join is canary production evidence. Canonical promotion still requires the WOP authority chain and all source-scope/CUP gates.

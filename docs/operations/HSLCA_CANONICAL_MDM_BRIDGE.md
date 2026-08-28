# HSLCA → CANONICAL MDM BRIDGE — SWITZERLAND_JOB_OS

Version: **HCMB-1.0**  
Status: **PRE-AUTHORITY TRANSFER BRIDGE**

## Purpose

A PCF-finalized HSLCA capture proves one coherent current HotellerieSuisse member-directory partition set, but the historical HSLCA compatibility compiler emits an intermediate manifest schema. D2C/CMI intentionally accepts only the stricter transfer contract `MEMBER-DIRECTORY-1.0`.

HCMB-1.0 converts the already-finalized capture into that canonical transfer manifest without changing source completeness semantics or operational authority.

```text
HSLCA + MDC-1.1
→ HPCB / PCCN / PCF when count-less
→ finalized capture
→ HCMB-1.0
→ MEMBER-DIRECTORY-1.0
→ D2C-1.0 candidate export
→ CMI non-authoritative anti-join/staging
```

## Input gate

HCMB accepts only a finalized HSLCA capture with:

```text
schema_version = MEMBER_DIRECTORY_CAPTURE_V1
capture_mode = LIVE_COMPLETE_MATERIALIZED_COUNT
coverage_claim = COMPLETE
record_count_basis = MATERIALIZED_PARTITION_TOTAL
capture_violations = []
exact page set = 1..expected_pages
materialized records = declared_raw_records
unique detail URLs
non-empty name/city/detail_url/evidence_ref
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
send_allowed = 0
```

It does not re-prove PCF. It refuses any capture that has not already crossed that finalization boundary.

## Canonical record semantics

Each source row becomes a `DirectoryRecord` with:

```text
source_provider = HOTELLERIESUISSE_MEMBER_DIRECTORY
source_surface = member-directory
source_epoch = capture_id
partition_key = page:<zero-padded page position>
evidence_scope = CURRENT_DIRECTORY_RECORD
record_id = deterministic hash(capture_id + exact detail URL)
hs_id = source-provided value only; normally empty at this stage
```

No canonical H-ID is generated or reserved.

The output is then compiled and independently revalidated by `swiss_os.member_directory`, including exact partition/count parity, duplicate checks, source/locale/epoch coherence, current evidence scope, records hash and manifest hash.

## D2C boundary

A successful HCMB output is directly eligible for D2C-1.0. D2C remains pre-authority and emits `ssr_pending=true`; this bridge does not waive SSR/source-scope reconciliation or terminal mapping requirements.

## Safety

```text
CRM_UNIVERSE_COMPLETE = FALSE
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND = CLOSED
send_allowed = 0
```

Canonical promotion remains forbidden until every frozen source record is terminally mapped and the later atomic DB / HOTELS_MASTER / Intelligence / Graph reconciliation passes.

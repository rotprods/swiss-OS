# DISCOVER.SWISS SNAPSHOT ADAPTER — SWITZERLAND_JOB_OS

Version: **DSA-1.0**  
Status: **CANONICAL SOURCE-ACQUISITION CONTRACT**

## Purpose

Use the structured discover.swiss Infocenter / AccommoDataHub interface as the preferred machine-readable acquisition surface for HotellerieSuisse lodging data, while preserving the HotellerieSuisse public member directory as a separate scope-reconciliation and fallback surface.

This adapter accelerates enumeration. It does **not** by itself prove `CRM_UNIVERSE_COMPLETE = TRUE`.

## Source basis

HotellerieSuisse documents that hotel/room data from AccommoDataHub is available through discover.swiss. discover.swiss documents:

- free access through the `Infocenter Open` product;
- subscription-key authentication using `Ocp-Apim-Subscription-Key`;
- project `dsod-hs` to obtain HotellerieSuisse-specific data;
- list endpoint `/info/v2/lodgingbusinesses`;
- `nextPageToken` → `continuationToken` paging;
- `top=-1` as the recommended client value for downloading all data while still expecting multiple server-side pages;
- `hsId` in `additionalProperty` as the official HotellerieSuisse identifier;
- HotellerieSuisse provenance in `dataGovernance.origin`;
- `updatedSince` / `deleted=true` for incremental synchronization.

The current AccommoDataHub quickstart prose explicitly says `project=dsod-hs`, while some embedded request examples still show `dsod-content`. SWITZERLAND_JOB_OS follows the explicit HotellerieSuisse-specific instruction and defaults to `dsod-hs`. A project override must be deliberate and recorded in the snapshot manifest.

## Security

The API key is never accepted as a CLI argument, never written to a manifest and never committed to GitHub.

Default environment variable:

```text
DISCOVER_SWISS_SUBSCRIPTION_KEY
```

The public repository stores only the client, tests and source-acquisition contracts.

## Request contract

Default request surface:

```text
GET https://api.discover.swiss/info/v2/lodgingbusinesses
project=dsod-hs
top=-1
includeCount=true   # first page
```

Headers:

```text
Ocp-Apim-Subscription-Key: <environment secret>
Accept-Language: de
categoryVersion: sui
Accept: application/json
```

Each subsequent page passes the exact prior `nextPageToken` as the URL-encoded query parameter:

```text
continuationToken=<nextPageToken>
```

Always expect more than one server page even when `top=-1` is used.

## Normalized source identity

For each lodging business persist at minimum:

```text
source_record_key
hs_id
discover_identifier
name
city
removed
last_modified
links
dataGovernance origins/licenses
has_hotelleriesuisse_origin
```

Preferred source-record key:

```text
hs:<hsId>
```

Fallback only if `hsId` is absent:

```text
discover:<identifier>
```

A missing `hsId` or missing HotellerieSuisse origin fails capture validation because the `dsod-hs` acquisition is expected to be HotellerieSuisse-specific.

## Snapshot capture invariants

The adapter fails closed or marks the capture invalid when any of these occur:

```text
missing first-page reported count
reported count != materialized record count
missing discover.swiss identifier
duplicate discover.swiss identifier
duplicate non-empty hsId
duplicate source_record_key
missing hsId
missing HotellerieSuisse dataGovernance origin
hasNextPage=true without nextPageToken
repeated continuation token / pagination cycle
invalid JSON / transport failure
```

The canonical record list is deterministically sorted and SHA-256 hashed.

No subscription key is present in the output manifest.

## Member-directory scope gate

**Critical:** a valid `dsod-hs` API capture is not automatically equivalent to the current public HotellerieSuisse member-directory universe.

The API snapshot therefore exits as:

```text
scope_state = HOTELLERIESUISSE_API_CAPTURED_MEMBER_DIRECTORY_RECONCILIATION_REQUIRED
member_directory_scope_reconciled = FALSE
crm_freeze_eligible = FALSE
```

A later reconciliation wave must compare the API capture with the selected/frozen member-directory scope and explain additions, removals, aliases, exclusions and any source-scope differences before the snapshot can become the CRM denominator.

Count equality alone is insufficient proof of scope equality.

## CLI

After obtaining an Infocenter Open subscription key and placing it in the environment:

```bash
export DISCOVER_SWISS_SUBSCRIPTION_KEY='...'
PYTHONPATH=src python -m swiss_os.cli discover-swiss snapshot \
  --out /private/path/discover_swiss_hs_snapshot.json
```

Optional flags:

```text
--project dsod-hs
--language de
--top -1
--key-env DISCOVER_SWISS_SUBSCRIPTION_KEY
--timeout 30
```

Never commit the generated raw/full snapshot to the public repository. Persist it to constrained/private operational storage and recovery surfaces according to WOP.

## CRM ingestion sequence

```text
DISCOVER.SWISS API CAPTURE
→ CAPTURE QA / COUNT / TOKEN / hsId / PROVENANCE
→ SOURCE SNAPSHOT MANIFEST
→ MEMBER-DIRECTORY SCOPE RECONCILIATION
→ SNAPSHOT FREEZE CONTRACT
→ SNAPSHOT_RECORD_ID GENERATION
→ CRM ANTI-JOIN
→ ENTITY / ALIAS / EXCLUSION RESOLUTION
→ AUTHORITY-ELIGIBLE DB COMMIT
→ HOTELS_MASTER MIRROR
→ GRAPH + INTELLIGENCE
→ CRM_UNIVERSE_COMPLETE GATE
```

The web-directory page harvest remains useful for reconciliation, regression analysis, current detail verification and fallback if API access is unavailable. It is no longer the preferred primary enumeration mechanism once the API key is available.

## Incremental refresh

After a full API-backed baseline is reconciled, use `updatedSince` for changed lodging businesses and `deleted=true` with the same time boundary to ingest soft-deleted records. Incremental refresh never changes the frozen snapshot denominator silently; it creates or proposes a new source observation/epoch under WOP.

# EXACT-CURRENT ENTITY VERIFY — SWITZERLAND_JOB_OS

Version: **ECV-1.0**  
Status: **EXECUTABLE PRE-AUTHORITY EVIDENCE CONTRACT**

## Objective

Verify each active CWP work item against its exact current official HotellerieSuisse member-detail page before entity resolution proceeds.

```text
CMI-WORK-PACKET batch
→ validate exact member-detail URL
→ robots policy
→ bounded official fetch
→ response SHA + HTTP metadata
→ expected name/city text checks
→ typed verification state
→ deterministic follow-up
```

ECV verifies current source identity evidence. It does not perform canonical allocation or resolve group/alias conflicts by itself.

## Accepted input

One CWP batch containing:

```text
batch_id
items_count
items[]
```

Each item requires:

```text
source_record_key
name
city
detail_url
work_state
```

`detail_url` must be an exact HotellerieSuisse member-detail URL. Directory pagination URLs are rejected.

## Access policy

ECV:

- reads only public official HotellerieSuisse pages;
- validates the allowed hostname;
- checks `robots.txt` once per host;
- uses a descriptive user agent;
- applies bounded retry and delay;
- records status, final URL, response size, SHA-256, ETag and Last-Modified where available;
- never bypasses authentication, CAPTCHA, rate limits or access controls.

## Verification states

```text
CURRENT_DETAIL_VERIFIED
CURRENT_DETAIL_NAME_ONLY
CURRENT_DETAIL_CITY_ONLY
CURRENT_DETAIL_MISMATCH
ROBOTS_BLOCKED
FETCH_FAILED
INVALID_WORK_ITEM
```

`CURRENT_DETAIL_VERIFIED` requires both normalized expected name and normalized expected city to be present in the visible official page content.

A weaker state is never silently promoted.

## Follow-up routing

```text
CURRENT_DETAIL_VERIFIED + RECONCILE_REQUIRED
→ RESOLVE_CANONICAL_CONFLICT

CURRENT_DETAIL_VERIFIED + VERIFY_NEW_ENTITY
→ DEDUPE_GROUP_ALIAS_REVIEW

CURRENT_DETAIL_VERIFIED + unknown decision
→ REVIEW_DECISION_SEMANTICS

mismatch/fetch failure
→ REQUEUE_EXACT_CURRENT

robots blocked
→ PROVIDER_POLICY_REVIEW
```

## Commands

```bash
python -m swiss_os.exact_current_verify verify \
  CMI_WORK_BATCH_0001.json \
  --out EXACT_CURRENT_BATCH_0001.json \
  --delay 0.25

python -m swiss_os.exact_current_verify validate \
  EXACT_CURRENT_BATCH_0001.json
```

## Output invariants

```text
one result per input item
source_record_key unique
packet SHA-256 exact
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND = CLOSED
send_allowed = 0
```

## Relationship to entity resolution

ECV consumes the canonical CWP-1.0 work-packet contract now present on `main`; it does not redefine CWP classification semantics.

ECV output feeds a later entity-resolution transition:

```text
verified current identity
→ canonical/name-city/domain/group anti-join
→ ACTIVE_CANONICAL | ALIAS_TO_CANONICAL | EXCLUDED_WITH_REASON | RECONCILE_REQUIRED
```

No ECV result alone may set `CRM_UNIVERSE_COMPLETE`, allocate an H-ID or alter HOTELS_MASTER.

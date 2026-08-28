# WOP — CRM UNIVERSE NEXT WAVE

Date: **2026-08-28**  
Authority at handoff: **E4 / 686 active / 690 physical**  
Outbound: **CLOSED**  
CRM_UNIVERSE_COMPLETE: **FALSE**

## Milestone just completed

The pre-authority CRM-universe chain is now executable as one bundle:

```text
discover.swiss capture
+
member-directory observations
+
coverage/conflict metadata
+
optional evidence-backed scope explanations
        ↓
PAB-1.0
        ↓
MDM-1.0 manifest
coverage plan
SSR-1.0 reconciliation
FROZEN_CANDIDATE or typed blockers
candidate-to-CMI ingest records
```

Merged capabilities:

```text
DSA-1.0  discover.swiss structured acquisition
MDM-1.0  member-directory manifest compiler
SSR-1.0  source-scope reconciliation
PAB-1.0  end-to-end pre-authority bundle
CMI-1.0  deterministic mass anti-join/staging
Coverage Planner  deterministic page/conflict workset
Ingest Scheduler  refresh/entity-resolution/exclusion routing
```

## Last verified source fallback

These are last verified facts only; they MUST NOT be treated as a fresh read:

```text
reference pages          171
cache-evidenced pages     57
pending pages            114
cache observations       629
historical missing       182
staging/import           248
snapshot conflicts         4
```

The Drive connector was unavailable again during the final data-read attempt. No counter or authority state was changed.

## Next executable milestone

Goal: produce the **first real FROZEN_CANDIDATE** or a complete machine-readable blocker set from current live source data.

### Input A — discover.swiss

Execute a full `project=dsod-hs` capture with DSA-1.0 and persist the public-safe API manifest.

Required gate:

```text
capture_valid = true
reported_count = records_count
source_record_key unique
pagination cycle violations = 0
records_sha256 present
```

### Input B — member directory

Acquire one coherent locale+epoch. Feed raw observations to PAB-1.0; do not hand-author a `coverage_complete=true` manifest.

Required observation identity precedence:

```text
hsId
→ exact detail URL
→ normalized name + city
```

Page number is coverage metadata only.

### Execute PAB-1.0

```bash
python -m swiss_os.pre_authority_pipeline \
  discover-swiss-manifest.json \
  member-directory-observations.json \
  --directory-snapshot-id <SNAPSHOT> \
  --observed-at <ISO8601> \
  --locale de \
  --epoch <EPOCH> \
  --expected-pages <N> \
  --declared-raw-records <N> \
  --conflict-pages conflict-pages.json \
  --explanations scope-explanations.json \
  --out-dir artifacts/pre-authority
```

### Exit semantics

`exit 0`:

```text
state = FROZEN_CANDIDATE_READY
crm_freeze_eligible = true
ingest_records_count = API records_count
AUTHORITY_ADVANCED = false
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = false
```

`exit 2`:

```text
state = BLOCKED_PRE_AUTHORITY
```

Typed blocker families include:

```text
API_CAPTURE_INVALID
MEMBER_DIRECTORY_INCOMPLETE
DIRECTORY_COVERAGE_WORK_REMAINS
SOURCE_SCOPE_UNRESOLVED
```

## If directory coverage is incomplete

Use `coverage_plan.json` as the sole page-level workset.

Priorities:

```text
950 SNAPSHOT_CONFLICT_EXACT_CURRENT_REFRESH
900 MISSING_PAGE_EXACT_CURRENT_REFRESH
```

Foreign locale/epoch evidence does not reduce the missing-page count.

## If FROZEN_CANDIDATE is ready

Run CMI-1.0 against the constrained DB parent:

```text
ACTIVE_MATCH
ALIAS_MATCH
TRUE_MISSING
CONFLICT
EXCLUSION_CANDIDATE
```

Then drain scheduler work:

```text
TRUE_MISSING        → REFRESH_EXACT_CURRENT
CONFLICT            → ENTITY_RESOLUTION
EXCLUSION_CANDIDATE → EXCLUSION_REVIEW
```

Do not allocate any H-ID during staging.

## Completion condition for CRM universe

A later authority-eligible wave may set `CRM_UNIVERSE_COMPLETE=true` only when every source record in one frozen/versioned target snapshot maps exactly once to:

```text
ACTIVE_CANONICAL
ALIAS_TO_CANONICAL
EXCLUDED_WITH_REASON
```

and all of the following hold:

```text
RECONCILE_REQUIRED = 0
unmapped = 0
DB↔Sheets exact
Graph exact
Intelligence exact
same snapshot lineage
same active denominator
```

## Authority blockers unrelated to acquisition

Native in-place `HOTELS_MASTER` mutation remains tracked by issue #12. A locally correct DB cannot promote authority until the CRM mirror and downstream graph/intelligence/observability layers can be atomically reconciled.

## Non-negotiable invariants

```text
truth > volume
evidence > inference
count equality != source-scope equality
partial cache != complete snapshot
page position != identity
staging != authority
no H-ID reservation before authority commit
no outbound before CRM universe completion + independent gates + explicit authorization
```

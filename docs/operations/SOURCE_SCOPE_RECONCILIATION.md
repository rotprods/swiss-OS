# SOURCE SCOPE RECONCILIATION — SWITZERLAND_JOB_OS

Version: **SSR-1.0**  
Status: **PRE-AUTHORITY HARD GATE**

## Objective

Prove whether one structurally valid `discover.swiss / dsod-hs` capture represents the intended HotellerieSuisse public member-directory scope at source-record level.

Count equality is never sufficient.

## Inputs

### Structured API manifest

Produced by:

```bash
swiss-os discover-swiss snapshot --out <private-manifest.json>
```

It must already satisfy `capture_valid = true`.

### Member-directory evidence manifest

Must contain:

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
      "hs_id": "optional",
      "detail_url": "optional",
      "evidence_ref": "required"
    }
  ]
}
```

`coverage_complete=true` is a strong assertion: the selected member-directory evidence set must represent the complete selected directory snapshot/epoch, not a partial cache collection.

## Matching precedence

```text
1. EXACT_HSID
2. EXACT_DETAIL_URL
3. EXACT_NAME_CITY
```

All matching layers require uniqueness. Ambiguity within either source is itself a typed conflict and fails closed.

## Scope states

```text
EXACT
EXPLAINED
UNRESOLVED
```

`EXACT` means every API record and every directory record is paired exactly once.

`EXPLAINED` permits explicit source-scope deltas only when every unmatched record carries a typed explanation with an evidence reference. Examples may include a source-specific non-public record or a directory-only record omitted from the API for a verified reason. The explanation is evidence, not a heuristic.

`UNRESOLVED` means at least one unmatched record or conflict remains.

## Explanation contract

```json
[
  {
    "side": "API",
    "record_key": "hs:123",
    "reason_code": "REMOVED_FROM_PUBLIC_MEMBER_DIRECTORY",
    "evidence_ref": "..."
  }
]
```

Required fields:

```text
side = API | DIRECTORY
record_key
reason_code
evidence_ref
```

Duplicate explanations for the same side/key are rejected.

## Candidate snapshot

Run:

```bash
swiss-os crm-scope reconcile \
  api-manifest.json \
  member-directory-manifest.json \
  --explanations explanations.json \
  --out crm-candidate-snapshot.json
```

The output is deterministic and includes a reconciliation SHA-256.

A candidate can become:

```text
snapshot_state = FROZEN_CANDIDATE
crm_freeze_eligible = true
```

only when:

```text
API capture_valid = true
member-directory coverage_complete = true
scope state = EXACT | EXPLAINED
conflicts = 0
unexplained API-only = 0
unexplained DIRECTORY-only = 0
```

This does **not** mean authority advanced and does not set `FROZEN_VERIFIED` by itself.

Hard outputs remain:

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
```

## Candidate → mass-ingest bridge

A reconciled candidate can be deterministically transformed into the input schema consumed by CMI-1.0:

```bash
python -m swiss_os.candidate_export \
  crm-candidate-snapshot.json \
  api-manifest.json \
  --out crm-ingest-records.json
```

The bridge verifies:

```text
candidate crm_freeze_eligible = true
candidate snapshot_state = FROZEN_CANDIDATE
candidate api_snapshot_id = API snapshot_id
API capture_valid = true
API records_count = exported record count
source_record_key uniqueness
non-empty source name
```

It exports:

```text
source_url
raw_name
raw_city
detail_url
provider_record_key
```

and still guarantees:

```text
H_ID_ALLOCATIONS = 0
AUTHORITY_ADVANCED = FALSE
```

The resulting file can be passed directly to:

```bash
swiss-os crm-ingest stage DB_PATH SNAPSHOT_ID crm-ingest-records.json --observed-at <ISO8601>
```

This closes the executable handoff from structured acquisition to deterministic anti-join/scheduler while keeping authority separate.

## Relationship to CUP-1.1

```text
discover.swiss acquisition
→ SSR-1.0 source-scope reconciliation
→ FROZEN_CANDIDATE
→ candidate_export
→ CRM mass anti-join + scheduler
→ exact-current / entity-resolution work
→ terminal mappings
→ snapshot freeze verification
→ authority-eligible commit
→ cross-plane reconciliation
→ CRM_UNIVERSE_COMPLETE
```

SSR-1.0 closes the ambiguity between a valid API capture and the intended public member-directory universe. It does not bypass issue #12 or any outbound gate.

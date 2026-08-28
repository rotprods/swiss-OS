# PRE-AUTHORITY CRM BUNDLE — PAB-1.0

Status: **EXECUTABLE PRE-AUTHORITY ORCHESTRATION**

## Purpose

PAB-1.0 collapses the current CRM-universe pre-authority chain into one deterministic execution unit:

```text
discover.swiss API manifest
+
member-directory observations
+
coverage/conflict metadata
+
optional evidence-backed scope explanations
        ↓
member-directory manifest (MDM-1.0)
        ↓
directory coverage plan
        ↓
SSR-1.0 source-scope reconciliation
        ↓
FROZEN_CANDIDATE or explicit blockers
        ↓
candidate-to-CMI ingest export
```

It does **not** advance authority, allocate H-IDs, write HOTELS_MASTER or open outbound.

## Fail-closed gates

The bundle is `FROZEN_CANDIDATE_READY` only when all of the following hold:

1. discover.swiss manifest has `capture_valid=true`;
2. member-directory observations compile to `coverage_complete=true`;
3. no missing/conflicting directory pages remain for the selected locale+epoch;
4. SSR-1.0 resolves to `EXACT` or evidence-backed `EXPLAINED`;
5. candidate snapshot is `crm_freeze_eligible=true`;
6. candidate-to-ingest export passes source-record uniqueness and count parity.

Otherwise the bundle is `BLOCKED_PRE_AUTHORITY` and emits typed blockers plus deterministic coverage tasks.

## Artifacts

A run writes:

```text
pre_authority_bundle.json
directory_manifest.json
coverage_plan.json
candidate_snapshot.json
ingest_records.json
```

The bundle includes a deterministic SHA-256 over its public-safe content.

## CLI

```bash
python -m swiss_os.pre_authority_pipeline \
  discover-swiss-manifest.json \
  member-directory-observations.json \
  --directory-snapshot-id MD-EPOCH \
  --observed-at 2026-08-28T12:00:00Z \
  --locale de \
  --epoch EPOCH \
  --expected-pages 171 \
  --declared-raw-records N \
  --conflict-pages conflict-pages.json \
  --explanations scope-explanations.json \
  --out-dir artifacts/pre-authority
```

Exit code `0` means the pre-authority bundle is ready for CMI staging. Exit code `2` means work remains and no ingest export is allowed.

## Invariants

```text
AUTHORITY_ADVANCED = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND_OPENED = FALSE
page position != source identity
partial cache != complete directory manifest
count equality != source-scope equality
```

PAB-1.0 is the execution bridge between acquisition/reconciliation and the existing mass-ingestion scheduler. It removes manual handoffs while preserving CUP-1.1 fail-closed semantics.

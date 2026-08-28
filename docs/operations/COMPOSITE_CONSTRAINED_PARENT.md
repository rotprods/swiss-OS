# COMPOSITE CONSTRAINED PARENT — SWITZERLAND_JOB_OS

Version: **CCP-1.0**  
Status: **RECOVERY REPRESENTATION CONTRACT**

## Objective

CCP-1.0 allows the Recovery & Persistence Engine to represent a repaired constrained SQLite state durably when the active provider can read the immutable parent bytes but cannot egress a newly materialized binary.

It is not a relaxed authority path. It is a content-addressed recovery representation:

```text
immutable durable base bytes
+ pinned deterministic ARR-1.0 repair definition
+ pinned repair engine revision
+ precommitted materialized SQLite SHA-256
+ verified integrity/FK/idempotency materialization proof
= DURABLE_MATERIALIZABLE_CONSTRAINED_PARENT
```

The repaired binary may be materialized on demand. Every materialization must reproduce the precommitted output digest exactly.

## Eligibility

A CCP manifest MUST contain:

```text
schema_version = CCP-1.0
base_sha256
base_size_bytes
base_replicas[] on durable remote providers
repair_protocol = ARR-1.0
repair_plan_path
repair_plan_blob_sha
repair_engine_blob_sha
repair_engine_commit_sha
expected_materialized_sha256
materialization_proof.output_sha256 == expected_materialized_sha256
materialization_proof.integrity_check = ok
materialization_proof.foreign_key_violations = 0
materialization_proof.idempotency_replay = PASS
active_denominator = null
active_denominator_state = RECONCILE_REQUIRED_CROSS_PLANE
authority_advanced = false
canonical_id_allocations = 0
outbound_opened = false
send_allowed = 0
```

A local-only base is not sufficient. At least one durable remote base reference is required. Multiple remote replicas are preferred for recovery resilience.

## What CCP changes

CCP removes one storage-mechanics blocker only: the recovery wave no longer requires the repaired SQLite binary itself to be uploaded before it can have a durable constrained-state representation.

CCP does **not** change semantic or cross-plane authority requirements.

```text
CCP valid
≠ COMPLETE_AUTHORITY
≠ active denominator proven
≠ CRM_UNIVERSE_COMPLETE
≠ outbound permission
```

A valid CCP remains:

```text
active_denominator_state = RECONCILE_REQUIRED_CROSS_PLANE
```

until the repaired materialization and every affected authoritative plane are reconciled in one bounded recovery transaction.

## Materialization gate

Executable validator:

```text
src/swiss_os/composite_constrained_parent.py
```

Commands:

```bash
python -m swiss_os.composite_constrained_parent validate <manifest.json>
python -m swiss_os.composite_constrained_parent verify <manifest.json> <materialized.sqlite>
```

`verify` requires the materialized SQLite SHA-256 to equal the precommitted digest and reruns SQLite integrity and FK checks.

## Authority promotion after CCP

A CCP may participate as the constrained-backend representation in `RECOVERY_RECONCILE` only if the same wave also proves:

```text
fresh Git ancestry
+ exact durable base SHA
+ exact ARR plan / engine revision
+ exact materialized SQLite digest
+ ASR-1.0 = EXACT
+ DB materialized state ↔ HOTELS_MASTER exact
+ Intelligence exact
+ Operational Graph exact
+ scheduler/checkpoints/metrics/SLO/invariants exact
+ append-only corrective transitions exact
+ restore/replay/idempotency gauntlet PASS
```

Only after those gates pass may the Authority & Reconciliation Engine derive a numeric active denominator and persist an authority-eligible synchronized commit.

## Failure semantics

Any of the following fails closed:

```text
base SHA/size drift
missing/non-durable base reference
repair plan or repair engine revision drift
materialized digest mismatch
SQLite integrity/FK failure
idempotency proof failure
pre-authorized active denominator
authority_advanced != false
canonical_id_allocations != 0
outbound_opened != false
send_allowed != 0
```

On failure:

```text
RECOVERY_RECONCILE
AUTHORITY_ADVANCE = FALSE
H_ID_ALLOCATIONS = 0
OUTBOUND = CLOSED
send_allowed = 0
```

## Security / persistence

Public GitHub CCP manifests may contain public-safe provider file identifiers and digests, but never operational binary contents, secrets, candidate PII or private contact data.

The base bytes remain on their durable provider. GitHub stores only the executable contract, content-addressed repair lineage and public-safe state pointers.

CCP never converts GitHub or Library into the operational database.

# SQLITE REPAIR SPEC — SWITZERLAND_JOB_OS

Version: **SRS-2.0**  
Status: **CONSTRAINED REPAIR ENGINE**

## Objective

Convert a validated source-to-canary SQLite delta into an exact, transactional and replay-safe repair operation without granting operational authority.

Implementation:

```text
src/swiss_os/sqlite_repair.py
```

SRS-2.0 exists because an authority-adjacent migration must prove more than the affected rows. A database whose repaired tables match while an unrelated operational table has drifted is not a valid post-state.

## Build contract

```python
build_repair_spec(source_db, target_canary_db, repair_id=...)
```

The builder requires:

```text
source schema signature = target schema signature
source table set = target table set
```

It records:

- exact source-file SHA-256;
- schema signature including schema objects, encoding, `user_version` and `application_id`;
- exact affected tables and column order;
- complete multiset removed and added rows;
- expected row count for every non-internal table;
- deterministic logical row-content hash for every non-internal table;
- one whole-database postcondition fingerprint.

The spec includes no authority, H-ID or outbound permission.

## Apply contract

```python
apply_repair_spec(db_path, spec, backup_path=...)
```

The engine follows this order:

```text
validate spec and hard locks
→ validate schema signature
→ test whole-database post-state
→ if exact: verified NOOP_ALREADY_APPLIED
→ otherwise require exact source-file SHA-256
→ create immutable backup if requested
→ BEGIN IMMEDIATE
→ defer foreign keys until transaction validation
→ validate exact operation tables/columns
→ apply multiset removals and additions
→ validate every-table count/hash postconditions
→ integrity_check
→ foreign_key_check
→ COMMIT or full ROLLBACK
```

A database that is neither the exact source parent nor the verified whole-database post-state fails closed.

## Whole-database replay invariant

A no-op replay is valid only when:

```text
live table set = expected post table set
schema signature = expected schema signature
every table row count = expected count
every table logical row hash = expected hash
integrity_check = ok
foreign_key_check = 0
```

Drift in an unaffected table invalidates replay eligibility.

## Multiset semantics

Rows are compared as multisets, not sets. When identical physical rows occur multiple times, the repair preserves the exact target multiplicity.

For a removal of `N` identical rows from `M` source rows:

```text
require M >= N
remove matching physical rows
reinsert M-N retained rows
validate target count/hash
```

This avoids silently collapsing valid duplicate multiplicity while remaining deterministic at the logical-data level.

## Security and correctness

- SQL identifiers must match a strict grammar.
- All values are parameterized.
- Booleans are not accepted as integer repair values.
- Non-finite floats are rejected.
- BLOBs use explicit hexadecimal encoding.
- Duplicate operation tables are rejected.
- Operations targeting absent tables are rejected, including during the no-op path.
- Postcondition maps must cover exactly every live non-internal table.
- Tampered postcondition fingerprints fail before mutation.
- Existing backup files are never overwritten.
- Schema or parent drift blocks execution.

## Receipt states

```text
APPLIED_CANARY_NON_AUTHORITY
NOOP_ALREADY_APPLIED
```

Every receipt contains:

```text
authority_advanced = false
h_id_allocations = 0
outbound_opened = false
send_allowed = 0
```

## Relationship to issue #89

SRS-2.0 can deterministically reproduce the V13-to-ASR-repair-canary delta and prove replay safety. It repairs only one constrained SQLite copy.

AAR-1.0 still requires exact parity across:

```text
constrained DB
HOTELS_MASTER
Intelligence
Operational Graph
metrics / scheduler / checkpoints / transitions
```

before an enclosing WOP transaction may publish an authority transition.

Until then:

```text
alias semantics = RECONCILE_REQUIRED
canonical H-ID allocation = FORBIDDEN
CRM_UNIVERSE_COMPLETE = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```

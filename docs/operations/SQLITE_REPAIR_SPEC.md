# SQLITE REPAIR SPEC — SWITZERLAND_JOB_OS

Version: **SRS-1.0**  
Status: **CONSTRAINED REPAIR ENGINE**

## Objective

Turn a validated source-to-canary SQLite delta into an exact, transactional and idempotent repair operation without granting operational authority.

Implementation:

```text
src/swiss_os/sqlite_repair.py
```

## Build

```python
build_repair_spec(source_db, target_canary_db, repair_id=...)
```

The builder requires identical SQLite schema signatures and records:

- exact source-file SHA-256;
- exact affected tables and column order;
- complete removed and added rows;
- expected post-repair table counts;
- deterministic post-repair row-content hashes.

It emits no H-ID allocation and no authority/outbound permission.

## Apply

```python
apply_repair_spec(db_path, spec, backup_path=...)
```

The engine:

1. validates schema and identifiers;
2. returns an idempotent no-op when the verified post-state already exists;
3. otherwise requires the exact source-file SHA-256;
4. creates an optional immutable backup;
5. opens `BEGIN IMMEDIATE`;
6. requires each removed row to exist exactly once;
7. applies parameterized deletes and inserts;
8. verifies deterministic postconditions;
9. runs `integrity_check` and `foreign_key_check`;
10. commits or rolls back the whole repair.

A database that is neither the exact source nor the verified post-state fails closed.

## Security and correctness

- SQL identifiers must match a strict identifier grammar.
- Values are always parameterized.
- Duplicate rows are handled with multiset semantics.
- Binary values use explicit hex encoding.
- Schema drift blocks execution.
- Tampered postconditions roll back.
- A replay after successful application is a verified no-op.

## Authority boundary

Every receipt contains:

```text
authority_advanced = false
h_id_allocations = 0
outbound_opened = false
send_allowed = 0
```

SRS-1.0 repairs only one constrained SQLite copy. AAR-1.0 still requires exact DB-to-HOTELS_MASTER-to-Intelligence-to-Operational-Graph-to-observability parity before an enclosing WOP transaction may publish authority.

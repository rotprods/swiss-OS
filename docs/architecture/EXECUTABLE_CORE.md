# Executable Core V1

The repository now contains a deliberately small Python/SQLite integrity core. It converts the most failure-prone system contracts into executable constraints without attempting to recreate the entire Drive control plane in code.

## Modules

- `manifest.py` — parses old/new operational manifest shapes and enforces physical-vs-active canonical semantics.
- `invariants.py` — duplicate, gap and manifest integrity checks.
- `reconcile.py` — exact PK-set reconciliation between a physical mirror and active constrained state.
- `db.py` + `schema.sql` — SQLite initialization, integrity/FK checks and constrained canonical/task/run tables.
- `scheduler.py` — idempotent task admission by scope/type/freshness key.
- `cli.py` — small operator interface for manifest and DB validation.

## Core semantic correction

A physical hotel row is not automatically an active canonical entity.

```text
physical rows
- explicitly superseded duplicate rows
= active canonical entity set
```

Checkpoint counters must use the active canonical entity set. Physical ID lineage remains preserved for audit/gap semantics.

## Deliberate non-goals

V1 does not implement provider scraping, Google Sheets writes, a background daemon, application sending, Postgres, distributed queues or workflow orchestration. Those are added only when a concrete execution bottleneck requires them.

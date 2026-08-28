# EXECUTABLE CORE — SWITZERLAND_JOB_OS

Version: **CORE-1.1**  
Status: **STABLE ARCHITECTURE CONTRACT**

The repository contains a deliberately small Python/SQLite integrity core. It converts the most failure-prone system contracts into executable constraints without recreating the full Drive control plane or inventing distributed infrastructure that the current scale does not require.

## Modules

- `manifest.py` — parses public-safe operational manifest shapes and enforces physical-vs-active canonical semantics.
- `invariants.py` — manifest integrity plus active/physical separation primitives.
- `reconcile.py` — exact PK-set reconciliation between physical mirrors and active constrained state.
- `db.py` + `schema.sql` — SQLite initialization, integrity/FK checks, logical restore equivalence and constrained canonical/task/run tables.
- `scheduler.py` — idempotent task admission by scope/type/freshness key.
- `cli.py` — small operator interface for manifest and DB validation.
- `scripts/repo_guard.py` — public-repository/secret boundary guard.
- `scripts/system_contract_guard.py` — stable-document/WOP/engine-contract drift guard.

## Core semantic corrections

### Physical lineage is not active canonical state

```text
physical rows
- explicitly superseded duplicate rows
= active canonical entity set
```

Checkpoint counters use the active canonical set. Physical IDs remain immutable lineage.

### SQLite restore is logical, not binary

A valid SQLite backup/restore may serialize pages differently while representing identical operational state.

Restore PASS therefore checks:

```text
integrity source + restore
FK source + restore
schema objects
same table sets / row counts
source EXCEPT restore = empty
restore EXCEPT source = empty
```

Binary SHA equality remains useful for transfer verification of the exact same artifact, not for logical restore equivalence.

### Local canary is not authority

A constrained local DB may pass every local invariant and remain non-authoritative until the Wave Operating Protocol synchronizes all affected authority planes.

## Deliberate non-goals

The core does not implement:

- provider scraping;
- hidden background daemons;
- automatic Google Sheets orchestration inside the public package;
- application sending;
- CAPTCHA/auth/paywall bypass;
- Postgres/Kubernetes/distributed queues;
- a duplicate workflow platform.

Those are introduced only when a measured production bottleneck requires them.

## Production role

The executable core is the **constraint kernel**, not the whole OS.

The full system sequence is defined by:

```text
docs/operations/WAVE_OPERATING_PROTOCOL.md
docs/operations/PRODUCTION_READINESS_GAUNTLET.md
docs/architecture/ENGINE_REGISTRY.md
```

CI validates the repository kernel/contracts. Runtime authority still requires constrained DB + affected live mirrors/graphs/governance surfaces to reconcile.
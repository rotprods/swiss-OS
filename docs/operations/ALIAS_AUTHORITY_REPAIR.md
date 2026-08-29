# ALIAS AUTHORITY REPAIR — SWITZERLAND_JOB_OS

Version: **AAR-1.0**  
Status: **AUTHORITY-PROMOTION GATE**

## Objective

Promote a validated ARC-1.0 alias repair canary only after every affected operational plane proves the same repaired physical, active and alias PK sets.

A repair canary is evidence, not authority. This contract prevents a valid local SQLite repair from being published while HOTELS_MASTER, Intelligence, Operational Graph or observability still encode corrupt lineage.

## Executable contract

Implementation:

```text
src/swiss_os/asr_authority.py
```

Pure stages:

```python
compile_authority_repair_expected(...)
validate_authority_repair(...)
```

The compiler derives exact expected post-repair sets from the unchanged physical H-ID set, current alias edges, a canary-eligible ARC-1.0 plan, the exact parent manifest and authority epoch.

The validator consumes post-write receipts from every required plane. It never performs writes or advances authority directly.

## Required capabilities

Every capability must be the JSON boolean `true`:

```text
constrained_db_write
native_hotels_master_write
intelligence_write
operational_graph_write
observability_write
```

Strings such as `"true"` fail closed.

## Exact parity requirements

```text
DB physical IDs                 = expected physical IDs
HOTELS_MASTER physical IDs      = expected physical IDs
DB active IDs                   = expected active IDs
HOTELS_MASTER active IDs        = expected active IDs
Intelligence active IDs         = expected active IDs
Operational Graph active IDs    = expected active IDs
DB alias edges                  = expected alias edges
HOTELS_MASTER alias edges       = expected alias edges
Operational Graph alias edges   = expected alias edges
```

Counts never substitute for PK-set equality.

## Concurrency gate

Immediately before promotion:

```text
live parent manifest = compiled parent manifest
live authority epoch = compiled authority epoch
```

Any change requires a new `RECOVERY_RECONCILE` cycle.

## QA gate

```text
SQLite integrity_check = ok
FK violations = 0
replay unintended mutations = 0
restore logical differences = 0
semantic alias violations = 0
active normalized name+city duplicates = 0
invalid alias targets = 0
```

## Observability gate

The active denominator must match in metrics, checkpoint state and scheduler. A state transition, run-log record and issue update must all be emitted.

## Governance gate

```text
OUTBOUND = CLOSED
send_allowed = 0
external actions performed = false
```

A successful validation emits:

```text
authority_repair_state = COMPLETE_AUTHORITY_ELIGIBLE
promotion_eligible = true
authority_advanced = false
```

The final `authority_advanced=false` is deliberate: this validator proves eligibility. The enclosing WOP transaction may persist an authority transition only after final reconciliation.

## Current issue #89 semantics

The current repair projection preserves all physical H-IDs and quarantines four phantom alias edges. That projection remains non-authoritative until AAR-1.0 passes against DB, HOTELS_MASTER, Intelligence, Operational Graph and observability.

Until then:

```text
safe authoritative active count = RECONCILE_REQUIRED
canonical H-ID allocation = FORBIDDEN
CRM_UNIVERSE_COMPLETE = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```

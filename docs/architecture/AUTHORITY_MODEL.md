# Authority Model

SWITZERLAND_JOB_OS deliberately separates versioned system definition from operational state.

## Authority order

```text
1. Physical + constrained operational data
2. Live control-plane registries / active machine state
3. Latest validated operational manifest
4. GitHub versioned contracts + STATE.md
5. Release/handoff prose
6. Legacy documentation
```

If layers disagree, do not silently choose. Record drift and repair the stale layer.

## Storage roles

### GitHub

Version control for:

- goals and operating contracts;
- architecture;
- schemas;
- migrations;
- tests/validators;
- runbooks;
- durable decisions;
- public-safe state pointers.

### Google Drive / Sheets

Human/control-plane mirror for:

- registries;
- scheduler;
- goals/checkpoints;
- metrics/health;
- issue/state-transition/run ledgers;
- operational collaboration.

### Constrained database

Operational state backend enforcing PK/FK/UNIQUE/CHECK/idempotency and restore/replay semantics.

## Non-negotiable boundary

GitHub must never be treated as a replacement for the operational DB, and Sheets must never be treated as an unconstrained production database.

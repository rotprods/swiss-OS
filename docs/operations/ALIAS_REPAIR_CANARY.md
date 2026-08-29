# ALIAS REPAIR CANARY — SWITZERLAND_JOB_OS

Version: **ARC-1.0**  
Status: **PRE-AUTHORITY REPAIR CONTRACT**

## Objective

Convert an ASR-1.0 semantic alias failure into a deterministic, non-destructive repair plan without inferring a new authoritative denominator.

ARC-1.0 exists for the failure mode where an entity-resolution candidate identifies the canonical target, but the persisted alias H-ID belongs to a different real-world hotel because row position or ID lineage drifted.

## Automatic quarantine eligibility

An alias edge may be proposed for canary quarantine only when all conditions hold:

```text
ASR violation = ALIAS_IDENTITY_MISMATCH
alias H-ID exists as a physical catalog record
canonical target exists
alias identity != target identity
target normalized name+city is unique in the physical catalog
resolution evidence binds the persisted alias assertion
no stable-identity proof supports the existing edge
```

Any ambiguity produces `RECONCILE_REQUIRED`.

## Canary action

The allowed action is:

```text
QUARANTINE_ALIAS_EDGE_REACTIVATE_PHYSICAL_ID
```

It means:

- preserve every physical H-ID;
- remove the semantically impossible alias edge in a canary copy;
- restore only explicitly state-like fields from a verified earlier parent where required;
- remove the corresponding alias graph edge in the canary where it is structurally identifiable;
- recompute the effective active set by PK anti-join;
- run integrity, FK, duplicate, replay and restore checks.

It does **not** mean:

```text
authority advanced
canonical H-ID allocated
HOTELS_MASTER modified
Graph/Intelligence authority reconciled
checkpoint completed
CRM_UNIVERSE_COMPLETE
outbound authorized
```

## Executable implementation

```text
src/swiss_os/asr_repair.py
```

Primary functions:

```python
plan_phantom_alias_quarantine(catalog_rows, alias_rows, resolution_rows)
apply_plan_to_alias_rows(alias_rows, plan)
```

The planner is pure and fail-closed. It never mutates persistent state.

## Required canary gauntlet

```text
ASR lineage proof = PASS
invalid edge quarantine count = expected count
physical H-ID count unchanged
SQLite integrity_check = ok
FK violations = 0
known bad edges remaining = 0
active normalized name+city duplicates = 0
repair replay unintended mutations = 0
restore integrity = ok
restore FK violations = 0
```

## Authority promotion

A successful ARC canary is only a repair candidate. Authority requires a later bounded `AUTHORITATIVE_WRITE` wave:

```text
re-read live parent/epoch
→ native HOTELS_MASTER writer available
→ apply constrained DB migration
→ mirror exact alias/active PK state to HOTELS_MASTER
→ recompute Intelligence active PK set
→ recompute Operational Graph nodes/edges
→ recompute metrics/scheduler/checkpoints/transitions
→ restore/replay/idempotency gauntlet
→ ASR-1.0 EXACT across every affected plane
→ final cross-plane reconciliation
→ COMPLETE_AUTHORITY
```

Until that wave closes:

```text
alias semantics = RECONCILE_REQUIRED
canonical allocation = FORBIDDEN
CRM_UNIVERSE_COMPLETE = FALSE
OUTBOUND = CLOSED
send_allowed = 0
```

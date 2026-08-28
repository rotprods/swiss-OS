# ALIAS SEMANTIC RECONCILIATION — SWITZERLAND_JOB_OS

Version: **ASR-1.0**  
Status: **PRE-AUTHORITY HARD GATE**

## Objective

Prevent structurally valid alias/supersession edges from corrupting canonical authority when the H-ID referenced as the alias belongs to a different real-world hotel than the entity-resolution evidence.

SQLite PK/FK integrity is necessary but insufficient. Before any authority promotion, every persisted alias edge must pass a semantic identity proof.

## Core invariant

For every edge:

```text
alias_hotel_id → canonical_hotel_id
```

all of the following must hold:

```text
alias H-ID exists in the physical catalog
canonical target H-ID exists in the physical catalog
alias != canonical target
exactly one compatible entity-resolution record binds the alias H-ID
entity-resolution candidate identifies the physical alias H-ID
entity-resolution target agrees with the persisted canonical target when explicitly recorded
alias and canonical target are proven to represent the same real-world entity
```

The default deterministic proof is normalized exact `name + city`. A stronger resolver may set `stable_identity_verified = true` only when equivalence is already proved from stable detail/source identity. That flag is evidence state, not a heuristic escape hatch.

## Fail-closed classifications

Material failures include:

```text
INVALID_ALIAS_EDGE
DUPLICATE_ALIAS_EDGE
ALIAS_HOTEL_MISSING
CANONICAL_TARGET_MISSING
SELF_ALIAS
ALIAS_EVIDENCE_MISSING
ALIAS_EVIDENCE_AMBIGUOUS
IDENTITY_FIELDS_MISSING
ALIAS_IDENTITY_MISMATCH
ALIAS_EVIDENCE_IDENTITY_MISMATCH
REAL_WORLD_EQUIVALENCE_UNPROVEN
RESOLUTION_TARGET_MISMATCH
```

`ALIAS_IDENTITY_MISMATCH` is the critical pattern where the entity-resolution candidate matches the canonical target but not the actual physical identity behind the purported alias H-ID. This catches row/ID drift that FK checks cannot detect.

Any violation produces:

```text
alias_semantics_state = RECONCILE_REQUIRED
alias_semantics_valid = false
authority_advanced = false
h_id_allocations = 0
outbound_opened = false
send_allowed = 0
```

No canonical count may advance from a parent whose alias semantics are `RECONCILE_REQUIRED`.

## Executable contract

Implementation:

```text
src/swiss_os/alias_semantics.py
```

Primary function:

```python
validate_alias_semantics(catalog_rows, alias_rows, resolution_rows)
```

It is read-only and deterministic.

## Repair protocol

A failed edge does **not** authorize deleting an alias or reactivating the superseded H-ID. Repair must proceed as a non-authoritative canary:

```text
reconstruct pre-supersession lineage
→ resolve intended duplicate candidate by stable identity
→ bind candidate to actual physical H-ID by PK, never row offset
→ preserve every physical H-ID
→ construct repair canary
→ rerun ASR-1.0
→ recompute active denominator
→ reconcile Intelligence + Operational Graph + scheduler/checkpoints/transitions
→ restore/replay/idempotency gauntlet
→ authoritative cross-plane wave only if every gate passes
```

If the intended duplicate physical row cannot be proved, keep the edge `RECONCILE_REQUIRED` rather than inferring a replacement denominator.

## Production gate

ASR-1.0 is mandatory whenever the authority parent contains aliases/superseded IDs or a wave changes alias semantics.

Required before `COMPLETE_AUTHORITY`:

```text
alias_semantics_state = EXACT
alias semantic violations = 0
structural invalid alias targets = 0
DB ↔ HOTELS_MASTER alias PK sets = exact
Operational Graph ALIASES_TO edges = exact
active denominator recomputed from reconciled semantics
```

This gate is independent from CRM source coverage. Passing source-scope reconciliation cannot override a failed alias semantic gate.

## Outbound lock

ASR-1.0 never authorizes outbound.

```text
OUTBOUND = CLOSED
send_allowed = 0
```

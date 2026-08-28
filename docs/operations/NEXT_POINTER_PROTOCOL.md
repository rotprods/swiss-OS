# NEXT POINTER PROTOCOL — SWITZERLAND_JOB_OS

Version: **NPP-1.0**  
Status: **CANONICAL CONTINUATION CONTRACT**

## Purpose

`NEXT` is the durable machine-readable continuation pointer emitted at the end of every material Meta Execution activation or whenever control must pass to another agent/runtime.

It prevents continuation from depending on chat memory.

`NEXT` is **not** authority. It is a resumable instruction whose parent/authority assertions must be revalidated before execution.

## Required fields

```json
{
  "schema_version": "NPP-1.0",
  "project": "SWITZERLAND_JOB_OS",
  "generated_at": "ISO8601",
  "cycle_id": "...",
  "parent_git_sha": "...",
  "authority_epoch": "...",
  "authority_parent": "...",
  "execution_mode": "...",
  "selected_route": "...",
  "next_route": "...",
  "goal_id": "...",
  "checkpoint_id": "...",
  "hard_blockers": [],
  "dependencies": [],
  "required_inputs": [],
  "capabilities_required": [],
  "artifacts": [],
  "graph_impact": "NONE|META|OPERATIONAL|BOTH",
  "authority_advance_allowed": false,
  "canonical_id_allocation_allowed": false,
  "outbound_allowed": false,
  "resume_instructions": [],
  "done_when": []
}
```

## Hard defaults

Every pointer defaults to:

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
```

A pointer cannot pre-authorize a future irreversible action.

## Resume semantics

A new activation MUST NOT execute `NEXT` blindly.

It first performs:

```text
read current GitHub main
→ compare parent_git_sha
→ reconstruct operational authority
→ compare authority_epoch / authority_parent
→ read current blockers/capabilities
→ anti-join any provisional work
→ recalculate MEP route
```

If the parent moved, `NEXT` becomes an input to `RECOVERY_RECONCILE`, not an instruction to force-write.

## Meta-PR chaining

System-definition work may execute as a sequence of atomic meta-PRs, but they are **serially rebased by reconstruction**, not blindly stacked.

Canonical chain:

```text
PR_n branch from current main
→ implementation
→ tests / guards
→ PR_n
→ CI
→ adversarial review
→ merge
→ reread new main SHA
→ reconstruct authority/capabilities
→ persist NEXT_n
→ create PR_n+1 from the new main only if it is still the highest-value safe route
```

Forbidden:

```text
open many dependent PRs from stale parent
→ assume all will merge unchanged
```

This makes concurrent agent work absorbable rather than destructive.

## Activation chaining

Within one runtime activation, completing a wave does not imply stopping.

The Meta Execution session must:

```text
WAVE complete
→ QA/persist
→ compute NEXT
→ if safe route exists and runtime remains available:
     immediately execute next meta-cycle/wave
→ otherwise persist NEXT and close activation
```

The external scheduled wake-up is only a re-entry mechanism after the runtime ends; it is not the primary production cadence.

## Persistence

Persist the latest pointer in every available relevant recovery plane:

```text
GitHub public-safe handoff/state reference
Drive project context/recovery folder
ChatGPT Library /SWITZERLAND_JOB_OS/NEXT.json
Project Memory Meta Graph
```

Do not store private credentials, raw PII or operational secrets in public GitHub NEXT artifacts.

## CRM-universe NEXT priority

Until `CRM_UNIVERSE_COMPLETE = TRUE`, preferred continuation ordering remains:

```text
AUTHORITY_RECOVERY
→ STRUCTURED_SOURCE_CAPTURE
→ MEMBER_DIRECTORY_MANIFEST
→ SOURCE_SCOPE_RECONCILIATION
→ FROZEN_CANDIDATE_EXPORT
→ MASS_INGEST_STAGING
→ EXACT_CURRENT_REFRESH
→ TERMINAL_MAPPING
→ AUTHORITATIVE_PROMOTION
```

MEP may select a safe fallback when the preferred route lacks capability.

## Closure rule

No material activation closes without either:

```text
NEXT persisted
```

or

```text
terminal project state / explicit BLOCKED_P0 with no safe productive route
```

An empty or vague “continue later” handoff is invalid.
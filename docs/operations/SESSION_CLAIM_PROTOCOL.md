# SESSION / CLAIM / FENCING PROTOCOL — SCP-1.0

Status: **V2 CANDIDATE CONTRACT**

## Purpose

Add explicit multi-agent ownership to MEP/WOP without creating a new authority plane.
Every material activation receives `project_id`, `agent_id`, globally unique `session_id`, `workstream_id`, `objective_id` and `correlation_id`.

## Cognitive barrier

Before material mutation, the writer MUST possess all of:

1. a live WRITE `ScopeClaim`;
2. a non-expired lease;
3. a fencing token equal to the current live fence;
4. a ContextPack pinned to current main SHA, authority parent SHA, event watermark and projection revision;
5. no conflicting active WRITE claim over overlapping resource + semantic scopes;
6. all existing MEP/WOP authority and capability gates.

Failure means `RECOVERY_RECONCILE` or a typed blocker, never force-write.

## Scope model

Claims bind two independent dimensions:

- `resource_scope`: concrete surface such as `repo/docs/state`, `db/hotels`, `sheets/HOTELS_V2`, `source/SRET/050`;
- `semantic_scope`: meaning such as `source-resolution`, `entity-authority`, `candidate-assets`, `architecture`.

Two READ claims may overlap. WRITE vs WRITE, and WRITE vs READ, collide when both resource and semantic scopes overlap across different sessions. Claims remain historical nodes after release/expiry but lose mutation authority.

## Fencing

Fencing tokens are monotonically increasing within the protected authority/resource domain. A writer with token `n` MUST fail when live token is greater than `n`, even if its wall-clock lease has not expired. This protects against delayed workers, agent death and clock uncertainty.

## Session lifecycle

```text
PROPOSED
→ ACTIVE
→ HANDOFF_PENDING | COMPLETE | FAILED | EXPIRED
→ CLOSED
```

A session may execute multiple bounded WOP waves, but every material wave records `session_id`. A closed or expired session cannot regain authority through an old ContextPack.

## Required events

```text
HELLO / WORK_STARTED
CLAIM_ACQUIRED
CLAIM_RELEASED
CONTEXT_REFRESHED
WAVE_STARTED
WAVE_CLOSED
HANDOFF_EMITTED
SESSION_CLOSED
```

Events conform to EEP-2.0 and carry expected aggregate version.

## DoD

SCP-1.0 is implemented only when collision, expiry, fencing, main-parent drift and event-watermark drift tests fail closed, and PRG G19 validates the contract before authority-changing work.
# TASKS — CANONICAL POINTER

**Authority:** execution-navigation pointer  
**Scope:** V2.2 implementation program and live machine task frontier  
**Owner:** Technical Product Manager / Mission Commander  
**Source revision:** COS V2.2 / `/GRAPH-REFACTOR-V2`

Machine-readable task state is:

`docs/state/v2/tasks.json`

The current task file is authoritative for execution navigation only; it does not replace operational hotel/candidate/application authority.

Canonical architecture:

`docs/architecture/V2_ARCHITECTURE.md`

Stable goal contract:

`GOAL.md`

A task is not DONE because code, prose or a PR exists. Applicable implementation, executed tests, security review, state/graph/evidence updates and zero-context handoff must reconcile. Typed blockers such as `BLOCKED_HUMAN`, `BLOCKED_REVIEW` and `BLOCKED_DOMAIN_CLAIM_REQUIRED` are valid system outcomes and must not be bypassed for velocity.

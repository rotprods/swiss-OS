# SWITZERLAND_JOB_OS — ZERO-CONTEXT HANDOFF

**Generated:** 2026-09-01  
**Repository:** `rotprods/swiss-OS`  
**Verified Git main at handoff:** `6ca946e61d6145424ff06754831a567d6e2b2f3e`  
**Hotel authority epoch:** `HS_ENTITY_EPOCH_2026-08-25_E4`  
**Authority materialized SHA:** `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6`

This bundle exists so a completely fresh session can recover the project without relying on chat memory.

## Critical rule

There are four different states and they MUST NOT be conflated:

1. **Git main** — executable contracts/code and merged architecture.
2. **Hotel/CRM authority** — current authoritative hotel universe and IDs.
3. **Staging / canary / open PRs** — useful work that is NOT authority until promoted.
4. **Chat context** — disposable cache, never source of truth.

At handoff time:
- Git main is `6ca946e61d6145424ff06754831a567d6e2b2f3e` after merged PR #405.
- Authoritative hotel/CRM state is E4 with **690 physical/canonical rows** and **H-0691 UNALLOCATED**.
- `CRM_UNIVERSE_COMPLETE = FALSE`.
- `OUTBOUND = CLOSED`.
- `send_allowed = 0`.
- Production entity-resolution NEXT is B07, but open PR #404 must be revalidated against fresh main before any merge/promotion.
- Application pipeline has advanced independently to AAG-3.1 with 16 non-compensable hard gates.

## Files in this bundle

- `01_ACTA_DE_CONSCIENCIA_OPERACIONAL.md`
- `02_HISTORICAL_REGRESSION.md`
- `03_CONTEXT_LAYERS_AND_AUTHORITY.md`
- `04_CURRENT_STATE_EXACT.md`
- `05_NEXT_ITERATION_PHASES.md`
- `06_ZERO_CONTEXT_METAPROMPT.md`
- `07_PR_BODY.md`
- `08_NEW_SESSION_MESSAGE.md`

Start with `06_ZERO_CONTEXT_METAPROMPT.md` in the next session.

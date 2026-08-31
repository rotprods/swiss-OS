# META HANDOFF — 2026-08-31 — CRM CURRENT REBASE

## Reconstruction

Bootstrap `main` was `02dad1a5bd82219b34430b5fd1cee3ee088642b6`. Immediate ancestry observed:

1. `02dad1a5bd82219b34430b5fd1cee3ee088642b6` — merged PR #382, current Gonten review-lineage re-anchor.
2. `df375cf63200ed83fdc172ae7d1274e4bb458a34` — merged PR #381, coherent current CRM source projection.
3. `39302962480d708ce408cce636e49da05874670f` — prior main parent.

Operational authority remains E4 / `70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6` with 690 canonical rows, zero persisted H-ID alias edges and `H-0691` unallocated.

## Source truth correction

The current HotellerieSuisse member-directory source is now `HS-MEMBER-DE-33339392661`, run `33339392661`, artifact `9740219406`: 172 pages, 2061 records, `coverage_complete=true`, records SHA-256 `b16fdb63a01149e10feb4d506f38301644b73a612f898ce72567ec4fa92da404`.

This supersedes the earlier partial run `33206402141` / artifact `9700376482` for current source identity. Historical review lineage may be carried only where the current-source projection explicitly proves that carry.

## Current mapping frontier

`623` exact active matches + `35` reviewed exceptional carry-forward mappings = `658` terminal current source mappings. `1403` current source records remain `RECONCILE_REQUIRED`; 34 authority rows remain reverse source gaps. The two changed Gonten identities were separately re-anchored and remain pre-authority `NEW_CANONICAL` reviews with no H-ID reservation/allocation.

## Open governing work

P0 issue #240 remains the governing closure program. Issue #239 governs deterministic/batch-safe source resolution. Issue #14 remains the structured discover.swiss acquisition/SSR path. Issue #12 is resolved: native Sheets write exists, but authority remains DB-first.

## Capability routing / MEP fallback

The discover.swiss subscription key and capture-valid structured manifest are absent, so SSR-1.0 cannot execute now. The fallback is not idle: continue bounded current-member-directory entity-resolution batches over the 1403 unresolved records. File Library write is unavailable, so durable recovery is GitHub + Drive. Drive native Sheets write exists but is not used for authority in this wave.

## Safety

No operational authority mutation, canonical allocation/reservation, outbound action or irreversible external business action is authorized by this handoff. `OUTBOUND=CLOSED`, `send_allowed=0`.

## NEXT

`CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION`

Before each batch: verify current main is this handoff's parent or descendant, E4 hash unchanged, `H-0691` still unallocated, current source artifact/hash unchanged, and no competing authority claim. Use immutable source keys and current evidence. Similarity is review-only and cannot autobind. Structured discover.swiss SSR becomes eligible only after a valid runtime credential produces a capture-valid manifest. Authority promotion becomes eligible only after durable DB-first E4 egress is recovered and all cross-plane gates pass.

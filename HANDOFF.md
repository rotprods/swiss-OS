# HANDOFF — CANONICAL ZERO-CONTEXT POINTER

**Authority:** navigation/continuity pointer only  
**Scope:** current execution resumption  
**Owner:** Mission Commander / Memory Systems  
**Source revision:** COS V2

A successor does not resume from chat memory.

Read, in order:

1. `GOAL.md`
2. `STATE.md`
3. `ARCHITECTURE.md`
4. `docs/state/v2/project-state.json`
5. `docs/state/v2/context-pack.json`
6. `docs/state/v2/active-claims.json`
7. `TASKS.md`
8. latest applicable domain handoff under `docs/handoffs/`

The ContextPack is acceleration, not authority. V2.1 does **not** require its base SHA to equal the current `main` HEAD: concurrent unrelated commits may advance `main`. Reject the pack when its `base_main_sha` is no longer an ancestor of the execution head, when any declared `relevant_paths` changed relative to `relevant_scope_revision`, or when projection, authority revision, event watermark or pack hash is stale. A newer descendant HEAD with no relevant-scope drift is valid.

Current V2 workstream is architecture/pre-authority only. Hotel authority, canonical-ID allocation and outbound execution remain outside this handoff's authority ceiling.

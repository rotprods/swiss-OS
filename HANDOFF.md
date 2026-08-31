# HANDOFF — CANONICAL ZERO-CONTEXT POINTER

**Authority:** navigation/continuity pointer only  
**Scope:** current execution resumption  
**Owner:** Mission Commander / Memory Systems  
**Source revision:** COS V2 + CSP-1.0

A successor does not resume from chat memory.

Read, in order:

1. live GitHub `main` SHA/ancestry;
2. `GOAL.md`;
3. `STATE.md`;
4. `ARCHITECTURE.md`;
5. `docs/operations/CONTEXT_SURVIVAL_PROTOCOL.md`;
6. `docs/continuity/CONTEXT_SURVIVAL.json` and verify every pinned digest;
7. `docs/state/v2/project-state.json`;
8. `docs/state/v2/context-pack.json`;
9. `docs/state/v2/active-claims.json` plus durable claim records;
10. `TASKS.md`;
11. latest explicit domain NEXT and applicable handoff under `docs/state/` + `docs/handoffs/`;
12. `docs/handoffs/NEXT_ITERATION_METAPROMPT_V3.md` when a full zero-context agent bootstrap is required.

The ContextPack and Context Survival checkpoint are acceleration/recovery attestations, not operational authority. V2.1 does **not** require a stored ancestry floor to equal current `main` HEAD: concurrent descendant commits may advance `main`. Reject a pack/checkpoint when its ancestry floor is no longer an ancestor, when a pinned/relevant file digest drifts, or when projection, authority revision, active-claim state, event watermark or payload hash is stale. A newer descendant HEAD is valid only after those checks pass.

If the Context Survival checkpoint is stale, reconstruct it from live durable sources before material continuation; stale recovery metadata is never a reason to guess from chat memory.

Current V2/CSP workstream is coordination/pre-authority only. Hotel authority, canonical-ID allocation and outbound execution remain outside this handoff's authority ceiling.

# ARCHITECTURE — CANONICAL POINTER

**Authority:** stable architecture pointer  
**Scope:** project architecture, not mutable hotel authority  
**Owner:** Principal Systems Architecture  
**Source revision:** `/GRAPH-REFACTOR-V2`  
**Supersedes:** no historical document; it selects the canonical architecture surface.

The canonical V2 architecture is:

`docs/architecture/V2_ARCHITECTURE.md`

Existing V1 domain contracts remain valid where V2 explicitly marks them **KEEP** or **REFINE**. `docs/architecture/SYSTEM_MAP.md`, `AUTHORITY_MODEL.md`, and `ENGINE_REGISTRY.md` remain supporting contracts; they do not compete with V2.

Mutable truth never lives here. Read:

1. `STATE.md` for the public-safe operational frontier.
2. `docs/state/v2/project-state.json` for V2 machine coordination state.
3. `docs/state/v2/context-pack.json` for zero-context resumption.
4. physical/constrained authority and cross-plane receipts before any authority mutation.

No architecture document can allocate canonical IDs, open outbound, or promote a canary.

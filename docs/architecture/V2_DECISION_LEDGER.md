# V2 DECISION LEDGER

## ADR-V2-001 — Preserve operational authority; add separate coordination authority

**Problem:** agent/session continuity and concurrency are implicit.  
**Selected:** append-only coordination events + claims/projections; operational DB/Sheets/Graph authority unchanged.  
**Alternatives rejected:** GitHub-as-operational-DB; chat memory; one giant graph as authority.  
**Why:** minimum migration risk and no second hotel truth.  
**Tradeoff:** two explicit authority hierarchies must be understood.  
**Reversible:** high; V2 coordination can be removed without touching hotel authority.  
**Confidence:** HIGH.

## ADR-V2-002 — Event ledger + disposable projections

**Problem:** mutable handoff summaries lose history and cannot prove replay.  
**Selected:** immutable events; projections derived and hash-revisioned.  
**Rejected:** mutable session registry as primary history.  
**Risk:** event schema drift. Mitigation: versioned schemas/reducers.  
**Confidence:** HIGH.

## ADR-V2-003 — Git files first; no new distributed infrastructure

**Problem:** coordination needs durability but current load is tiny.  
**Selected:** public-safe JSON events/claims in Git + CI guards.  
**Rejected now:** Kafka/Redis/Postgres/etcd/Kubernetes.  
**Trigger to reconsider:** measured event/claim volume or writer concurrency makes Git-based append/PR flow a bottleneck.  
**Confidence:** HIGH.

## ADR-V2-004 — Claims are bounded ownership, not authority

A Claim contains resource/semantic scopes, excluded scopes, authority ceiling and monotonic fencing token. It can coordinate writers but cannot grant domain authority.  
**Confidence:** HIGH.

## ADR-V2-005 — ContextPack is derived acceleration, never authority

**Initial hypothesis (SUPERSEDED):** pin ContextPack validity to equality with live `main` HEAD.  
**Observed failure:** during the V2 gauntlet, unrelated concurrent provider-identity commits repeatedly advanced `main` after a green CI run. Exact HEAD equality therefore made a valid ContextPack self-stale even though its relevant architecture inputs and authority revision had not changed.  
**Selected V1.1 semantics:** persist `base_main_sha`, require that base to remain an ancestor of the execution head, bind the pack to explicit `relevant_paths` and a deterministic `relevant_scope_revision`, and independently pin projection revision, authority revision, event watermark and pack hash.  
**Reject when:** ancestry breaks, relevant scope drifts, authority/projection revision drifts, watermark is incompatible, or the hash fails.  
**Why selected:** preserves fail-closed semantics while permitting safe unrelated concurrency.  
**Alternative rejected:** chase every new HEAD by rewriting the ContextPack; this creates coordination churn and makes the pack depend on unrelated domain work.  
**Confidence:** HIGH — directly derived from repeated live-main movement during this refactor.

## ADR-V2-006 — Preserve V1 domain engines

The current architecture already has strong authority, evidence, wave, recovery and graph separation. Refactor only measured defects; do not rewrite entity/evidence/domain engines for aesthetic consistency.  
**Confidence:** HIGH.

## ADR-V2-007 — Root canonical pointers

Add `ARCHITECTURE.md`, `HANDOFF.md`, `TASKS.md`, `LEXICON.md` so a zero-context operator has deterministic entry points. Historical handoffs remain history.  
**Confidence:** HIGH.

## ADR-V2-008 — Treat duplicate bootstrap as escaped bug family

The session produced a duplicate coordination issue before detection. The observed instance is closed; the failure family becomes idempotency/collision tests.  
**Confidence:** HIGH, directly observed.

## ADR-V2-009 — Branch protection deferred pending operator-fit evidence

Live main is currently unprotected. Protection would reduce accidental direct writes but may conflict with rapid solo-agent waves. Define the interface now; decide after measuring PR-only friction and ensuring automation can operate.  
**Confidence:** MEDIUM. Owner: Git/DevSecOps. Trigger: V2 migration phase.

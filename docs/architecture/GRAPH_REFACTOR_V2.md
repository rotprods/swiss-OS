# GRAPH REFACTOR V2 — CURRENT-TRUTH ARCHITECTURE SYNTHESIS

Status: **V2 CANDIDATE — IMPLEMENTED ON BRANCH, NOT AUTHORITY**

## Executive V2

SWITZERLAND_JOB_OS already has strong production primitives: MEP-2.0/COLETTE, WOP-1.1, ASR/SRR/SRET/SMO/RAGR, constrained SQLite, Sheets control-plane mirroring, operational/meta graph separation, fail-closed source mapping, recovery bundles and adversarial CI. V2 therefore does **not** replace those systems.

V2 closes the highest-value remaining coordination defect: material work has Wave/Run identity but lacks a uniform first-class `Session + ScopeClaim + Lease/FencingToken + EventEnvelope + ContextPack` contract that rejects stale or colliding parallel agents before mutation.

Authority hierarchy remains unchanged:

```text
fully synchronized constrained operational authority
> live control plane / PK mirror
> validated manifests
> GitHub STATE pointer
> historical prose / Library recovery
```

The concurrency kernel is a guard/projection layer. It never promotes canonical state by itself.

## Current → V2 delta

| Concern | Current | V2 |
|---|---|---|
| Execution identity | Wave/run IDs | KEEP + first-class globally unique Session |
| Concurrency | ancestry re-read + anti-join | KEEP + scope claims, leases and fencing |
| Stale context | protocol requires re-read | executable ContextPack watermark/fence |
| Events | run/transition/meta deltas | uniform EventEnvelope for material coordination |
| Graph | operational + meta projections | KEEP + temporal hyperrelation projection contract |
| Authority | cross-plane promotion | KEEP unchanged |
| SQLite | constrained backend | KEEP; no Postgres migration yet |
| Parallel agents | convention-driven | explicit collision/ownership guard |
| Recovery | durable recovery surfaces | KEEP + zero-context session/ContextPack recovery |

## Greenfield comparison

**KEEP:** MEP, WOP, Engine Registry, PRG, ASR, source-resolution protocols, constrained DB, PK Sheets mirror, Operational Graph, Meta Graph, GitHub state contracts, recovery bundles.

**REFINE:** concurrency, session identity, state/event watermarks, active scope ownership, stale-PR/claim detection, event schema and ContextPack.

**DEPRECATE:** implicit ownership inferred from chat, branch names or stale handoffs; any writer that checks only a local copy without a live fence.

**DEFER:** shared Postgres/Supabase authority. Trigger: measured genuinely concurrent multi-writer operational transactions that cannot be safely serialized through WOP without material queue latency/collision risk. Until then, SQLite + bounded authoritative waves is simpler and safer.

## Temporal hypergraph kernel

New first-class node types:

```text
Session
ScopeClaim
Lease
FencingToken
EventEnvelope
ContextPack
EventWatermark
ProjectionRevision
AuthorityFence
```

Core relations:

```text
Session --CLAIMS--> ScopeClaim
Session --EMITS--> EventEnvelope
Session --USES--> ContextPack
Session --EXECUTES--> Wave
ScopeClaim --SCOPES--> Resource
ScopeClaim --SCOPES_SEMANTICS--> SemanticScope
ScopeClaim --FENCED_BY--> FencingToken
ScopeClaim --VALID_UNTIL--> Lease
ContextPack --PINNED_TO--> GitMainSHA
ContextPack --PINNED_TO--> AuthorityParent
ContextPack --PINNED_TO--> EventWatermark
ContextPack --PINNED_TO--> ProjectionRevision
EventEnvelope --CAUSED_BY--> EventEnvelope
EventEnvelope --ATTRIBUTED_TO--> Session
EventEnvelope --MUTATES_OR_OBSERVES--> Aggregate
```

A material decision may modify multiple contracts/modules/tests/risks simultaneously; V2 represents that as a hyperrelation/projection over shared IDs rather than duplicated canonical truth.

## COS dimensions

- L0 Visual: project clusters and authority boundaries.
- L1 Execution: Goal→Checkpoint→Wave→Task→Test→Evidence.
- L2 State: Session/Claim/Wave/Authority/Source mapping machines.
- L3 Dependency: blockers, transitive dependencies and blast radius.
- L4 Call Graph: executable Python kernel and existing core.
- L5 Control Flow: fail-closed mutation barrier.
- L6 DataFlow: source→evidence→mapping→authority→projection.
- L7 Compute: bounded batches; no measured distributed-compute need.
- L8 Knowledge: facts/claims/evidence/decisions.
- L9 Semantic: canonical lexicon and deprecated aliases.
- L10 Similarity: review aid only; never authority.
- L11 GraphRAG: ContextPack/recovery retrieval target.
- L12 Memory: Git/DB/Drive/Library roles + invalidation.
- L13 Agent: sessions, claims, leases, collisions, handoffs.
- L14 Tool: connector/provider capability and trust boundaries.
- L15 Workflow: MEP/WOP and compensation/recovery.
- L16 Network: NOT_APPLICABLE beyond external provider boundaries; no new network infra.
- L17–L19: NOT_APPLICABLE until a measured domain need exists.

## Security and reliability

External/provider/web/issue/PR/Drive/prompt content is untrusted data. V2 explicitly addresses stale writers, overlapping agent claims, expired leases, replayed events, stale ContextPacks, moved main/authority parents and confused-deputy authority escalation. The kernel stores no credentials and introduces no public PII.

## Recovery / death drill target

A zero-context successor must reconstruct current main SHA, authority epoch/parent, `STATE.md`, active barriers/claims, event watermark, projection revision and next safe action. If any fence differs from a cached ContextPack, the pack loses write authority.

## Migration strategy

1. Introduce protocols + pure validation kernel and tests — read-only architecture change.
2. Wire AGENTS/WOP/PRG and CI guard after tests pass.
3. Persist session/claim/event coordination state in the existing constrained backend or a dedicated coordination table, without changing hotel authority.
4. Run two-agent collision, stale-writer, replay and death drills.
5. Adopt event-first coordination incrementally; do not rewrite existing hotel state into a synthetic event history.
6. Consider a shared transactional backend only after a measured concurrency trigger.

## V2 acceptance

`V2_FINAL` is forbidden until implementation tests + contract guard + CI pass, PR adversarial review passes, stale open PR overlap is classified, concurrency/death/replay tests pass, and the refactor causes zero authority/H-ID/outbound changes. Until then: `V2_CANDIDATE`.
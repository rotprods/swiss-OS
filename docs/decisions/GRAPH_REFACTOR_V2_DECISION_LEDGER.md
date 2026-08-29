# GRAPH REFACTOR V2 — DECISION LEDGER

Version: **DL-V2-1.0**  
Status: **FOUNDATION DECISIONS ACCEPTED; MIGRATION DECISIONS GATED**  
Owner: Principal Systems Architect  
Last updated: 2026-08-30

## DEC-V2-001 — Preserve existing operational authority stores

- **Problem:** V2 needs richer semantics without introducing a competing truth.
- **Constraints:** SQLite/HOTELS_MASTER/Operational Graph/Intelligence already carry validated domain state.
- **Alternatives:** replace with graph DB; move all state to event ledger; keep current stores.
- **Selected:** keep current authority stores; V2 ledger/graph are coordination/history/projections until migration.
- **Why:** lowest regression/migration risk and strongest existing evidence.
- **Rejected:** graph DB duplicates authority; pure event sourcing requires unjustified historical reconstruction.
- **Tradeoff:** cross-plane reconciliation remains necessary.
- **Risk:** a projection is mistaken for authority.
- **Mitigation:** authority ceiling, PRG/WOP and manifest hard fields.
- **Reversibility:** high.
- **Reconsider:** only after measured store/reconciliation SLO failure.
- **Confidence:** HIGH.

## DEC-V2-002 — Typed temporal hypergraph as canonical semantic model

- **Problem:** binary/prose relationships cannot represent multi-party decision impact cleanly.
- **Alternatives:** plain property graph; relational-only model; RDF/ontology platform; typed in-process hypergraph.
- **Selected:** typed temporal nodes, edges and role-bearing hyperedges with deterministic projections.
- **Why:** queryable decision/risk/test/migration relations without new infrastructure.
- **Rejected:** property graph alone obscures hyperrelations; RDF platform increases complexity before need.
- **Tradeoff:** custom kernel/query projections require maintenance.
- **Risk:** bespoke abstraction becomes overgeneralized.
- **Mitigation:** small standard-library implementation and domain-specific nodes retained.
- **Reversibility:** high at foundation, medium after migration.
- **Reconsider:** query/performance SLO breach.
- **Confidence:** HIGH.

## DEC-V2-003 — Append-only hash-chained causal event ledger

- **Problem:** current state says what is true but does not universally explain why/how it changed.
- **Alternatives:** mutable logs; Git history only; Kafka/event platform; JSONL causal ledger.
- **Selected:** canonical-JSON, SHA-256 chained, sequenced JSONL contract with causation IDs.
- **Why:** deterministic replay/corruption detection at current scale.
- **Rejected:** mutable logs lack integrity; Git omits operational causation; Kafka is unjustified.
- **Tradeoff:** snapshot/compaction policy may be needed later.
- **Risk:** ledger mistaken for operational authority.
- **Mitigation:** explicit authority ceiling and domain-store separation.
- **Reversibility:** high.
- **Reconsider:** throughput/replay-time trigger.
- **Confidence:** HIGH direction, MEDIUM storage longevity.

## DEC-V2-004 — First-class Session, Claim, Lease and FencingToken

- **Problem:** active agents and overlapping work are not safely governed by prose/handoffs alone.
- **Alternatives:** branch convention; global mutex; optimistic merge only; scoped claims plus fencing.
- **Selected:** globally unique sessions, scoped claims, expiring leases and monotonic fencing tokens.
- **Why:** preserves safe parallelism and rejects stale writers.
- **Rejected:** conventions are unenforced; global mutex destroys parallelism; Git merge is too late for external/state mutations.
- **Tradeoff:** coordination state and expiry semantics must be maintained.
- **Risk:** dead lease blocks progress or clock assumptions drift.
- **Mitigation:** bounded expiry, takeover, heartbeats and server/ledger timestamps during production migration.
- **Reversibility:** medium after adoption.
- **Reconsider:** multi-node/distributed lease requirements.
- **Confidence:** HIGH.

## DEC-V2-005 — Deterministic ContextPack rather than conversational memory

- **Problem:** chat/session context can be stale, compacted or unavailable.
- **Alternatives:** rely on STATE.md; load all docs; vector-memory retrieval; bounded compiled ContextPack.
- **Selected:** digested pack with main SHA, authority, event watermark, projection revision, contracts, barriers, claims, work/evidence and NEXT.
- **Why:** bounded, inspectable, freshness-verifiable and recoverable.
- **Rejected:** STATE alone lacks complete lineage; all-doc loading is expensive/noisy; vector similarity is not authority.
- **Tradeoff:** pack must be rebuilt when inputs move.
- **Risk:** pack itself becomes authority or leaks secrets.
- **Mitigation:** explicit cache role, freshness assertions and redaction.
- **Reversibility:** high.
- **Confidence:** HIGH.

## DEC-V2-006 — Assurance compiler for architecture claims

- **Problem:** prose can claim completeness without owners/tests/evidence.
- **Alternatives:** manual checklist; CI-only tests; graph-aware assurance compiler.
- **Selected:** compile graph integrity, critical owner/test gaps, invariant evidence and ranked gaps.
- **Why:** makes acceptance objective and machine-readable.
- **Rejected:** checklist is drift-prone; CI alone does not map tests to architecture claims.
- **Tradeoff:** symbolic architecture tests still require physical qualification checkpoints.
- **Risk:** metrics/gates are gamed.
- **Mitigation:** distinct result states, SHA-bound attestation and adversarial review.
- **Reversibility:** high.
- **Confidence:** HIGH.

## DEC-V2-007 — SHA-bound test attestation before compilation

- **Problem:** a compiler could self-declare symbolic tests PASS without proof that the exact revision was tested.
- **Alternatives:** trust CI order; boolean `--tests-passed`; exact attestation file.
- **Selected:** require a test-result set bound to exact commit SHA and evidence reference.
- **Why:** prevents moved-main/stale-result acceptance.
- **Rejected:** CI order is implicit; boolean is forgeable/underspecified.
- **Tradeoff:** one extra CI artifact.
- **Risk:** attestation generated without real tests.
- **Mitigation:** workflow generates it only after full regression suite exits successfully; artifact preserves run identity.
- **Reversibility:** high.
- **Confidence:** HIGH.

## DEC-V2-008 — Mutation loop guard for irreversible actions

- **Problem:** live issue-create tool loop produced duplicate administrative objects.
- **Alternatives:** prose warning; tool-specific dedupe; universal mutation-attempt model.
- **Selected:** idempotency identity, durable-object lookup, strategy budget, `CHANGE_STRATEGY` and `STUCK_LOOP`.
- **Why:** generalizes to PR/file/calendar/message/application creation.
- **Rejected:** prose already failed; tool-specific fixes duplicate logic.
- **Tradeoff:** callers must persist/replay attempts.
- **Risk:** legitimate retries suppressed.
- **Mitigation:** semantic idempotency keys include action/target/scope; strategy can change after failure.
- **Reversibility:** high.
- **Confidence:** HIGH.

## DEC-V2-009 — COS dimensions as projections, not subsystems

- **Problem:** 20D analysis could produce symmetry-driven overengineering.
- **Alternatives:** service per dimension; documentation only; projection registry.
- **Selected:** one registry and derived projections with ACTIVE/DEFERRED/NOT_APPLICABLE states.
- **Why:** shared IDs and no duplicated authority/infrastructure.
- **Rejected:** per-dimension services add cognitive/operational cost; prose-only views are not testable.
- **Tradeoff:** some dimensions remain light until domain demand.
- **Reversibility:** high.
- **Confidence:** HIGH.

## DEC-V2-010 — Strangler migration, no big-bang rewrite

- **Problem:** current production is active and concurrent; replacing it risks regression and lost authority.
- **Alternatives:** immediate cutover; indefinite shadow-only mode; checkpointed strangler migration.
- **Selected:** foundation → shadow compile → parity → drills → new-wave coordination → history backfill → cutover.
- **Why:** reversible, measurable and compatible with ongoing CRM work.
- **Rejected:** big bang has excessive blast radius; shadow forever delivers no operational value.
- **Tradeoff:** temporary dual projection paths and migration overhead.
- **Risk:** prolonged fragmentation.
- **Mitigation:** CP0–CP14 with explicit cutover and deprecation tasks.
- **Reversibility:** high until CP13, rollback-tested thereafter.
- **Confidence:** HIGH.

## DEC-V2-011 — Do not introduce distributed infrastructure now

- **Problem:** graph/event/agent language can tempt premature Kafka, Redis, Neo4j, Kubernetes or microservices.
- **Selected:** Python standard library, JSON/JSONL and current SQLite/GitHub/Drive primitives.
- **Why:** current scale and failure modes do not justify distributed operating cost.
- **Trigger:** measured event throughput, projection-rebuild SLO, unsolved writer contention, impractical local data volume or durable provider fan-out.
- **Confidence:** HIGH.

# ADR-0001 — Typed Temporal Hypergraph over Existing Authority Stores

Status: **ACCEPTED FOR V2 FOUNDATION; PRODUCTION ADOPTION GATED**  
Date: 2026-08-30  
Owners: Principal Systems Architect, Data Architect, Reliability Architect

## Problem

The project has mature domain contracts and constrained state, but architecture, causation, sessions, claims, risks, tests and handoffs are distributed across code, documents, PRs, issues, Sheets and chat-derived summaries. Direct graphs capture binary relations but material decisions often affect multiple contracts/modules/tests/risks/migrations simultaneously. Current continuity also lacks one universal executable contract for causal history, fencing and ContextPack freshness.

## Constraints

- preserve current SQLite/HOTELS_MASTER/Operational Graph/Intelligence authority;
- do not interrupt CRM universe production;
- no second hidden authority;
- public GitHub cannot contain private operational data or credentials;
- current scale does not justify distributed infrastructure;
- migration must be reversible and evidence-backed;
- outbound remains independently closed.

## Alternatives

### A. Keep documents and domain tables only

Rejected because causal/ownership relationships remain implicit, agent collision remains procedural and zero-context graph queries are unreliable.

### B. Adopt Neo4j as new operational authority

Rejected because it duplicates constrained truth, creates migration/operations cost and solves no measured throughput bottleneck.

### C. Adopt Kafka/event-sourced microservices

Rejected because current event volume, team topology and recovery SLO do not justify distributed delivery semantics or operational burden.

### D. Use a generic property graph only

Rejected as the sole model because multi-party decisions and assurance relations become opaque intermediate nodes or prose. Binary projections remain available from the hypergraph.

### E. Typed temporal hypergraph + hash-chained event ledger over existing stores

Selected.

## Decision

Implement a standard-library Python kernel with:

- typed nodes, directed edges and role-bearing hyperedges;
- validity intervals, source event/commit, authority, confidence, provenance and supersession;
- append-only hash-chained causal events;
- first-class Session, Claim, Lease and monotonic FencingToken;
- deterministic ContextPack with ancestry/watermark/projection freshness checks;
- assurance and implementation compilers;
- COS L0–L19 projection registry;
- JSON/JSONL build artifacts and SHA-256 manifests;
- strangler migration and shadow parity before production adoption.

## Why selected

It closes the measured architecture defects while retaining the proven data plane. It is locally deterministic, cheap, testable, recoverable and reversible. It exposes a future storage interface without pre-buying distributed complexity.

## Tradeoffs

- JSONL requires explicit compaction/snapshot policy as history grows.
- Hypergraph queries initially use in-process projections rather than a specialized database.
- Legacy history may remain partially reconstructed with `HISTORICAL_UNKNOWN` nodes.
- Production qualification requires recovery and concurrency drills.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Ledger mistaken for domain authority | explicit authority ceiling and migration gate |
| Stale writer | lease expiry + monotonic fencing token |
| Graph drift | source watermark/digest and exact projection reconciliation |
| Context leak | recursive secret redaction + public-repo guard |
| Event corruption | canonical serialization + hash chain + replay verification |
| Overengineering | no external graph/event infrastructure without measured trigger |
| Repeated create mutation | idempotency key + mutation loop budget + permanent regression test |

## Reversibility

High at foundation stage: revert Git changes and discard generated projections. Medium after coordination cutover: close leases, restore prior projection revision and keep ledger events. Operational authority migration requires separate rollback-tested checkpoint.

## Trigger for reconsideration

Reconsider storage/transport only when measured event throughput, projection rebuild time, concurrent writer contention, data volume or provider fan-out breaches declared SLOs and cannot be solved with the existing primitives.

## Confidence

**HIGH_CONFIDENCE** for the architecture direction and authority boundaries.  
**MEDIUM_CONFIDENCE** for JSONL longevity and five-minute recovery target pending empirical drills.

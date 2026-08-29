# ADR-0001 — Typed Temporal Hypergraph over Existing Authority Stores

Status: **ACCEPTED FOR V2 FOUNDATION; PRODUCTION ADOPTION GATED**  
Date: 2026-08-30  
Owners: Principal Systems Architect, Data Architect, Reliability Architect

## Problem

The project has mature domain contracts and constrained state, but architecture, causation, sessions, claims, risks, tests and handoffs are distributed across code, documents, PRs, issues, Sheets and chat-derived summaries. Binary graphs alone also hide the multi-party impact of major decisions. The current system lacks one universal executable contract for causal history, fencing and ContextPack freshness.

## Constraints

- preserve current SQLite/HOTELS_MASTER/Operational Graph/Intelligence authority;
- do not interrupt CRM-universe production;
- create no second hidden authority;
- keep private operational data and credentials out of public GitHub;
- avoid distributed infrastructure without measured need;
- make migration reversible and evidence-backed;
- keep outbound independently closed.

## Alternatives

### A. Keep documents and domain tables only

Rejected: causation and ownership remain implicit; agent collision remains procedural; zero-context queries are unreliable.

### B. Adopt Neo4j as new operational authority

Rejected: duplicates constrained truth, adds migration/operations cost and solves no measured throughput bottleneck.

### C. Adopt Kafka/event-sourced microservices

Rejected: current event volume, team topology and recovery SLO do not justify distributed delivery semantics and operational burden.

### D. Generic property graph only

Rejected as the sole model: multi-party decisions and assurance relations become opaque intermediate nodes or prose. Binary projections remain derivable from the hypergraph.

### E. Typed temporal hypergraph + hash-chained event ledger over existing stores

Selected.

## Decision

Implement a standard-library Python kernel with:

- typed nodes, directed edges and role-bearing hyperedges;
- temporal validity, source event/commit, authority, confidence, provenance and supersession;
- append-only hash-chained causal events;
- first-class Session, Claim, Lease and monotonic FencingToken;
- deterministic ContextPack with ancestry/watermark/projection freshness checks;
- assurance and implementation compilers;
- COS L0–L19 projection registry;
- JSON/JSONL build artifacts and SHA-256 manifests;
- strangler migration and shadow parity before production adoption.

## Why selected

It closes measured architecture defects while retaining the proven data plane. It is deterministic, inexpensive, testable, recoverable and reversible. It leaves storage/transport replaceable without pre-buying distributed complexity.

## Tradeoffs

- JSONL needs a future snapshot/compaction policy if history grows materially.
- Hypergraph queries initially use in-process projections rather than a specialized database.
- Legacy history may remain partially reconstructed through explicit `HISTORICAL_UNKNOWN` nodes.
- Production qualification requires physical recovery and concurrency drills.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Ledger mistaken for domain authority | authority ceiling and independent migration gate |
| Stale writer | lease expiry + monotonic fencing token |
| Graph drift | source watermark/digest and exact reconciliation |
| Context secret leakage | recursive redaction + public-repository guard |
| Event corruption | canonical serialization + hash-chain verification |
| Overengineering | measured trigger before specialized infrastructure |
| Repeated create mutation | idempotency key + mutation-loop budget + regression test |

## Reversibility

High at foundation stage: revert Git changes and discard generated projections. Medium after coordination cutover: close leases, restore the prior projection revision and retain ledger history. Operational authority migration requires a separately rollback-tested checkpoint.

## Reconsideration triggers

Reconsider storage/transport only when measured event throughput, projection rebuild time, concurrent-writer contention, data volume or provider fan-out breaches a declared SLO and cannot be solved with current primitives.

## Confidence

- **HIGH_CONFIDENCE:** architecture direction and authority boundaries.
- **MEDIUM_CONFIDENCE:** JSONL longevity and five-minute recovery target pending empirical drills.

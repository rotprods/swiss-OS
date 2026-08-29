# SWITZERLAND_JOB_OS — GRAPH REFACTOR V2

Status: **V2 FOUNDATION IMPLEMENTED — MIGRATION GATED**  
Authority: architecture and executable-kernel contract; operational authority remains in the current constrained/control-plane lineage until a separately validated migration wave.  
Owner: Mission Commander + Principal Systems Architecture  
Last updated: 2026-08-30  
Supersedes: competing future-architecture proposals, not historical operational truth

## Executive V2

SWITZERLAND_JOB_OS V2 is a typed temporal hypergraph projected from an append-only causal event ledger. Existing SQLite, HOTELS_MASTER, Operational Graph, Intelligence, GitHub, Drive and Library remain the persistence primitives. V2 adds the missing coordination and assurance kernel without creating a second operational database.

```text
North Star / Goals / Checkpoints
                │
                ▼
        Commands + Sessions
                │
        Claims / Leases / Fencing
                │
                ▼
    Append-only causal Event Ledger
                │
                ▼
        Canonical Temporal Hypergraph
          ┌─────┼─────┬────────┐
          ▼     ▼     ▼        ▼
       State   Tasks  Evidence  ContextPack
          │     │     │        │
          └─────┴─────┴────────┘
                │
                ▼
 SQLite / Sheets / Operational Graph / Intelligence
                │
                ▼
     Invariants / CI / Recovery / Handoffs
```

## Hard boundaries

- The event ledger records causation and history; it does not silently become hotel authority.
- The hypergraph is a semantic model and deterministic projection contract; operational entity truth remains constrained and PK-keyed.
- ContextPack is a digested cache with freshness checks, never authority.
- Session, Claim, Lease and FencingToken are first-class coordination entities.
- Every authority mutation remains governed by MEP → WOP → domain contracts → PRG.
- This refactor allocates no H-ID, changes no hotel/source mapping and opens no outbound.
- `OUTBOUND = CLOSED`; `send_allowed = 0`.

## Canonical V2 surfaces

- Architecture: `docs/architecture/HYPERGRAPH_ARCHITECTURE_V2.md`
- Ontology/lexicon: `docs/architecture/LEXICON_V2.md`
- Implementation program: `docs/operations/GRAPH_REFACTOR_V2_IMPLEMENTATION_PROGRAM.md`
- Adversarial gauntlet: `docs/audits/GRAPH_REFACTOR_V2_GAUNTLET.md`
- Decision record: `docs/decisions/ADR-0001-HYPERGRAPH-KERNEL.md`
- Executable kernel: `src/swiss_os/v2_kernel.py`
- Mutation loop guard: `src/swiss_os/v2_loop_guard.py`
- Deterministic compiler: `scripts/compile_graph_v2.py`
- Machine seed: `docs/graph/v2/canonical_seed.json`
- CI artifact: `graph-refactor-v2-<exact-sha>`

## V1 → V2 delta

| Current capability | V2 treatment | Reason |
|---|---|---|
| Constrained DB / HOTELS_MASTER | KEEP | proven authority/data-plane primitives |
| Operational Graph / Intelligence | KEEP + reconcile | domain projections remain valuable |
| MEP/WOP/PRG and domain contracts | KEEP + bridge | strong execution/governance kernel |
| STATE/NEXT | REFINE into ContextPack inputs | prevent stale conversational recovery |
| Wave/run logs | REFACTOR into causal events | make causation/replay queryable |
| Agent ownership | REFACTOR into Session/Claim/Lease/Fence | prevent collisions and stale writers |
| Graph JSONs | REFINE into temporal typed projections | shared IDs, provenance, validity and digest |
| Architecture QA | REFACTOR into assurance compiler | named tests/evidence instead of prose confidence |
| Kafka/Neo4j/Redis/Kubernetes | DEFER | no measured trigger; would add failure modes |
| Chat memory as continuity | DEPRECATE | cannot survive context loss or agent death |

## Migration posture

V2 uses a strangler migration:

1. merge and verify the architecture foundation;
2. shadow-compile current authoritative state;
3. execute zero-context recovery and agent-death drills;
4. execute concurrency/security gauntlets;
5. compare V1/V2 projections and exact PK/digest sets;
6. introduce V2 coordination for new bounded waves;
7. backfill historical events with explicit `HISTORICAL_UNKNOWN` where evidence is absent;
8. promote only through CP0–CP14 and a rollback-tested authority transition.

No big-bang rewrite is authorized.

## Current Definition of Done

The foundation is acceptable only when CI proves:

```text
all V2 tests PASS
exact SHA-bound test attestation
valid graph with no hard dependency cycles
20 explicit COS projections
critical owner/test gaps = 0
invariant failures = 0
open P0/P1 foundation gaps = 0
operational_authority_mutated = false
h_id_allocations = 0
outbound_opened = false
send_allowed = 0
```

This does not declare `V2_FINAL` or production authority. CP7–CP14 remain objectively gated in the implementation program.

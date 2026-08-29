# SWITZERLAND_JOB_OS — GRAPH REFACTOR V2

Status: **V2 FOUNDATION — IMPLEMENTED, MIGRATION GATED**  
Authority: architecture and executable-kernel contract; operational authority remains in the current constrained/control-plane lineage until a separately validated migration wave.  
Owner: Principal Systems Architecture / Mission Commander  
Source revision: bound by Git parent and CI runtime  
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
- The canonical hypergraph is a semantic model and deterministic projection contract; operational entity truth remains constrained and PK-keyed.
- A ContextPack is a signed/digested cache with freshness checks, never authority.
- A Session, Claim, Lease and FencingToken are first-class coordination entities.
- Every authority mutation remains governed by MEP → WOP → domain contracts → PRG.
- `CRM_UNIVERSE_COMPLETE`, H-ID allocation and outbound are unchanged by this refactor.
- `OUTBOUND = CLOSED`; `send_allowed = 0`.

## Canonical V2 surfaces

- Architecture: `docs/architecture/HYPERGRAPH_ARCHITECTURE_V2.md`
- Ontology and lexicon: `docs/architecture/LEXICON_V2.md`
- Implementation program: `docs/operations/GRAPH_REFACTOR_V2_IMPLEMENTATION_PROGRAM.md`
- Adversarial gauntlet: `docs/audits/GRAPH_REFACTOR_V2_GAUNTLET.md`
- Decision record: `docs/decisions/ADR-0001-HYPERGRAPH-KERNEL.md`
- Executable kernel: `src/swiss_os/v2_kernel.py`
- Compiler: `scripts/compile_graph_v2.py`
- Machine inputs: `docs/graph/v2/`, `docs/state/v2/`, `docs/events/v2/`

## Migration posture

V2 is introduced by strangler migration:

1. shadow-compile graph/events/context from existing authoritative state;
2. prove deterministic replay and zero-context recovery;
3. run agent-death and concurrency drills;
4. compare V1 and V2 projections;
5. activate V2 coordination gates for new waves;
6. migrate historical state with explicit `SUPERSEDED` lineage;
7. promote only after CP0–CP14 acceptance.

No big-bang rewrite is authorized.

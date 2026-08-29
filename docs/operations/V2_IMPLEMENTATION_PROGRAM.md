# V2 IMPLEMENTATION PROGRAM

**Program:** COS 20D Hypergraph V2  
**Machine source:** `docs/state/v2/tasks.json`  
**North Star:** G-0001 remains unchanged.

## Phase topology

```text
P0 Reconstruction
 ├─ P1 Graph/Ontology
 ├─ P2 Historical Regression
 └─ P3 Gap Analysis
        ↓
P4 Architecture Freeze
        ↓
P5 Contract Kernel
 ├─ P6 Event/State
 ├─ P7 Agent/Session/Claims
 ├─ P8 Context/Memory
 ├─ P9 Documentation
 ├─ P10 Assurance
 ├─ P11 Recovery
 └─ P12 Security
        ↓
P14 Migration
        ↓
P16 Final Gauntlet
        ↓
P17 Production coordination authority
```

No hotel authority promotion is part of this program.

## Checkpoints

CP0 live truth; CP1 graph; CP2 history; CP3 gaps; CP4 V2 architecture; CP5 contracts; CP6 kernel; CP7 recovery; CP8 death drill; CP9 concurrency; CP10 security; CP11 product path; CP12 empirical qualification; CP13 migration; CP14 production authority.

`docs/state/v2/checkpoint.json` is the machine checkpoint projection.

## Program Definition of Done

V2 program is DONE only when:

- architecture and authority hierarchy are coherent;
- critical graph entities/edges are queryable;
- Session/Event/Claim/ContextPack contracts are implemented;
- tests actually executed and passed;
- duplicate/stale/concurrency/replay failure families are covered;
- security implications reviewed;
- projection recovery and zero-context death drill pass;
- documentation/root pointers updated;
- machine state/graph/task/checkpoint/context pack persisted;
- main ancestry reconciled after CI;
- no unresolved P0/P1 V2 regression remains;
- handoff succeeds without chat context.

## Parallelization

Safe parallel lanes after CP4:

1. **Kernel lane:** Session/Event/Claim/ContextPack implementation/tests.
2. **Graph/docs lane:** ontology, lexicon, graph projection docs.
3. **Security/recovery lane:** threat/recovery/death drills.
4. **Domain lane:** current provider-identity/reverse-gap work can continue because V2 claims exclude hotel authority and domain mapping files.

Conflict rule: two lanes may share semantic scope only when their file/resource scopes are disjoint or explicitly shared. All writers re-read main before merge.

## Exact executable frontier

Current safe frontier:

- finish V2 files and CI guard on the isolated branch;
- run repository CI;
- adversarially inspect diff for accidental authority/domain mutation;
- reread live main/open PRs;
- rebase/recompile machine pointers if main moved;
- merge V2 only after green CI;
- then migrate active workstreams incrementally to V2 claims/events.

See `tasks.json` for per-task inputs/outputs/dependencies/tests/evidence/rollback/DoD.

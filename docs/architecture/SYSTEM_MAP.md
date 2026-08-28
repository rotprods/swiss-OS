# SYSTEM MAP — SWITZERLAND_JOB_OS

Status: **STABLE ARCHITECTURE MAP**

Mutable counts, active tasks, current epochs and operational parent versions do not live in this document. Read `STATE.md` and reconcile against the live authority plane for current state.

```text
                         ┌───────────────────────┐
                         │        G-0001         │
                         │ verified viable offer │
                         └───────────┬───────────┘
                                     │
                         META EXECUTION PROTOCOL
                              MEP-2.0 / COLETTE
                                     │
                  ┌──────────────────┼──────────────────┐
                  │                  │                  │
                  ▼                  ▼                  ▼
              Ancestry         Capability Matrix   Bottleneck / P0
            Reconstruction       + Fallbacks       / SLO / TTL scan
                  │                  │                  │
                  └──────────────────┼──────────────────┘
                                     ▼
                             Mission Commander
                                     │
                         Authority / Reconciliation
                                     │
                              WAVE TRANSACTION
                                     │
       ┌─────────────────────────────┼─────────────────────────────┐
       │                             │                             │
       ▼                             ▼                             ▼
Canonical Market              Candidate Truth               Intelligence OS
Discovery/Evidence            Lane Assets                   Domain Research
Entity Resolution             Templates                     Vacancy/Housing
Aliases/Groups                Claim QA                      People/Channels
       │                             │                       Digital/Tech/etc.
       └──────────────────────┬──────┴───────────────┬─────────────┘
                              │                      │
                              ▼                      ▼
                         Scheduler / TTL       Scoring / Priority
                              │                      │
                              └──────────┬───────────┘
                                         ▼
                                 Stage / Canary
                                         │
                                         ▼
                              Constrained SQLite
                                         │
                      ┌──────────────────┼──────────────────┐
                      │                  │                  │
                      ▼                  ▼                  ▼
                Drive / Sheets      Intelligence      Operational Graph
                control mirror      PK packages       PK-keyed relations
                      │                  │                  │
                      └──────────────────┼──────────────────┘
                                         ▼
                              QA / Governance / SLO
                                         │
                                         ▼
                                Observability Engine
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 │                       │                       │
                 ▼                       ▼                       ▼
              GitHub              Project Meta Graph      Recovery / Library
        code/contracts/CI       goals/waves/artifacts      cold persistence
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         ▼
                                 MEP LEARN / NEXT ROUTE
                                         │
                                         └──────→ next COLETTE cycle
```

## Meta execution scope

MEP-2.0 is a cross-engine routing/control contract, not a separate operational authority database and not a new daemon.

It selects the next safe productive route after reconstructing Git ancestry, operational authority, capabilities and the current bottleneck.

A recoverable capability outage triggers an alternative safe route when one exists. Examples include structured source acquisition, source-scope reconciliation, mass staging, exact-current refresh, engineering QA and recovery persistence.

MEP never lowers WOP/CUP/SSR/PRG/privacy/outbound gates.

## Two graph scopes

### Operational Graph

Represents operational relationships among canonical hotels/entities, aliases/groups, evidence, vacancies, housing, people, channels, tasks, applications and outcomes.

It is PK-keyed constrained operational state. Authoritative operational mutations synchronize it in the same wave.

### Project Memory Meta Graph

Represents goals, checkpoints, releases, waves, meta-cycles, protocols, capability blockers, decisions, architecture and artifact lineage.

It is project memory and must never be mistaken for the complete operational hotel graph.

Material MEP routing/protocol/blocker decisions belong to this scope.

## Persistence planes

```text
GitHub          = source of versioning / executable contracts
Drive / Sheets  = human control plane + operational mirror
SQLite          = constrained operational state backend
OperationalGraph= PK-keyed operational relationships
Meta Graph      = project/release/wave/meta-cycle/decision memory
Library         = recovery / cold persistence
Local workspace = execution cache, not shared authority
```

Create-only Drive persistence is not equivalent to native in-place Sheets mutation. Capability semantics must be explicit.

## Meta-cycle path

```text
COLLECT authority + Git ancestry + capabilities
→ OBSERVE drift / blockers / scheduler / SLO / TTL
→ LOCATE highest-value safe bottleneck
→ SELECT MEP ROUTE
→ EXECUTE WOP WAVE
→ TEST / GAUNTLET / ADVERSARIAL QA
→ TRANSACT + PERSIST every affected available durable plane
→ FINAL RECONCILIATION
→ EVOLVE state / next route
```

## Promotion path

Every canonical material mutation still follows the Wave Operating Protocol:

```text
AUTHORITY BOOTSTRAP
→ SCHEDULER / SCOPE
→ DISCOVER / VERIFY
→ NORMALIZE / RESOLVE
→ STAGE / CANARY
→ VALIDATE
→ DB COMMIT
→ SHEETS PK MIRROR
→ INTELLIGENCE
→ OPERATIONAL GRAPH
→ QA / INVARIANTS / SLO
→ METRICS / HEALTH / SCHEDULER / TRANSITIONS
→ GITHUB HANDOFF
→ RECOVERY PERSISTENCE
→ FINAL RECONCILIATION
→ WAVE CLOSE
```

If a required authority plane is unavailable, the wave switches to `DEGRADED_CANARY` or `RECOVERY_RECONCILE`; canonical authority cannot advance. MEP then selects another safe route if one can still reduce the bottleneck.
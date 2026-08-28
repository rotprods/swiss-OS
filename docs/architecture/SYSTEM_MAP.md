# SYSTEM MAP — SWITZERLAND_JOB_OS

Status: **STABLE ARCHITECTURE MAP**

Mutable counts, active tasks, current epochs and operational parent versions do not live in this document. Read `STATE.md` and reconcile against the live authority plane for current state.

```text
                         ┌───────────────────────┐
                         │        G-0001         │
                         │ verified viable offer │
                         └───────────┬───────────┘
                                     │
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
```

## Two graph scopes

### Operational Graph

Represents operational relationships among canonical hotels/entities, aliases/groups, evidence, vacancies, housing, people, channels, tasks, applications and outcomes.

It is PK-keyed constrained operational state. Authoritative operational mutations synchronize it in the same wave.

### Project Memory Meta Graph

Represents goals, checkpoints, releases, waves, decisions, architecture and artifact lineage.

It is project memory and must never be mistaken for the complete operational hotel graph.

## Persistence planes

```text
GitHub          = source of versioning / executable contracts
Drive / Sheets  = human control plane + operational mirror
SQLite          = constrained operational state backend
OperationalGraph= PK-keyed operational relationships
Meta Graph      = project/release/wave/decision memory
Library         = recovery / cold persistence
Local workspace = execution cache, not shared authority
```

## Promotion path

Every canonical material mutation follows the Wave Operating Protocol:

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

If a required authority plane is unavailable, the wave switches to `DEGRADED_CANARY`; canonical authority cannot advance.
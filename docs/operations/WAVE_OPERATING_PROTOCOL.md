# WAVE OPERATING PROTOCOL — SWITZERLAND_JOB_OS

Version: **WOP-1.0**  
Status: **CANONICAL OPERATING CONTRACT**

## 1. Purpose

A **WAVE** is the smallest bounded unit of material execution in SWITZERLAND_JOB_OS.

Any operation that can mutate canonical data, constrained DB state, Sheets/control-plane state, Graph/Intelligence, GitHub system memory, checkpoint state, scheduler state or recovery artifacts MUST execute inside a named wave.

A wave is not a chat turn. It is a transaction-like execution envelope with explicit authority, scope, gates and closure semantics.

The North Star remains G-0001: secure a truthful, legal, economically viable Swiss job offer that Roberto accepts and can sustainably relocate for.

## 2. Wave identity

Every material wave MUST declare or derive:

```text
wave_id
run_id
goal_id
checkpoint_id
task_id(s)
authority_epoch
parent_manifest
scope
batch_limit
execution_mode
started_at
owner/agent
```

Recommended IDs:

```text
WAVE-YYYYMMDD-<checkpoint>-<sequence>
RUN-YYYYMMDD-HHMM-<slug>
```

No anonymous material mutation is permitted.

## 3. Canonical command semantics

Agents may interpret these conversational commands:

```text
/wave
/wave status
/wave recover
/wave close
/wave goal=<id> checkpoint=<id> task=<id> batch=<n>
```

`/wave` with no parameters means:

1. reconstruct authority;
2. read scheduler/issues/SLO/TTL state;
3. select the highest-value unblocked canonical task;
4. execute one bounded wave;
5. reconcile every required persistence layer before claiming authority.

`/wave recover` ALWAYS runs reconciliation before new discovery or allocation.

## 4. Authority model

Only an **authority-eligible fully synchronized commit** can advance canonical state.

```text
LAST FULLY SYNCHRONIZED CONSTRAINED COMMIT
  = constrained DB validated
  + Sheets/control plane reconciled
  + Graph/Intelligence reconciled where affected
  + metrics/checkpoints/scheduler/transitions updated
  + persistent handoff emitted
```

A local SQLite file may be physically valid and still be **NON-AUTHORITATIVE** if the synchronization chain is incomplete.

Within authority-eligible artifacts, precedence remains:

```text
PHYSICAL + CONSTRAINED DATA
> LIVE CONTROL PLANE
> VALIDATED MANIFEST
> GITHUB STATE POINTER
> HISTORICAL PROSE
```

Local canaries are explicitly excluded from the first line until promoted.

## 5. Storage responsibility matrix

### GitHub — version control / executable system memory

Stores:

- code;
- schemas;
- migrations;
- tests;
- CI;
- architecture contracts;
- operating protocol;
- public-safe run/state handoffs;
- public-safe intelligence summaries.

Does NOT store:

- operational SQLite payloads;
- PII;
- raw contacts;
- candidate-private assets;
- sensitive raw evidence;
- credentials.

GitHub is the source of versioning, not the operational database.

### Drive / Sheets — human control plane + operational mirror

Stores/mirrors:

- GOAL_STATE;
- CHECKPOINT_REGISTRY;
- scheduler;
- issues;
- metrics/health/SLO;
- run log/transitions;
- hotel/entity control-plane tables;
- human-reviewable Graph/Intelligence projections;
- persistent project documents.

Writes MUST be by canonical PK/key resolution, never blind row offsets.

### SQLite constrained backend

Stores operational constrained state and enforces PK/FK/UNIQUE/CHECK/idempotency semantics.

It is the constrained state backend, but a new local DB version becomes authoritative only after the full synchronization gate passes.

### Operational Graph

Operational graph truth belongs in constrained PK-keyed data structures/tables.

Entity/evidence/task mutations update the operational graph in the same wave before authority promotion.

### Project Memory Meta Graph

Tracks goals, checkpoints, releases, waves, decisions, artifacts, architecture and lineage.

`graph_registry.json` or equivalent is a project-memory graph/pointer, not the entire hotel operational graph.

### ChatGPT Library — recovery / cold persistence

Library is a durable recovery surface, NOT operational truth.

Every material DB/schema/recovery wave SHOULD persist:

```text
WAVE_<id>_RECOVERY_BUNDLE.zip
manifest.json
state_digest.json
```

Research-only waves may persist a compact handoff instead of a full SQLite bundle.

### Local execution workspace / Git local

Local execution state is a cache/workspace, never authority by itself.

In ChatGPT sandbox, local filesystem and Git CLI persistence/network access are not guaranteed. GitHub connector operations are therefore the canonical VCS actuator in this environment.

When executing from Roberto's persistent Mac/Codex environment, a normal local clone may be used, but remote GitHub remains the shared version-control authority.

## 6. Execution modes

A wave MUST operate in one of four explicit modes.

### A. AUTHORITATIVE_WRITE

Required planes are available and preflight passes.

May perform canonical promotion.

### B. READ_ONLY_RESEARCH

No canonical mutation intended.

May collect evidence/intelligence and stage future work.

### C. DEGRADED_CANARY

One or more required authority planes are unavailable.

Permitted:

- research;
- staging;
- local constrained canary;
- QA;
- restore/replay testing;
- GitHub public-safe engineering;
- Library recovery persistence.

Forbidden:

- claiming new canonical count;
- allocating IDs as reserved;
- checkpoint promotion;
- pretending Graph/Sheets are synchronized;
- outbound.

Closure state MUST be `SAFE_STOP_CANARY`.

### D. RECOVERY_RECONCILE

Mandatory after any outage, ambiguous partial write, concurrent-agent uncertainty or stale handoff.

No new canonical discovery allocation until live authority is reconstructed and provisional work is anti-joined.

## 7. Mandatory wave lifecycle

```text
0  WAVE OPEN
1  AUTHORITY BOOTSTRAP
2  DRIFT / ISSUE / SLO / TTL SCAN
3  SCHEDULER SELECTION
4  DISCOVER / VERIFY
5  NORMALIZE
6  DEDUPE / ALIAS / GROUP RESOLUTION
7  STAGE
8  CANARY
9  VALIDATE
10 COMMIT CONSTRAINED DB
11 MIRROR SHEETS BY PK
12 SYNC INTELLIGENCE
13 SYNC OPERATIONAL GRAPH
14 UPDATE ENTITY/SNAPSHOT EPOCH
15 RUN QA + INVARIANTS + SLO
16 UPDATE METRICS / HEALTH
17 UPDATE SCHEDULER / ISSUES
18 EMIT STATE TRANSITIONS / RUN LOG
19 UPDATE GOAL / CHECKPOINT IF WARRANTED
20 UPDATE GITHUB STATE/HANDOFF
21 PERSIST LIBRARY RECOVERY ARTIFACTS
22 FINAL RECONCILIATION
23 WAVE CLOSE
```

Steps 10–23 are one logical promotion chain. If a required step fails, authority does not advance.

## 8. Bootstrap contract

Before material execution, reconstruct at minimum:

```text
release
active_goal_id
active_checkpoint_id
authority_epoch
latest authority-eligible DB manifest
physical row count
active canonical count
alias/superseded count
DB integrity
FK violations
snapshot state/drift
Graph active denominator
Intelligence active denominator
open P0 issues
active scheduler tasks
stale send-critical facts
send_allowed count
outbound state
GitHub STATE pointer
Library latest recovery pointer
```

Never trust counts copied from the prompt without reconciliation.

## 9. Write protocol

Canonical entity writes use:

```text
DISCOVER
→ NORMALIZE
→ DEDUPE
→ RECONCILE
→ STAGE
→ CANARY
→ VALIDATE
→ DB COMMIT
→ SHEETS PK MIRROR
→ GRAPH / INTELLIGENCE SYNC
→ INVARIANTS
→ OBSERVABILITY
→ PERSISTENCE
```

Never:

```text
discover → append rows → declare success
```

All IDs are immutable. Superseded IDs remain lineage and map explicitly to canonical targets.

## 10. Required gauntlet for canonical promotion

Applicable tests MUST include:

```text
SQLite integrity_check = ok
FK violations = 0
canonical IDs valid
unexplained ID gaps = 0
active name+city duplicate conflicts = 0
active non-empty domain duplicates = 0
alias targets valid
active duplicate QA states = 0
metric active-key duplicates = 0
snapshot drift = 0
DB ↔ Sheets PK reconciliation exact
Graph active denominator = canonical active count
Intelligence active denominator = canonical active count
stale send-critical facts without refresh task = 0
invalid UNKNOWN_AFTER_SEARCH = 0 for new V3 data
score-scale violations = 0
idempotency replay creates 0 unintended rows
restore logical differences = 0
send_allowed = 0 unless a separately authorized outbound gate exists
release/checkpoint/control-plane agreement = PASS
```

SQLite restore equivalence is logical, not binary-file SHA equality.

## 11. Graph synchronization contract

Every wave classifies graph impact:

```text
GRAPH_IMPACT = NONE | META | OPERATIONAL | BOTH
```

META updates are required when changing:

- goal;
- checkpoint;
- release;
- decision;
- wave/run;
- architecture;
- artifact lineage.

OPERATIONAL updates are required when changing:

- hotel/entity;
- alias/group;
- evidence/claim;
- vacancy;
- person/channel;
- housing;
- task;
- application/outcome.

No authoritative entity write may leave its operational graph node/edges behind.

## 12. Agent synchronization contract

`AGENTS.md` contains **stable operating rules and role contracts only**.

It MUST NOT hardcode mutable frontier counts/tasks because that creates stale-agent drift.

Mutable state lives in:

```text
live Drive/Sheets control plane
latest authority-eligible manifest
STATE.md pointer
```

Agents MUST read `WAVE_OPERATING_PROTOCOL.md` + `GOAL.md` + `STATE.md` before material work and then reconcile against the live authority plane.

## 13. Git protocol

Architecture/code/schema/protocol changes use:

```text
issue when materially useful
→ branch
→ implementation
→ tests
→ PR
→ CI
→ review/diff check
→ merge
→ operational adoption/reconciliation
```

One wave may create several commits but SHOULD create one coherent PR per architectural concern.

Data-only operational waves do not require committing private operational data to GitHub; update public-safe `STATE.md`/state docs after full authority synchronization.

CI success proves repository contracts/tests, not that Drive/DB runtime state is synchronized.

## 14. Library protocol

For every material wave with DB/schema/recovery impact:

1. generate recovery bundle;
2. generate manifest with SHA-256 and authority/canary status;
3. upload to `/SWITZERLAND_JOB_OS/`;
4. update `LATEST_RECOVERY.json` or equivalent pointer;
5. never label a canary bundle as authoritative.

Library failure does not invalidate a fully synchronized operational commit, but it creates a persistence issue that must be recorded and repaired.

## 15. Degraded/outage protocol

If Drive/Sheets, DB parent, GitHub or another required plane fails:

```text
DETECT
→ STOP AUTHORITY PROMOTION
→ REGISTER BLOCKED LAYER
→ CONTINUE ONLY SAFE RESEARCH/CANARY WORK
→ PERSIST PUBLIC-SAFE GITHUB HANDOFF
→ PERSIST LIBRARY RECOVERY BUNDLE
→ CLOSE SAFE_STOP_CANARY
```

When the layer returns:

```text
/wave recover
→ read live authority
→ compare provisional candidates
→ anti-join IDs/names/cities/domains/aliases/tasks
→ reallocate provisional IDs if frontier moved
→ rerun canary from the live parent
→ only then execute AUTHORITATIVE_WRITE
```

No provisional local ID is a reservation.

## 16. Concurrency protocol

Before any canonical commit:

- re-read the live frontier;
- anti-join active canonical entities;
- anti-join aliases/superseded IDs;
- anti-join domains;
- anti-join active scheduler task keys;
- confirm parent manifest/epoch has not changed.

If the parent moved, the wave re-enters `RECOVERY_RECONCILE` rather than force-writing stale assumptions.

## 17. Observability emitted by every material wave

At minimum:

```text
wave_id
run_id
goal_id
checkpoint_id
execution_mode
authority_parent
authority_epoch
canonical_before
canonical_after_authoritative
canary_candidate_count
physical_before
physical_after_authoritative
tasks_attempted
tasks_completed
tasks_failed
issues_opened
issues_resolved
SLO breaches
DB integrity
FK violations
duplicate count
snapshot drift
stale critical count
send_allowed count
Graph denominator
Intelligence denominator
quality result
closure_state
next bottleneck
```

Never report a canary count in `canonical_after_authoritative`.

## 18. Wave closure states

Every material wave closes as exactly one:

```text
COMPLETE_AUTHORITY
COMPLETE_READ_ONLY
SAFE_STOP_CANARY
BLOCKED_P0
SUPERSEDED
```

`COMPLETE_AUTHORITY` requires all required persistence and reconciliation gates.

## 19. Real-time meaning

SWITZERLAND_JOB_OS does **not** claim a background daemon unless one is actually configured.

"Real-time synchronization" means:

> before a material wave is allowed to return an authoritative promotion, every affected required layer is synchronously reconciled within that wave.

Temporary staging/canary divergence is allowed. Silent post-wave divergence is not.

## 20. Outbound lock

No wave may perform email, portal submission, DM, WhatsApp or follow-up unless the completely separate outbound authorization stack passes.

Default remains:

```text
OUTBOUND = CLOSED
send_allowed = 0
```

Research and market mapping are never implicit authorization to contact employers.

## 21. Current implementation rule

Until Drive/Sheets write capability is available again, SWITZERLAND_JOB_OS runs in `DEGRADED_CANARY` or `READ_ONLY_RESEARCH` for work that depends on those layers.

The current V16 candidate state is acceleration/recovery material only. The last fully synchronized authority remains the value declared by `STATE.md` and the live control plane when available.

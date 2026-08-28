# WAVE OPERATING PROTOCOL — SWITZERLAND_JOB_OS

Version: **WOP-1.1**  
Status: **CANONICAL OPERATING CONTRACT**

## 1. Definition

A **WAVE** is the smallest bounded unit of material execution.

Any operation that can mutate canonical data, constrained DB state, Drive/Sheets, Graph/Intelligence, scheduler/checkpoints, GitHub system memory or recovery artifacts MUST execute inside a named wave.

A wave is not a chat turn. It is a transaction-like envelope with explicit authority, scope, gates and closure.

## 2. Wave header

Every material wave declares or derives:

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
graph_impact
```

Recommended IDs:

```text
WAVE-YYYYMMDD-<checkpoint>-<sequence>
RUN-YYYYMMDD-HHMM-<slug>
```

No anonymous material mutation is permitted.

## 3. Command semantics

```text
/wave
/wave status
/wave recover
/wave close
/wave goal=<id> checkpoint=<id> task=<id> batch=<n>
```

`/wave` with no parameters means:

1. reconstruct authority;
2. scan drift/issues/SLO/TTL;
3. select the highest-value unblocked scheduler task;
4. execute one bounded wave;
5. reconcile all required persistence layers before claiming authority.

`/wave recover` always reconciles before new discovery/allocation.

## 4. Authority

Only the **last fully synchronized authority-eligible constrained commit** may advance canonical state.

A local SQLite file may be physically valid and still be **NON-AUTHORITATIVE**.

Authority eligibility requires, where affected:

```text
constrained DB validated
+ Drive/Sheets reconciled
+ Graph/Intelligence reconciled
+ metrics/health/SLO updated
+ scheduler/issues/checkpoints updated
+ transitions/run log emitted
+ persistent handoff emitted
```

Within authority-eligible artifacts:

```text
PHYSICAL + CONSTRAINED DATA
> LIVE CONTROL PLANE
> VALIDATED MANIFEST
> GITHUB STATE POINTER
> HISTORICAL PROSE
```

Local canaries are excluded from authority until promotion completes.

## 5. Storage roles

### GitHub

Version-control and executable-contract plane:

- code;
- schemas/migrations;
- tests/CI;
- architecture/operating contracts;
- public-safe state/handoffs;
- public-safe intelligence summaries.

Never store operational SQLite, credentials, raw contacts, candidate-private assets, PII or sensitive raw evidence in the public repo.

### Drive / Sheets

Human control plane + operational mirror:

- GOAL_STATE / CHECKPOINT_REGISTRY;
- scheduler;
- issues;
- metrics/health/SLO;
- RUN_LOG / STATE_TRANSITIONS;
- entity/control-plane tables;
- Graph/Intelligence human mirrors;
- persistent project documents.

Authoritative writes resolve canonical keys/PKs. Blind positional row writes are prohibited.

### SQLite constrained backend

Operational state backend enforcing PK/FK/UNIQUE/CHECK/idempotency semantics.

A new local DB version is authority only after the synchronization gate passes.

### Operational Graph

PK-keyed operational truth for hotels, aliases/groups, evidence, vacancies, people/channels, housing, tasks, applications and outcomes.

### Project Memory Meta Graph

Goals, checkpoints, releases, waves, decisions, artifacts and architecture.

`graph_registry.json` or equivalent is meta/project memory, not the entire operational graph.

### ChatGPT Library

Durable recovery/cold-persistence surface, not operational truth.

Material DB/schema/recovery waves should persist:

```text
WAVE_<id>_RECOVERY_BUNDLE.zip
manifest.json
state_digest.json
```

### Local execution workspace / Git local

Execution cache only.

In the ChatGPT sandbox, filesystem persistence and Git CLI network access are not guaranteed; GitHub connector operations are the VCS actuator.

In a persistent Mac/Codex environment, a normal local clone may be used, but remote GitHub remains the shared VCS authority.

## 6. Execution modes

### AUTHORITATIVE_WRITE

All required planes available; preflight passes; canonical promotion allowed.

### READ_ONLY_RESEARCH

Evidence/research/staging only; no canonical mutation intended.

### DEGRADED_CANARY

One or more required authority planes unavailable.

Allowed:

- research;
- staging;
- local constrained canary;
- QA/restore/replay;
- GitHub public-safe engineering;
- Library recovery persistence.

Forbidden:

- canonical-count promotion;
- reserved-ID claims;
- checkpoint promotion;
- claiming Graph/Sheets synchronization;
- outbound.

Closes `SAFE_STOP_CANARY`.

### RECOVERY_RECONCILE

Mandatory after outage, partial write, stale parent, concurrent-agent uncertainty or ambiguous lineage.

No new canonical allocation until live authority is reconstructed and provisional work is anti-joined.

## 7. Mandatory lifecycle

```text
WAVE OPEN
→ AUTHORITY BOOTSTRAP
→ DRIFT / ISSUE / SLO / TTL SCAN
→ SCHEDULER SELECTION
→ DISCOVER / VERIFY
→ NORMALIZE
→ DEDUPE / ALIAS / GROUP RESOLUTION
→ STAGE
→ CANARY
→ VALIDATE
→ COMMIT CONSTRAINED DB
→ MIRROR SHEETS BY PK
→ SYNC INTELLIGENCE
→ SYNC OPERATIONAL GRAPH
→ UPDATE ENTITY/SNAPSHOT EPOCH
→ QA + INVARIANTS + SLO
→ METRICS / HEALTH
→ SCHEDULER / ISSUES
→ STATE TRANSITIONS / RUN LOG
→ GOAL / CHECKPOINT IF WARRANTED
→ GITHUB STATE/HANDOFF
→ LIBRARY RECOVERY
→ FINAL RECONCILIATION
→ WAVE CLOSE
```

From DB COMMIT onward, the chain is one logical promotion transaction. If a required step fails, authority does not advance.

## 8. Bootstrap minimum

Reconstruct:

```text
release
active goal/checkpoint
authority epoch
latest authority-eligible manifest
physical count
active canonical count
aliases/superseded count
DB integrity / FK violations
snapshot drift
Graph denominator
Intelligence denominator
open P0 issues
active scheduler tasks
stale send-critical facts
send_allowed / outbound
GitHub STATE pointer
Library recovery pointer
```

Never trust prompt-copied counts without reconciliation.

## 9. Canonical write protocol

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
→ GRAPH / INTELLIGENCE
→ INVARIANTS
→ OBSERVABILITY
→ PERSISTENCE
```

Never:

```text
discover → append rows → declare success
```

IDs are immutable. Superseded IDs remain lineage with explicit canonical targets.

## 10. Promotion gauntlet

Applicable checks include:

```text
SQLite integrity_check = ok
FK violations = 0
canonical IDs valid
unexplained ID gaps = 0
active name+city conflicts = 0
active non-empty domain duplicates = 0
alias targets valid
active duplicate QA states = 0
active metric-key duplicates = 0
snapshot drift = 0
DB ↔ Sheets PK reconciliation exact
Graph denominator = active canonical count
Intelligence denominator = active canonical count
stale send-critical facts without refresh = 0
invalid UNKNOWN_AFTER_SEARCH = 0 for new V3 data
score-scale violations = 0
idempotency replay unintended inserts = 0
restore logical differences = 0
send_allowed = 0 unless separately authorized
release/checkpoint/control-plane agreement = PASS
```

SQLite restore equivalence is logical, not binary SHA equality.

## 11. Graph contract

Every wave declares:

```text
GRAPH_IMPACT = NONE | META | OPERATIONAL | BOTH
```

META required for changes to goals, checkpoints, releases, waves, decisions, architecture or artifact lineage.

OPERATIONAL required for changes to entities, aliases/groups, evidence, vacancies, people/channels, housing, tasks, applications or outcomes.

No authoritative operational mutation may leave its graph representation behind.

## 12. Agent contract

`AGENTS.md` stores stable behavior/roles only.

It MUST NOT hardcode mutable frontier counts or current tasks.

Mutable state belongs in:

```text
live Drive/Sheets control plane
latest authority-eligible manifest
STATE.md
```

Agents read:

```text
WAVE_OPERATING_PROTOCOL.md
→ GOAL.md
→ STATE.md
→ AGENTS.md
→ OPERATING_RULES.md
→ live authority reconciliation
```

before material work.

## 13. Git protocol

Architecture/code/schema/protocol changes:

```text
issue when useful
→ branch
→ implementation
→ tests
→ PR
→ CI
→ diff/review
→ merge
→ operational adoption/reconciliation
```

Data-only waves never require private operational data in GitHub.

CI success validates repository contracts/tests. It does NOT prove Drive/DB runtime synchronization.

## 14. Library protocol

For material DB/schema/recovery waves:

1. build recovery bundle;
2. build manifest with SHA and `AUTHORITATIVE` vs `CANARY` state;
3. upload under `/SWITZERLAND_JOB_OS/`;
4. update `LATEST_RECOVERY.json` or equivalent pointer;
5. never label canary as authority.

Library failure creates a persistence issue but does not rewrite operational authority.

## 15. Outage protocol

If a required authority layer fails:

```text
DETECT
→ STOP AUTHORITY PROMOTION
→ REGISTER BLOCKED LAYER
→ CONTINUE SAFE RESEARCH/CANARY ONLY
→ GITHUB PUBLIC-SAFE HANDOFF
→ LIBRARY RECOVERY BUNDLE
→ CLOSE SAFE_STOP_CANARY
```

When it returns:

```text
/wave recover
→ re-read live authority
→ compare provisional work
→ anti-join IDs/names/cities/domains/aliases/tasks
→ reallocate provisional IDs if frontier moved
→ rerun canary from live parent
→ AUTHORITATIVE_WRITE only after reconciliation
```

No provisional local ID is a reservation.

## 16. Concurrency

Immediately before canonical commit:

- re-read live frontier;
- anti-join canonical entities;
- anti-join aliases/superseded IDs;
- anti-join domains;
- anti-join active task keys;
- confirm parent manifest/epoch unchanged.

If the parent moved, transition to `RECOVERY_RECONCILE` rather than force-writing.

## 17. Wave observability

Emit at minimum:

```text
wave_id / run_id
goal_id / checkpoint_id
execution_mode
authority_parent / authority_epoch
canonical_before
canonical_after_authoritative
canary_candidate_count
physical_before / physical_after_authoritative
tasks attempted/completed/failed
issues opened/resolved
SLO breaches
DB integrity / FK violations
duplicate count / snapshot drift
stale critical count
send_allowed
Graph denominator
Intelligence denominator
quality_result
closure_state
next_bottleneck
```

Never put a canary count in `canonical_after_authoritative`.

## 18. Closure states

Exactly one:

```text
COMPLETE_AUTHORITY
COMPLETE_READ_ONLY
SAFE_STOP_CANARY
BLOCKED_P0
SUPERSEDED
```

`COMPLETE_AUTHORITY` requires all required persistence/reconciliation gates.

## 19. Real-time semantics

No background daemon is claimed unless actually configured.

**Real-time synchronization** means:

> before an authoritative wave closes, every affected required layer is synchronously reconciled inside that wave.

Temporary staging/canary divergence is allowed. Silent post-wave divergence is not.

## 20. Outbound lock

Research and market mapping never imply authorization to contact employers.

Default:

```text
OUTBOUND = CLOSED
send_allowed = 0
```

External email, portal submission, DM, WhatsApp or follow-up requires the separate outbound gate plus explicit user authorization.

## 21. Current-state location rule

Current connector availability, active checkpoint, live counts, active task, parent manifest and canary frontier are operational state.

They MUST live in `STATE.md`, live Drive/Sheets and manifests — never in this permanent protocol.

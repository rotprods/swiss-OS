# SESSION RUNTIME PROTOCOL — SRP-1.0

Status: IMPLEMENTED CONTRACT / OBSERVABILITY LAYER
Project: `SWITZERLAND_JOB_OS`
Parent runtime: `GRAPH-REFACTOR-V2` + COS V2.2 + Agent Autoresearch Runtime

## Purpose

SRP answers, without relying on chat memory:

- which agent/session is working;
- what durable goal/plan/task it owns;
- which claim/fencing token grants mutation authority;
- branch/worktree/PR location;
- last heartbeat and liveness state;
- weighted progress and pending work;
- blockers and exact next action;
- whether work actually completed or only released ownership;
- how a zero-context successor recovers after interruption/death.

SRP is a projection/observability layer. It does **not** create a parallel authority system.

## Authority hierarchy

```text
Git EVENT-1.1 + Claim + Fencing Token
                  │
                  ├── Agent Autoresearch identity / experiments
                  │
                  └── SRP deterministic session projections

Drive AGENT_WORK_LEASES / AGENT_HANDOFF_LOG
                  └── live human/runtime observability mirror only

Open branch / PR observations
                  └── UNMERGED_PROPOSAL only
```

A Drive lease, PR, branch, runtime registry row or chat message can never grant write authority. Only a valid claim/fencing state does.

## Mandatory runtime identity

Every material SRP-native session reuses the existing `AgentRunContext` identity:

```text
project_id
agent_id
session_id
workstream_id
objective_id
correlation_id
goal_ids[]
plan_id
task_id
claim_id
fencing_token
worktree
branch
PR when available
base_main_sha
authority_ceiling
```

`session_id` is immutable and never reused for takeover.

A connector-only agent without a real local worktree records an explicit locator such as `REMOTE_GITHUB_CONNECTOR_ONLY`; it must not invent a filesystem path.

## Chat/runtime locator

`chat_id` is optional because not every harness exposes one.

When unavailable:

```json
{
  "provider": "chatgpt",
  "chat_id": null,
  "chat_id_state": "UNAVAILABLE_BY_HARNESS"
}
```

Never synthesize or infer a chat ID.

## Heartbeat boundary

Before an SRP-native agent begins another material mutation, it persists a death-safe `HEARTBEAT` or equivalent material progress event containing enough durable state to reconstruct:

- graph runtime identity;
- plan revision and weighted plan items;
- tests/evidence already produced;
- blocker state;
- recovery inputs;
- exact next action;
- runtime/capability locator when relevant.

No claim of real-time/background heartbeat exists unless a real daemon/scheduler is installed. Liveness is recomputed whenever SRP is materialized, checked, bootstrapped or refreshed by an authorized runtime.

## Progress semantics

Agents may not self-report arbitrary percentages.

A progress snapshot contains stable plan items:

```text
item_id
state = PENDING | IN_PROGRESS | COMPLETED | BLOCKED | SKIPPED
weight > 0
summary
optional evidence/blocker refs
```

Derived progress is:

```text
completion_percent =
    sum(weight for COMPLETED or SKIPPED items)
    / sum(all plan weights)
```

Any `percent` or `progress_percent` field supplied by an agent is invalid.

A plan may evolve only by issuing a new `plan_revision` with the change visible in durable history; prior snapshots remain historical evidence.

## Work lifecycle and claim lifecycle are distinct

Claim ownership and work completion are not the same state machine.

Examples:

```text
CLAIM_RELEASED + no WORK_COMPLETED/WORK_BLOCKED
→ CLAIM_RELEASED_BUT_WORK_NOT_TERMINAL
```

```text
WORK_COMPLETED
→ lifecycle COMPLETED / liveness TERMINAL
```

```text
WORK_BLOCKED
→ lifecycle BLOCKED / liveness TERMINAL
```

Releasing a claim must never fabricate `COMPLETED`.

## Liveness

For SRP-native non-terminal sessions, default thresholds are:

```text
last activity <= 1 hour       LIVE
1h < age <= 4h                STALE
age > 4h                      ORPHANED_CANDIDATE
```

Timeout alone never means `DEAD`.

`ORPHANED_CANDIDATE` means takeover investigation is warranted. Before takeover:

1. replay Git events/claims;
2. inspect live branch/PR/worktree/provider state;
3. inspect Drive lease and any external irreversible-operation receipts;
4. release/supersede stale ownership only when eligible;
5. acquire a strictly higher fencing token;
6. create a **new session_id**;
7. resume from the latest valid SRP bundle/iteration receipt.

Historical/pre-SRP sessions with insufficient heartbeat semantics remain `LEGACY_UNKNOWN` rather than being falsely classified as dead/orphaned.

## Live branch / PR observations

SRP may ingest open branches/PRs to improve visibility before merge.

They are always tagged as observational/proposed state. A branch can demonstrate that work probably continues, but it never overrides main/event/claim authority.

This closes a real failure mode where a valid active claim can exist only on an unmerged branch and therefore be invisible to a naive main-only dashboard.

## Drive observability

Reuse existing sheets rather than creating another agent CRM:

### `AGENT_WORK_LEASES`
Live mirror for:
- session;
- heartbeat/expiry;
- workstream/task;
- state;
- release;
- claim/fencing/branch/progress/runtime bundle fields when the sheet is upgraded.

### `AGENT_HANDOFF_LOG`
Terminal/recovery mirror for completed/blocked/released sessions.

Drive rows do not grant ownership and never replace Git lifecycle replay.

## Deterministic runtime projections

Canonical committed projection root:

```text
docs/runtime/
  registry.json
  sessions/<SESSION_ID>/
    session.json
    progress.state.json
    PROGRESS.md
    GOALS.md
    CONTEXT.md
    HANDOFF.md
    MANIFEST.json
```

`session.json` and `progress.state.json` are machine projections.
The Markdown files are human-readable views regenerated from the same runtime object.
`MANIFEST.json` content-addresses the generated views and source event/claim lineage.

No agent manually edits the generated bundle.

## Registry

`docs/runtime/registry.json` summarizes:

- canonical event-derived sessions;
- liveness and lifecycle;
- active/released claim relation;
- derived progress;
- open-branch/PR observations when supplied;
- Drive live-lease observations when supplied.

The registry must carry this authority boundary explicitly:

`GIT_EVENT_CLAIM_FENCING_IS_OWNERSHIP_AUTHORITY; LIVE_LEASES_AND_PR_OBSERVATIONS_ARE_OBSERVABILITY_ONLY`

## CI / deterministic replay

`session_runtime_guard.py` and `build_session_runtime.py --check` must prove:

- committed bundles are deterministic at their pinned `observed_at`;
- no arbitrary progress percentage exists;
- native active sessions expose valid runtime identity and heartbeat;
- no fabricated chat ID;
- no `DEAD` state inferred from TTL;
- active claims are represented by a session projection;
- bundle manifests match their generated contents;
- claim release does not imply work completion;
- open PR/Drive observations remain non-authoritative.

CI reuses committed `observed_at`; wall-clock passage alone must not make deterministic Git CI drift. Live liveness refreshes happen through a new explicit materialization observation.

## Closure contract

An SRP-native material session is not cleanly closed until it has:

1. terminal `WORK_COMPLETED` or `WORK_BLOCKED` event;
2. claim `RELEASED` or `SUPERSEDED` as appropriate;
3. final weighted progress snapshot;
4. explicit next action / blocker;
5. regenerated session bundle/registry;
6. Drive lease readback updated to terminal/released when Drive is available;
7. terminal handoff mirror when appropriate.

A merged PR alone is not session completion.
A released claim alone is not session completion.

## Safety

SRP never changes:

```text
hotel authority
H-ID allocation/reservation
Candidate private truth
application authorization
OUTBOUND
send_allowed
provider credentials
financial/offer decisions
```

SRP increases observability and recoverability only.

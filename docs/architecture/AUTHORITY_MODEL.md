# AUTHORITY MODEL — SWITZERLAND_JOB_OS

Status: **STABLE ARCHITECTURE CONTRACT**

SWITZERLAND_JOB_OS separates versioned system definition, constrained operational state, human control-plane mirrors, graph projections and recovery artifacts.

## Authority eligibility

A state may advance canonical authority only when it is an **authority-eligible fully synchronized commit**.

Where affected, authority eligibility requires:

```text
constrained DB validated
+ live Drive/Sheets mirror reconciled
+ Operational Graph reconciled
+ Intelligence reconciled
+ metrics / health / SLO updated
+ scheduler / issues / checkpoints updated
+ transitions / run log emitted
+ persistent handoff emitted
```

A valid local SQLite canary is not authority by itself.

## Precedence within authority-eligible state

```text
1. Physical + constrained operational data
2. Live control-plane registries / active machine state
3. Latest validated authority-eligible manifest
4. GitHub `STATE.md` public-safe pointer
5. Release/handoff prose
6. Legacy documentation
```

If layers disagree, do not silently choose. Enter `RECOVERY_RECONCILE`, record drift and repair the stale layer.

Canary artifacts are explicitly excluded from the authority chain until the Wave Operating Protocol promotion chain completes.

## Storage roles

### GitHub

Version-control and executable-contract plane for:

- goals and stable operating contracts;
- architecture and engine registry;
- schemas/migrations;
- tests/validators/CI;
- runbooks;
- durable decisions;
- public-safe state pointers and handoffs.

GitHub is not the operational database.

### Drive / Sheets

Human control plane and operational mirror for:

- goals/checkpoints;
- scheduler;
- issues;
- metrics/health/SLO;
- run/state-transition ledgers;
- hotel/entity registries;
- human-readable Graph/Intelligence projections;
- operational collaboration and project documents.

Authoritative writes resolve canonical PKs/keys. Blind row-offset writes are prohibited.

### Constrained database

Operational state backend enforcing PK/FK/UNIQUE/CHECK/idempotency and restore/replay semantics.

Its state becomes authority only after affected mirrors/graphs/governance surfaces reconcile.

A raw repaired SQLite file is the preferred recovery artifact, but raw-binary provider egress is not a semantic authority requirement. `CCP-1.0` may represent constrained state as an immutable durable remote base plus a pinned deterministic `ARR-1.0` repair definition, precommitted materialized SHA-256 and exact materialization proof. This is a **DURABLE_MATERIALIZABLE_CONSTRAINED_PARENT**, not a local canary and not an authority promotion by itself.

A CCP remains `RECONCILE_REQUIRED_CROSS_PLANE` until the materialized state and every affected Drive/Sheets, Intelligence, Operational Graph, scheduler/checkpoint, observability and recovery plane reconcile in one bounded recovery wave. CCP never pre-authorizes a numeric active denominator, canonical ID allocation or outbound.

Contract: `docs/operations/COMPOSITE_CONSTRAINED_PARENT.md`.

### Operational Graph

PK-keyed operational relationship state for entities, aliases/groups, evidence, vacancies, people/channels, housing, tasks, applications and outcomes.

It must synchronize in the same authoritative wave as the operational mutation it represents.

### Project Memory Meta Graph

Project/release memory for goals, checkpoints, releases, waves, decisions, architecture and artifact lineage.

It is not the complete operational graph.

### ChatGPT Library

Durable recovery/cold-persistence surface.

It may hold recovery bundles, manifests, digests and public-safe handoffs, but it is **not operational truth**.

A Library artifact must state whether it is `AUTHORITATIVE` or `CANARY` and identify its parent/wave.

### Local workspace / local Git

Execution cache/workspace only unless running in a deliberately persistent operator environment.

In ChatGPT, local filesystem/Git network persistence is not a shared authority mechanism. GitHub remains the shared VCS authority.

## Failure semantics

If a required authority plane is unavailable:

```text
AUTHORITATIVE_WRITE → prohibited
READ_ONLY_RESEARCH  → allowed when safe
DEGRADED_CANARY     → allowed when safe
RECOVERY_RECONCILE  → required before later promotion
```

The system must never hide the missing plane by promoting a local/canary count.

## Non-negotiable boundaries

- GitHub never replaces the constrained operational DB.
- Sheets never acts as an unconstrained production database.
- Library never becomes operational authority.
- Meta Graph never substitutes for Operational Graph.
- CI PASS never proves runtime Drive/DB/Graph synchronization.
- No checkpoint closes merely because a numeric target is reached.
- Outbound remains an independent authorization stack.

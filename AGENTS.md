# AGENTS — SWITZERLAND_JOB_OS

## Mission contract

Every agent optimizes the G-0001 North Star, not vanity metrics.

## Mandatory GRAPH-REFACTOR-V2 bootstrap

Every material agent MUST operate inside `GRAPH-REFACTOR-V2`. Before mutation it must read `docs/operations/AGENT_AUTORESEARCH_PROGRAM.md` and bind its work to durable graph identity:

```text
project_id + agent_id + session_id + workstream_id + objective_id + correlation_id
+ goal_ids[] + plan_id + task_id + claim_id + fencing_token
+ worktree + branch + PR(if any) + base_main_sha + authority_ceiling
```

No anonymous material work is valid. `session_id` is never reused. Every parallel agent uses an isolated worktree/branch and a non-colliding claim. Every bounded iteration records a testable hypothesis, baseline, evaluation suite and one of `KEEP | DISCARD | CRASH | BLOCKED`. Discarded/crashed code may be reverted; the experiment evidence and graph lineage remain durable.

Before starting the next mutation, persist a death-safe heartbeat sufficient for another zero-context agent to recover the exact goal/plan/task, claim/fencing ownership, worktree/branch/PR, experiment state, tests/evidence and next safe action. A PR is not ownership; the claim/fencing token is ownership.

The Autoresearch loop never weakens authority, security, candidate-truth, human-approval or outbound gates. See `src/swiss_os/agent_improvement_runtime.py` for executable keep/discard semantics.

Before material work:

1. read `docs/operations/META_EXECUTION_PROTOCOL.md`;
2. read `docs/operations/WAVE_OPERATING_PROTOCOL.md`;
3. read `GOAL.md`;
4. read `STATE.md` from the current GitHub `main` ancestry;
5. reconcile against live Drive/Sheets + the latest authority-eligible constrained manifest;
6. read relevant invariants, issues, SLOs, TTL state and scheduler tasks;
7. identify affected engines using `docs/architecture/ENGINE_REGISTRY.md`;
8. when work affects hotel-universe coverage, CRM seeding or outbound readiness, read `docs/operations/CRM_UNIVERSE_PROTOCOL.md`;
9. when structured source capture/scope is involved, read `docs/operations/DISCOVER_SWISS_SNAPSHOT_ADAPTER.md` and `docs/operations/SOURCE_SCOPE_RECONCILIATION.md`;
10. when the authority parent contains aliases/superseded IDs, or work changes entity supersession, read and execute `docs/operations/ALIAS_SEMANTIC_RECONCILIATION.md` before any authority promotion;
11. select/declare an execution mode, MEP route and `GRAPH_IMPACT`;
12. fail closed on lineage ambiguity, stale parent state, semantic alias ambiguity or partial writes;
13. preserve outbound CLOSED unless separately and explicitly authorized.

Before checkpoint promotion, production continuation, architecture release or a user-requested full-system review, also run the applicable gates in `docs/operations/PRODUCTION_READINESS_GAUNTLET.md`.

## Meta execution contract

MEP-2.0 is the cross-engine continuity layer.

Every invoked or scheduled cycle follows the COLETTE loop:

```text
COLLECT authority/ancestry/capabilities
→ OBSERVE drift/blockers
→ LOCATE highest-value safe bottleneck
→ EXECUTE one bounded WAVE
→ TEST / adversarial QA
→ TRANSACT / PERSIST affected durable planes
→ EVOLVE state and select the next safe route
```

### No-idle rule

A preferred connector, provider or write path becoming unavailable is not itself permission to stop while safe productive alternatives exist.

Agents MUST use the deterministic fallback lattice in `META_EXECUTION_PROTOCOL.md`.

Examples:

```text
native Sheets write unavailable
→ source acquisition / source-scope / mass staging / exact-current refresh / QA / recovery
```

```text
discover.swiss key unavailable
→ coherent member-directory evidence / exact-current refresh / discovery-only anti-join
```

```text
direct Drive connector unavailable but authenticated Drive mount exists
→ rehydrate through mount without pretending native Sheet mutation occurred
```

This rule never lowers authority, privacy, evidence, provider-control, or outbound gates. If no safe route reduces the current bottleneck, record a typed P0 rather than fabricating progress.

## Authority

Repository prose is versioned system memory, not operational truth.

Only the last fully synchronized authority-eligible constrained commit may advance canonical state. A local SQLite canary is non-authoritative until DB → Sheets → Graph/Intelligence → observability → checkpoint/scheduler → handoff reconciliation succeeds.

Structural integrity is not semantic authority. If alias/supersession semantics are unresolved, the affected active denominator is `RECONCILE_REQUIRED` even when SQLite integrity and FK checks pass.

Mutable frontier counts/tasks MUST NOT be hardcoded in this file. Read them from the live control plane and `STATE.md` after reconciliation.

Every material cycle must also compare its last-known Git ancestry with the current shared `main`. Concurrent progress is absorbed/reconciled; it is never overwritten from a stale chat handoff.

## Core roles / engines

The canonical engine taxonomy and interfaces live in `docs/architecture/ENGINE_REGISTRY.md`. Major roles include:

- Mission Commander — goal hierarchy, wave scope and release integrity.
- Authority & Reconciliation Engine — reconstruct authority and detect cross-plane drift.
- Wave Transaction Engine — bound scope, mode, gates and closure.
- Market Mapper / Discovery Engine — current entity universe and discovery evidence.
- Entity Resolution Engine — canonical identity, aliases, groups and conflicts.
- Evidence Engine — provenance, scope, freshness and typed unknowns.
- Vacancy Engine — current vacancy/careers state.
- Housing Engine — vacancy-linked vs employer-policy housing evidence.
- People Engine — public-professional decision-maker resolution.
- Channel Engine — recruitment/contact routing and channel policy.
- Intelligence Engine — evidence-backed depth/dimension resolution.
- Operational Graph Engine — PK-keyed entity/evidence/task relationships.
- Project Memory Meta Graph Engine — goals/checkpoints/waves/releases/artifacts/decisions.
- Scheduler & TTL Engine — state-driven tasks, anti-joins and refresh work.
- Scoring Engine — versioned 0–100 heuristic priority rankings.
- Candidate Truth & Asset Engine — truthful lane-specific facts/assets.
- Template/Message Engine — evidence-backed deterministic renders.
- Data Engine — constrained DB, migrations, restore/replay, DB↔Sheets reconciliation.
- QA/Governance Engine — invariants, SLOs, gates, transitions and fail-closed promotion.
- Observability Engine — metrics, health, run logs and drift.
- Recovery & Persistence Engine — Library/Drive bundles, manifests and lineage.
- Git/CI Engine — branch/PR/tests/guards/versioning.
- Security/Privacy/Outbound Gate Engine — public boundary, suppression, idempotency and authorization.

MEP is not a twenty-third domain engine; it coordinates existing engines and chooses the next safe route from capability/bottleneck state.

Do not invent an additional engine unless it owns a distinct persistent responsibility or authority/invariant boundary.

## Mandatory wave loop

```text
META CYCLE OPEN
→ AUTHORITY + ANCESTRY BOOTSTRAP
→ CAPABILITY MATRIX
→ DRIFT / ISSUE / SLO / TTL SCAN
→ MEP ROUTE SELECTION
→ WAVE OPEN
→ SELECT CURRENT SCHEDULER/BOTTLENECK TASK
→ DISPATCH AFFECTED ENGINES
→ DISCOVER / VERIFY
→ NORMALIZE
→ DEDUPE / ALIAS / GROUP RESOLUTION
→ ALIAS SEMANTIC RECONCILIATION WHEN ALIASES EXIST
→ STAGE
→ CANARY
→ VALIDATE
→ COMMIT CONSTRAINED DB IF ELIGIBLE
→ MIRROR SHEETS BY PK IF ELIGIBLE
→ GRAPH / INTELLIGENCE SYNC IF AUTHORITY AFFECTED
→ QA + INVARIANTS + SLO
→ METRICS + HEALTH + SCHEDULER + ISSUES
→ TRANSITIONS + RUN LOG
→ GITHUB STATE/HANDOFF
→ LIBRARY / DRIVE RECOVERY PERSISTENCE
→ FINAL RECONCILIATION
→ WAVE CLOSE
→ META LEARN / NEXT ROUTE
```

If a required authority plane is unavailable, switch to `DEGRADED_CANARY` or `RECOVERY_RECONCILE`; no canonical promotion is allowed, but MEP must continue another safe route when one exists.

## Graph contract

Maintain two explicit scopes:

### PROJECT_MEMORY_META_GRAPH

Goals, checkpoints, releases, waves, decisions, artifacts, protocols, capability blockers and architecture.

### OPERATIONAL_GRAPH

Hotels, aliases, groups, vacancies, people, channels, evidence, housing, audits, tasks, applications and outcomes.

Operational graph truth belongs in constrained PK-keyed state. `graph_registry.json` or similar project-memory files are not the entire operational graph.

Every authoritative entity/evidence/task mutation must update the affected operational graph in the same wave.

Every material MEP decision that changes routing, protocol, blocker state or durable artifact lineage updates the META graph/handoff surfaces.

## Persistence contract

- **GitHub:** code, contracts, schemas, CI, public-safe state/handoffs.
- **Drive/Sheets:** human control plane and operational mirror.
- **SQLite:** constrained state backend.
- **ChatGPT Library:** durable recovery/cold persistence, not operational truth.
- **Local workspace/Git:** execution cache only unless running in a persistent operator environment; never sufficient for authority by itself.

A create-only Drive artifact path is not equivalent to native in-place Sheets mutation. Record capability semantics precisely.

## Context-compaction survival

A material cycle must leave enough durable state for another agent/chat to reconstruct truth without relying on conversation memory.

Minimum pointers:

```text
current GitHub main SHA
STATE.md
latest authority parent/manifest
LATEST_RECOVERY
LATEST_CRM_UNIVERSE when applicable
current protocol versions
current P0 blockers
latest material handoff / meta-cycle decision
```

Material reasoning that changes execution becomes a durable contract, decision, issue, test or handoff before closure.

## Hard rules

- Truth > volume.
- Evidence > inference.
- Canonical IDs are immutable and unique.
- Historical pages do not imply current membership.
- `UNKNOWN_AFTER_SEARCH` requires Search Proof.
- Resolution, known-value, evidence and freshness are separate metrics.
- Scores are heuristics, not hiring probabilities.
- Phone does not imply WhatsApp eligibility.
- Never fabricate candidate facts, contacts, housing, salaries, vacancies or internal employer gaps.
- Never write Sheets by blind row offset when a canonical key can be resolved.
- GitHub is not the operational DB.
- Library is not the operational DB.
- No PII/operational binaries in the public repository.
- No checkpoint promotion without validation and state transition.
- No canary count may be reported as authoritative.
- **No authority promotion may proceed from aliases/supersessions whose ASR-1.0 semantic state is not `EXACT`.**
- **No outbound gate may open before `CRM_UNIVERSE_COMPLETE = TRUE` for the frozen verified target snapshot.**
- A partial checkpoint, shortlist or deeply enriched sample never substitutes for complete CRM source-record coverage.
- No outbound without explicit authorization after all independent gates pass.
- Do not claim background/real-time daemons unless they actually exist.
- Do not stop merely because the preferred tool path failed when MEP identifies another safe productive route.
- Never treat page number as stable source-record identity across member-directory cache/locale epochs.
- Never overwrite concurrent shared progress without ancestry reconciliation.

## Closure

Every material wave closes as exactly one:

```text
COMPLETE_AUTHORITY
COMPLETE_READ_ONLY
SAFE_STOP_CANARY
BLOCKED_P0
SUPERSEDED
```

The enclosing meta-cycle then records its next route or terminal blocker.

Use `STATE.md` for the current mutable frontier. Use this file for stable agent behavior only.
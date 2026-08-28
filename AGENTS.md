# AGENTS — SWITZERLAND_JOB_OS

## Mission contract

Every agent optimizes the G-0001 North Star, not vanity metrics.

Before material work:

1. read `docs/operations/META_EXECUTION_PROTOCOL.md`;
2. read `docs/operations/NEXT_POINTER_PROTOCOL.md`;
3. read `docs/operations/WAVE_OPERATING_PROTOCOL.md`;
4. read `GOAL.md`;
5. read `STATE.md` from the current GitHub `main` ancestry;
6. reconcile against live Drive/Sheets + the latest authority-eligible constrained manifest;
7. read relevant invariants, issues, SLOs, TTL state and scheduler tasks;
8. identify affected engines using `docs/architecture/ENGINE_REGISTRY.md`;
9. when work affects hotel-universe coverage, CRM seeding or outbound readiness, read `docs/operations/CRM_UNIVERSE_PROTOCOL.md`;
10. when MEP selects structured acquisition, read `docs/operations/DISCOVER_SWISS_SNAPSHOT_ADAPTER.md`;
11. when MEP selects member-directory evidence acquisition, read and execute `docs/operations/MEMBER_DIRECTORY_MANIFEST.md` (MDM-1.0);
12. before source-scope reconciliation, read `docs/operations/SOURCE_SCOPE_RECONCILIATION.md` and require both DSA and MDM inputs to pass their own gates;
13. select/declare an execution mode, MEP route and `GRAPH_IMPACT`;
14. fail closed on lineage ambiguity, stale parent state or partial writes;
15. preserve outbound CLOSED unless separately and explicitly authorized.

Before checkpoint promotion, production continuation, architecture release or a user-requested full-system review, also run the applicable gates in `docs/operations/PRODUCTION_READINESS_GAUNTLET.md`.

## Meta execution contract

MEP-2.0 is the cross-engine continuity layer.

Every invoked or scheduled activation follows the COLETTE loop repeatedly:

```text
COLLECT authority/ancestry/capabilities
→ OBSERVE drift/blockers
→ LOCATE highest-value safe bottleneck
→ EXECUTE one bounded WAVE
→ TEST / adversarial QA
→ TRANSACT / PERSIST affected durable planes
→ EVOLVE state
→ persist NEXT
→ immediately execute the next safe cycle while runtime remains available
```

Completing one wave is not a stop condition.

### No-idle rule

A preferred connector, provider or write path becoming unavailable is not itself permission to stop while safe productive alternatives exist.

Agents MUST use the deterministic fallback lattice in `META_EXECUTION_PROTOCOL.md`.

Examples:

```text
native Sheets write unavailable
→ source acquisition / MDM evidence / source-scope / mass staging / exact-current refresh / QA / recovery
```

```text
discover.swiss key unavailable
→ MDM-1.0 coherent member-directory evidence / exact-current refresh / discovery-only anti-join
```

```text
direct Drive connector unavailable but authenticated Drive mount exists
→ rehydrate through mount without pretending native Sheet mutation occurred
```

This rule never lowers authority, privacy, evidence, provider-control, or outbound gates. If no safe route reduces the current bottleneck, record a typed P0 rather than fabricating progress.

## Authority

Repository prose is versioned system memory, not operational truth.

Only the last fully synchronized authority-eligible constrained commit may advance canonical state. A local SQLite canary is non-authoritative until DB → Sheets → Graph/Intelligence → observability → checkpoint/scheduler → handoff reconciliation succeeds.

Mutable frontier counts/tasks MUST NOT be hardcoded in this file. Read them from the live control plane and `STATE.md` after reconciliation.

Every material cycle must compare its last-known Git ancestry with the current shared `main`. Concurrent progress is absorbed/reconciled; it is never overwritten from a stale chat handoff.

A persisted `NEXT` pointer is continuation state, not authorization. Before resuming it, reread `main`, authority parent/epoch, blockers and capabilities, then recalculate MEP.

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

MDM is not a separate authority engine; it is an executable source-evidence contract owned by Discovery/Evidence/QA responsibilities and consumed by SSR.

Do not invent an additional engine unless it owns a distinct persistent responsibility or authority/invariant boundary.

## Mandatory wave loop

```text
META ACTIVATION OPEN
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
→ META LEARN
→ NEXT POINTER
→ NEXT SAFE WAVE IN SAME ACTIVATION
```

If a required authority plane is unavailable, switch to `DEGRADED_CANARY` or `RECOVERY_RECONCILE`; no canonical promotion is allowed, but MEP must continue another safe route when one exists.

## Graph contract

Maintain two explicit scopes:

### PROJECT_MEMORY_META_GRAPH

Goals, checkpoints, releases, waves, meta-cycles, decisions, artifacts, protocols, capability blockers and architecture.

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

A material activation must leave enough durable state for another agent/chat to reconstruct truth without relying on conversation memory.

Minimum pointers:

```text
current GitHub main SHA
STATE.md
latest authority parent/manifest
LATEST_RECOVERY
LATEST_CRM_UNIVERSE when applicable
NEXT
current protocol versions
current authority-blocking P0 blockers
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
- **No outbound gate may open before `CRM_UNIVERSE_COMPLETE = TRUE` for the frozen verified target snapshot.**
- A partial checkpoint, shortlist or deeply enriched sample never substitutes for complete CRM source-record coverage.
- No outbound without explicit authorization after all independent gates pass.
- Do not claim background/real-time daemons unless they actually exist.
- Do not stop merely because the preferred tool path failed when MEP identifies another safe productive route.
- Never treat page number as stable source-record identity across member-directory cache/locale epochs.
- Never label a mixed/partial MDM evidence set `coverage_complete=true`.
- Never overwrite concurrent shared progress without ancestry reconciliation.
- Never execute a persisted NEXT pointer without revalidation.

## Closure

Every material wave closes as exactly one:

```text
COMPLETE_AUTHORITY
COMPLETE_READ_ONLY
SAFE_STOP_CANARY
BLOCKED_P0
SUPERSEDED
```

The enclosing activation then persists NEXT and immediately continues the next safe route while runtime capacity remains. It only stops when the project/activation is genuinely terminal, all safe productive routes are blocked, explicit authorization/private input is required, or runtime/tool limits force handoff after NEXT persistence.

Use `STATE.md` for the current mutable frontier. Use this file for stable agent behavior only.
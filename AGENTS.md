# AGENTS — SWITZERLAND_JOB_OS

## Mission contract

Every agent optimizes the G-0001 North Star, not vanity metrics.

Before material work:

1. read `docs/operations/WAVE_OPERATING_PROTOCOL.md`;
2. read `GOAL.md`;
3. read `STATE.md`;
4. reconcile against live Drive/Sheets + the latest authority-eligible constrained manifest;
5. read relevant invariants, issues, SLOs, TTL state and scheduler tasks;
6. identify affected engines using `docs/architecture/ENGINE_REGISTRY.md`;
7. when work affects hotel-universe coverage, CRM seeding or outbound readiness, read `docs/operations/CRM_UNIVERSE_PROTOCOL.md`;
8. select/declare an execution mode and `GRAPH_IMPACT`;
9. fail closed on lineage ambiguity, stale parent state or partial writes;
10. preserve outbound CLOSED unless separately and explicitly authorized.

Before checkpoint promotion, production continuation, architecture release or a user-requested full-system review, also run the applicable gates in `docs/operations/PRODUCTION_READINESS_GAUNTLET.md`.

## Authority

Repository prose is versioned system memory, not operational truth.

Only the last fully synchronized authority-eligible constrained commit may advance canonical state. A local SQLite canary is non-authoritative until DB → Sheets → Graph/Intelligence → observability → checkpoint/scheduler → handoff reconciliation succeeds.

Mutable frontier counts/tasks MUST NOT be hardcoded in this file. Read them from the live control plane and `STATE.md` after reconciliation.

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

Do not invent an additional engine unless it owns a distinct persistent responsibility or authority/invariant boundary.

## Mandatory wave loop

```text
WAVE OPEN
→ AUTHORITY BOOTSTRAP
→ RECONCILE
→ ISSUE/SLO/TTL SCAN
→ SELECT CURRENT SCHEDULER TASK
→ DISPATCH AFFECTED ENGINES
→ DISCOVER / VERIFY
→ NORMALIZE
→ DEDUPE / ALIAS / GROUP RESOLUTION
→ STAGE
→ CANARY
→ VALIDATE
→ COMMIT CONSTRAINED DB
→ MIRROR SHEETS BY PK
→ GRAPH / INTELLIGENCE SYNC
→ QA + INVARIANTS + SLO
→ METRICS + HEALTH + SCHEDULER + ISSUES
→ TRANSITIONS + RUN LOG
→ GITHUB STATE/HANDOFF
→ LIBRARY / DRIVE RECOVERY PERSISTENCE
→ FINAL RECONCILIATION
→ WAVE CLOSE
```

If a required authority plane is unavailable, switch to `DEGRADED_CANARY`; no canonical promotion is allowed.

## Graph contract

Maintain two explicit scopes:

### PROJECT_MEMORY_META_GRAPH

Goals, checkpoints, releases, waves, decisions, artifacts and architecture.

### OPERATIONAL_GRAPH

Hotels, aliases, groups, vacancies, people, channels, evidence, housing, audits, tasks, applications and outcomes.

Operational graph truth belongs in constrained PK-keyed state. `graph_registry.json` or similar project-memory files are not the entire operational graph.

Every authoritative entity/evidence/task mutation must update the affected operational graph in the same wave.

## Persistence contract

- **GitHub:** code, contracts, schemas, CI, public-safe state/handoffs.
- **Drive/Sheets:** human control plane and operational mirror.
- **SQLite:** constrained state backend.
- **ChatGPT Library:** durable recovery/cold persistence, not operational truth.
- **Local workspace/Git:** execution cache only unless running in a persistent operator environment; never sufficient for authority by itself.

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

## Closure

Every material wave closes as exactly one:

```text
COMPLETE_AUTHORITY
COMPLETE_READ_ONLY
SAFE_STOP_CANARY
BLOCKED_P0
SUPERSEDED
```

Use `STATE.md` for the current mutable frontier. Use this file for stable agent behavior only.
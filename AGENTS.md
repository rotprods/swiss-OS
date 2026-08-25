# AGENTS — SWITZERLAND_JOB_OS

## Mission contract

Every agent optimizes the G-0001 North Star, not vanity metrics.

Before material work:

1. read `GOAL.md`;
2. read `STATE.md`;
3. reconcile against live Drive/Sheets + latest validated operational manifest;
4. read relevant invariants/issues/scheduler tasks;
5. fail closed on lineage ambiguity or partial writes;
6. preserve outbound CLOSED unless separately and explicitly authorized.

## Authority

Repository prose is versioned system memory, not operational truth. Live constrained state wins when newer.

## Core roles

- Mission Commander — goal hierarchy and release integrity.
- Market Mapper — current entity universe and snapshot reconciliation.
- Entity Resolution Engine — canonical identity, aliases, groups and conflicts.
- Evidence Engine — provenance, scope, freshness and typed unknowns.
- Vacancy Engine — current vacancy/careers state.
- Housing Engine — vacancy-linked vs employer-policy housing evidence.
- People Engine — public-professional decision-maker resolution.
- Channel Engine — recruitment/contact routing and channel policy.
- Scoring Engine — versioned 0–100 heuristic priority rankings.
- Candidate Engine — truthful lane-specific assets and claims.
- Template/Message Engine — evidence-backed deterministic renders.
- Data Engine — constrained DB, migrations, restore/replay, DB↔Sheets reconciliation.
- Graph Engine — PK-keyed graph synchronization.
- Scheduler Engine — state-driven tasks, anti-joins and TTL refresh.
- QA/Governance Engine — invariants, SLOs, gates, transitions and fail-closed promotion.
- Observability Engine — metrics, health, run logs and drift.

## Mandatory execution loop

```text
BOOTSTRAP
→ RECONCILE
→ SELECT CURRENT SCHEDULER TASK
→ DISCOVER / VERIFY
→ NORMALIZE
→ DEDUPE
→ STAGE
→ CANARY
→ VALIDATE
→ COMMIT DB
→ MIRROR SHEETS
→ GRAPH / INTELLIGENCE SYNC
→ QA + INVARIANTS
→ METRICS + TRANSITIONS
→ PERSIST HANDOFF
```

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
- GitHub is not the operational DB.
- No PII/operational binaries in this public repository.
- No checkpoint promotion without validation and state transition.
- No outbound without explicit authorization.

## Current frontier

Canonical: `SV2-058 / CP0750-BATCH04`, 677→750.  
Depth: `CP-0800-CURRENT-L4`, 105→677.  
Outbound: CLOSED.

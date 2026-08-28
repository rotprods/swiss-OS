# GOAL — SWITZERLAND_JOB_OS

## G-0001 — North Star

**Priority:** P0

Secure for Roberto a real Swiss job offer that is legal, truthful, verifiable, compatible with his real profile, economically viable, sustainable for relocation, acceptable to Roberto and capable of supporting long-term life in Switzerland.

The project optimizes:

```text
P(verified viable Swiss offer × Roberto accepts × relocation succeeds)
```

Hotel counts, scraping volume, outreach volume and dashboards are infrastructure, not the mission.

## Goal tree contract

```text
G-0001  Verified viable Swiss offer + sustainable relocation
├── G-0500  Canonical Swiss hotel universe / CRM parity
├── G-0600  Candidate readiness and truthful lane assets
├── G-0700  Full Swiss Hotel Intelligence / outreach-readiness OS
└── G-0800  Maximum Swiss Employment Acquisition OS
```

The live state, active checkpoint, counts, current entity epoch, constrained parent and next scheduler task are mutable operational state and MUST be read from the live control plane, latest authority-eligible constrained manifest and `STATE.md`.

This document deliberately does not duplicate mutable frontier counters.

## G-0500 — Canonical market + CRM universe system

Purpose:

- freeze/version the target hotel-directory snapshot;
- represent 100% of its source records in the CRM;
- maintain a deduplicated, provenance-backed Swiss hotel/entity universe;
- preserve immutable canonical IDs and alias lineage;
- distinguish source-record coverage from active canonical entity count;
- synchronize constrained DB, Sheets/CRM mirror, Graph/Intelligence and checkpoint observability.

The governing contract is `docs/operations/CRM_UNIVERSE_PROTOCOL.md`.

`CRM_UNIVERSE_COMPLETE = TRUE` requires every source record in the frozen verified snapshot to be deterministically mapped as canonical, alias or explicit exclusion, with zero unresolved/unmapped source records and exact affected-plane reconciliation.

Intermediate count checkpoints are scale milestones only. They do not satisfy the CRM-universe goal.

Canonical promotion follows the Wave Operating Protocol:

```text
DISCOVER
→ NORMALIZE
→ DEDUPE / ALIAS / GROUP RESOLUTION
→ RECONCILE EVIDENCE SCOPE
→ STAGE
→ CANARY
→ VALIDATE
→ DB COMMIT
→ SHEETS / CRM PK MIRROR
→ GRAPH / INTELLIGENCE
→ QA / INVARIANTS / SLO
→ OBSERVABILITY / HANDOFF / RECOVERY
```

## G-0600 — Candidate readiness

Maintain truthful, lane-specific candidate readiness for ENTRY / HYBRID / CREATIVE / PORTAL.

Do not fabricate phone, language CEFR, availability, LinkedIn, portfolio URLs, metrics, employment or case-study claims. ENTRY must not be blocked by CREATIVE/HYBRID-only assets where irrelevant.

## G-0700 — Intelligence system

Progressively resolve hotel intelligence with evidence-aware semantics across identity, web/careers, vacancies, housing, people, channels, social/digital/creative/tech, proposition and routing dimensions.

L1/L4/L9 counts are operational metrics and therefore live in the control plane/STATE pointer, not in this stable goal contract.

## G-0800 — Maximum acquisition readiness

Bring market, candidate, evidence, routing, asset, graph, scheduler and governance systems to maximum truthful pre-outbound readiness while keeping irreversible external action independently gated.

## Outbound hard lock

Outbound defaults to:

```text
OUTBOUND = CLOSED
send_allowed = 0
```

Before the outbound stack may even be evaluated:

```text
CRM_UNIVERSE_COMPLETE = TRUE
```

After that prerequisite, no email, portal submission, DM, WhatsApp or follow-up may execute without all applicable evidence, freshness, channel, suppression, idempotency, candidate-asset and explicit-user-authorization gates.

## Checkpoint semantics

A checkpoint is never complete because a counter reaches target. Completion requires all applicable integrity, QA, restore/replay, DB↔Sheets, Graph/Intelligence, scheduler, observability, persistence and governance gates in `docs/operations/WAVE_OPERATING_PROTOCOL.md`.

## Definition of success

G-0001 closes only after a real offer is verified, economically assessed and accepted. Every other goal is a supporting system.
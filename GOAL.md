# GOAL — SWITZERLAND_JOB_OS

## G-0001 — North Star

**Priority:** P0

Secure for Roberto a real Swiss job offer that is legal, truthful, verifiable, compatible with his real profile, economically viable, sustainable for relocation, acceptable to Roberto and capable of supporting long-term life in Switzerland.

The project optimizes:

```text
P(verified viable Swiss offer × Roberto accepts × relocation succeeds)
```

Hotel counts, scraping volume, outreach volume, architecture maturity and dashboards are infrastructure, not the mission.

## Goal tree contract — V2.2 compatibility model

Existing durable IDs are preserved. V2.2 changes semantics by **specialization**, not destructive renumbering.

```text
G-0001  Verified viable Swiss offer + sustainable relocation
├── G-0500  NICHE-001 Hotels: canonical universe / CRM parity
├── G-0600  Candidate truth + lane readiness + approved assets
├── G-0700  Employment intelligence core
│   ├── G-0710  Generic organization/opportunity intelligence
│   ├── G-0720  Niche adapter coverage
│   └── G-0730  Evidence / people / channel / benefit intelligence
└── G-0800  Swiss Employment Acquisition OS
    ├── G-0810  Application packet + adversarial authorization gates
    ├── G-0820  Response / outcome learning
    ├── G-0830  Interview pipeline
    ├── G-0840  Offer verification
    ├── G-0850  Financial viability
    └── G-0860  Relocation readiness
```

`G-0500` remains hotel-specific for backward compatibility and becomes the first niche implementation, not the system boundary. Additional niches attach through G-0720 and the generic employment core.

Mutable frontier counts, current claim/fencing token, active checkpoint, entity epoch and next safe task MUST be read from live state (`STATE.md`, `docs/state/NEXT.json`, `docs/state/v2/*` and operational authority), never inferred from this stable goal contract.

## G-0500 — NICHE-001 Hotels

Purpose:

- freeze/version the target hotel-directory snapshot;
- represent its source records in the CRM with explicit unresolved states;
- maintain deduplicated, provenance-backed hotel/entity identity;
- preserve immutable H-IDs and alias lineage;
- synchronize constrained DB, control-plane mirror, Graph/Intelligence and checkpoint observability;
- prove compatibility with the generic organization/niche model before any authority migration.

`CRM_UNIVERSE_COMPLETE = TRUE` requires the full frozen verified snapshot to be terminally partitioned with zero unresolved source records and exact affected-plane reconciliation.

Intermediate hotel count checkpoints are niche scale milestones only. They do not satisfy G-0001.

## G-0600 — Candidate truth and readiness

Maintain truthful candidate state for ENTRY / HYBRID / CREATIVE / PORTAL.

Candidate technical QA and human approval are independent. No asset becomes externally approved merely because it renders correctly or passes ATS checks.

Never fabricate contact data, CEFR levels, availability, work history, metrics, equipment, employers, degrees or case-study outcomes. ENTRY must not be blocked by CREATIVE/HYBRID-only assets where irrelevant.

## G-0700 — Employment intelligence core

Build reusable intelligence across niches:

- organization identity/group/location;
- opportunities and role families;
- people/recruiters;
- channels/policies;
- evidence/search proof/freshness;
- housing/benefits/compensation where observable;
- fit and routing signals.

Unknown remains unknown unless search-proof semantics justify `UNKNOWN_AFTER_SEARCH`. Scoring is a priority signal, never hiring probability.

## G-0800 — Swiss Employment Acquisition OS

Convert truthful candidate + market intelligence into safe measurable acquisition:

```text
truth
→ approved assets
→ opportunity/target binding
→ packet compilation
→ adversarial gates
→ explicit authorization
→ application/outreach
→ response
→ interview
→ offer
→ financial viability
→ relocation
```

`PACKET_COMPILED` is never equivalent to `SEND_AUTHORIZED`.

## Outbound hard lock

Outbound defaults to:

```text
OUTBOUND = CLOSED
send_allowed = 0
```

Any irreversible action requires all applicable independent gates: target/evidence freshness, candidate assets, claims, channel policy, suppression, idempotency, group/duplicate logic and explicit user authorization.

Legacy hotel-universe prerequisites remain binding where the active campaign contract says so; V2.2 does not weaken an existing gate by rewording the architecture.

## Checkpoint semantics

A checkpoint is never complete because a counter reaches target or a document exists. Completion requires applicable implementation, executed tests, security review, state/graph/evidence updates, recovery/handoff and no unresolved blocking regression.

## Definition of success

G-0001 closes only after a real offer is verified, economically assessed, accepted and relocation is operationally ready. Every other goal is supporting infrastructure.
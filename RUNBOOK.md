# RUNBOOK — HARDENED EXECUTION

## 0. Bootstrap

Read `GOAL.md`, `STATE.md`, `AGENTS.md` and the live Drive control plane. Recompute state before material writes.

Abort promotion when release lineage, PK sets, active checkpoint or critical invariants disagree.

## 1. Integrity preflight

Validate:

- canonical physical/unique state;
- DB↔Sheets PK-set equality;
- duplicate/gap/tombstone semantics;
- constrained-core field domains;
- graph/intelligence orphan state;
- metric uniqueness;
- critical issues/invariants;
- TTL/freshness queue state;
- outbound state.

## 2. Canonical discovery

Prefer exact current first-party entity-detail evidence.

Every candidate follows:

```text
DISCOVER → NORMALIZE → DEDUPE → RECONCILE → STAGE → CANARY → VALIDATE
```

Historical/cache candidates stay discovery-only until current membership is proven.

## 3. Commit protocol

```text
validated stage
→ constrained DB transaction
→ integrity/FK/UNIQUE/CHECK
→ replay test
→ Sheets PK mirror
→ exact DB↔Sheets reconciliation
→ Intelligence / Graph V2 sync
→ QA / invariants / SLOs
→ metrics / transitions / scheduler
→ persistent handoff
```

Never perform blind `discover → append → declare success`.

## 4. QA

Track independently:

- resolution_pct
- known_value_pct
- evidence_coverage_pct
- freshness_pct
- conflict_free_pct
- send_critical_pct

Typed unknown may count as resolved only with valid Search Proof; it never counts as a known value.

## 5. Scoring

Use declared 0–100 heuristic dimensions with priority bands, confidence and reason/blocking vectors. Never label heuristic scores as calibrated P(hire).

## 6. Outbound

Before any irreversible action require all applicable:

- market resolution;
- send-critical evidence;
- freshness;
- channel policy;
- lane assets;
- claims QA;
- suppression clear;
- idempotency clear;
- explicit user authorization.

Default: `send_allowed = 0`, outbound CLOSED.

## 7. Persistence

Every material run updates the relevant constrained DB/control-plane/graph/observability state. Repository docs change only when system contracts, architecture, migrations or durable state pointers materially change.

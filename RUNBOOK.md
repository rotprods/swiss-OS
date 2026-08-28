# RUNBOOK — HARDENED OPERATOR EXECUTION

This is the concise operator path. The full transaction contract is `docs/operations/WAVE_OPERATING_PROTOCOL.md`; production eligibility is `docs/operations/PRODUCTION_READINESS_GAUNTLET.md`.

## 0. Read order

Before material work:

```text
WAVE_OPERATING_PROTOCOL.md
→ GOAL.md
→ STATE.md
→ AGENTS.md
→ OPERATING_RULES.md
→ live authority reconciliation
```

Do not copy mutable state into this runbook.

## 1. Declare execution mode

Every material wave runs as exactly one:

```text
AUTHORITATIVE_WRITE
READ_ONLY_RESEARCH
DEGRADED_CANARY
RECOVERY_RECONCILE
```

If any required authority layer is unavailable or contradictory, canonical promotion is prohibited.

## 2. Authority bootstrap

Reconstruct at minimum:

- release / goal / checkpoint;
- authority parent + epoch;
- physical and active canonical sets;
- aliases/superseded lineage;
- constrained DB integrity/FK state;
- DB↔Sheets PK reconciliation when available;
- Graph/Intelligence denominators;
- open P0 issues / SLO breaches;
- scheduler + TTL refresh state;
- `send_allowed` / outbound state;
- GitHub `STATE.md` and Library recovery pointer.

Abort promotion when lineage, PK sets, checkpoint, Graph/Intelligence or critical invariants disagree.

## 3. Select bounded work

Use scheduler state and G-0001 value to choose one bounded task/batch.

Do not create an unbounded “mega task”. A batch has a declared ceiling and terminalizes when complete.

## 4. Discover / verify / resolve

Prefer exact current first-party evidence.

Every candidate/fact follows the relevant subset of:

```text
DISCOVER
→ VERIFY SOURCE SCOPE
→ NORMALIZE
→ DEDUPE / ALIAS / GROUP RESOLUTION
→ STAGE
→ CANARY
→ VALIDATE
```

Historical/cache/index sources remain discovery-only until current scope is proven.

## 5. Canonical commit chain

For an authoritative mutation:

```text
validated canary
→ constrained DB transaction
→ integrity/FK/UNIQUE/CHECK
→ idempotency replay
→ logical restore check
→ Sheets mirror by PK
→ exact DB↔Sheets reconciliation
→ Intelligence sync
→ Operational Graph sync
→ epoch/snapshot update
→ QA / invariants / SLO
→ metrics / health
→ scheduler / issues
→ transitions / run log
→ goal/checkpoint if warranted
→ GitHub state/handoff
→ Library/Drive recovery persistence
→ final reconciliation
```

From DB commit onward this is one logical promotion transaction. A missing required step means authority does not advance.

Never perform:

```text
discover → append → declare success
```

## 6. QA dimensions

Track independently:

```text
resolution_pct
known_value_pct
evidence_coverage_pct
freshness_pct
conflict_free_pct
send_critical_pct
```

Typed unknown may count as resolved only with valid Search Proof. It never counts as a known value.

Run the applicable `PRODUCTION_READINESS_GAUNTLET.md` gates before production continuation or checkpoint promotion.

## 7. Graph rule

Every material wave declares:

```text
GRAPH_IMPACT = NONE | META | OPERATIONAL | BOTH
```

Operational mutations update required PK-keyed nodes/edges in the same authoritative wave. Meta/project graph changes never substitute for the operational graph.

## 8. Scoring

Use declared 0–100 heuristic dimensions with confidence, reason and blocker vectors. Never present scores as calibrated hiring probabilities.

## 9. Outbound

Default:

```text
OUTBOUND = CLOSED
send_allowed = 0
```

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

Research, drafting or market mapping never implies authorization.

## 10. Persistence / closure

Every material wave updates all affected constrained/control-plane/graph/observability state before authoritative close.

Recovery artifacts are persisted to Library and Drive when available/required and labeled `AUTHORITATIVE` vs `CANARY`.

Every material wave closes as exactly one:

```text
COMPLETE_AUTHORITY
COMPLETE_READ_ONLY
SAFE_STOP_CANARY
BLOCKED_P0
SUPERSEDED
```

If a connector/outage causes `SAFE_STOP_CANARY`, the next write-capable execution begins with `/wave recover` / `RECOVERY_RECONCILE`, not new blind allocation.
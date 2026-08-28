# SWITZERLAND_JOB_OS — SYSTEM AUDIT & PRODUCTION PLAN

Date: **2026-08-28**  
Audit wave: **WAVE-20260828-SYSTEM-PERFECTION-01**  
Mode: **RECOVERY_RECONCILE → DEGRADED_CANARY**  
Graph impact: **META** for this architecture wave; no operational canonical entity mutation is claimed.

## Executive result

The system architecture is coherent, bounded and production-oriented after this audit. The largest internal failure mode found was **state duplication across stable documentation**: `STATE.md` was current while several architectural/agent documents still contained older frontiers/parents. That failure class is now removed and guarded by CI.

The remaining blocker to a fully authoritative production write is **external/runtime capability**: the Google Drive connector is disabled in the current execution session. Therefore this audit cannot truthfully close as `COMPLETE_AUTHORITY` across Drive/Sheets. It closes repository/architecture work as ready while preserving the operational authority frontier unchanged.

No outbound action was performed or authorized.

## Snapshot used by this audit

The current public-safe state pointer declares the last fully synchronized authority as:

```text
entity epoch              HS_ENTITY_EPOCH_2026-08-25_E4
physical HOTELS rows      690
superseded aliases          4
active canonical          686
CP-0750                   686 / 750 ACTIVE
remaining                  64
next authoritative ID     H-0691
Intelligence              686 / 686
Graph V2                  686 / 686
L4                        105 / 686
G-0700 L9                   0 / 2050
OUTBOUND                  CLOSED
send_allowed                0
```

The latest local acceleration canary is V16:

```text
local physical rows                         715
local candidate entities excluding aliases 711
Batch05 exact-detail candidates              25
integrity_check                              ok
FK violations                                 0
ID gaps                                       0
name+city duplicates                          0
non-empty domain duplicates                   0
idempotency replay unintended inserts         0
restore logical differences                   0
external actions                              0
send_allowed                                  0
```

V16 remains **CANARY / NON-AUTHORITATIVE** until live Drive/Sheets and all affected layers reconcile.

## Audit scope

The meta-wave reviewed these system concerns:

1. North Star / goal tree;
2. authority and state precedence;
3. Wave transaction semantics;
4. engine ownership and handoffs;
5. constrained SQLite semantics;
6. entity resolution / alias lineage;
7. evidence scope / provenance;
8. vacancy/housing/people/channel semantics;
9. scheduler / TTL / idempotency;
10. Graph and Intelligence contracts;
11. candidate truth / scoring / rendering boundaries;
12. QA / SLO / observability;
13. Git / CI / public repository safety;
14. recovery / Library / Drive persistence;
15. concurrency and partial-write recovery;
16. agent documentation consistency;
17. production continuation strategy;
18. outbound authorization isolation.

## Mechanisms exercised

### Mission Commander

PASS. G-0001 remains the North Star. Canonical hotel count, intelligence depth and code quality are supporting systems, not final success.

### Authority & Reconciliation Engine

PASS_WITH_DEFERRED_NONCRITICAL for design; runtime write authority BLOCKED by Drive capability in this session.

The system correctly distinguishes authority from V16 canary state and forbids local-count promotion.

### Wave Transaction Engine

PASS. WOP-1.1 defines bounded identity, modes, promotion chain, graph impact, closure states, concurrency and outage semantics.

### Entity Resolution Engine

PASS. Immutable IDs, superseded lineage, active-vs-physical semantics and domain/name+city conflict checks are explicit.

### Evidence Engine

PASS. Exact current detail, current support, historical discovery and reconciliation-required scopes remain distinct. Search-proof semantics protect typed unknowns.

### Scheduler & TTL Engine

PASS with future integration depth remaining intentionally bounded. The executable core enforces scope/type/freshness anti-join and does not require a distributed queue at current scale.

### Data / SQLite Engine

PASS. PK/FK/UNIQUE/CHECK boundaries exist. Restore semantics were previously hardened from binary-SHA equality to logical bidirectional equivalence.

### Operational Graph Engine

PASS at contract/state level. Authoritative entity/evidence/task mutations must update operational graph representations in the same wave. The public repository deliberately does not duplicate the full private operational graph payload.

### Project Memory Meta Graph Engine

PASS after this audit. System architecture now explicitly separates meta graph from operational graph.

### Intelligence Engine

PASS at current authority contract. Intelligence denominator may not diverge from active canonical denominator; L4/L9 promotion is evidence-earned rather than inherited from identity creation.

### QA / Governance Engine

PASS after hardening. A reusable `PRODUCTION_READINESS_GAUNTLET.md` now challenges authority, data, evidence, scheduler, Graph, Intelligence, candidate truth, security, concurrency and persistence.

### Observability Engine

PASS. Authoritative and canary counters are explicitly separate and every material wave must emit closure state + next bottleneck.

### Recovery & Persistence Engine

PASS for GitHub + Library. Drive replication is blocked by the current connector outage and must be repaired in the recovery wave.

### Git / CI Engine

PASS after hardening. CI now validates public-repo boundaries, stable-document state drift, unit tests and manifest semantics.

### Security / Privacy / Outbound Gate

PASS. Public repo excludes operational SQLite/PII/private candidate data. Default outbound remains CLOSED with `send_allowed = 0`.

## Findings and iterations

### F-01 — Stable-document state drift

**Severity before fix:** P1 architectural / potential P0 during stale-agent writes.

Observed examples before this audit:

- `SYSTEM_MAP.md` still embedded an older canonical count and old scheduler frontier;
- earlier iterations had already found stale state in README, AGENTS and GOAL;
- historical migration/reconciliation docs contained “next parent” language that could be misread as current authority.

**Fix:**

- `STATE.md` remains the only mutable repository state pointer;
- README/GOAL/AGENTS/RUNBOOK/SYSTEM_MAP/AUTHORITY_MODEL/EXECUTABLE_CORE are state-free contracts;
- historical docs receive explicit historical/not-authority banners;
- `scripts/system_contract_guard.py` makes regression a CI failure.

**Post-fix state:** PASS.

### F-02 — Engine taxonomy existed conceptually but not as one canonical interface registry

**Severity:** P1 maintainability/agent coordination.

**Fix:** `docs/architecture/ENGINE_REGISTRY.md` defines 22 bounded engines with purpose, inputs, outputs, persistence, graph impact, invariants and fail-closed semantics.

This removes role ambiguity without introducing runtime microservices.

**Post-fix state:** PASS.

### F-03 — “Full-system/perfect” requests lacked one reusable adversarial readiness checklist

**Severity:** P1 QA consistency.

**Fix:** `docs/operations/PRODUCTION_READINESS_GAUNTLET.md` defines G00–G20 and adversarial questions.

**Post-fix state:** PASS.

### F-04 — CI guarded secrets/tests but not architecture drift

**Severity:** P1 regression risk.

**Fix:** CI adds `scripts/system_contract_guard.py`; `repo_guard.py` now requires the WOP, engine registry, production gauntlet and restore tests.

**Post-fix state:** PASS pending CI confirmation on this PR.

### F-05 — System map underrepresented Library, two-graph model and Wave Engine

**Severity:** P2 architecture clarity.

**Fix:** state-free System Map now represents Mission → Authority → Wave → Engines → DB/Sheets/Intelligence/Operational Graph → QA → Observability → GitHub/Meta Graph/Library.

**Post-fix state:** PASS.

### F-06 — Authority model did not fully encode canary eligibility / Library / local workspace semantics

**Severity:** P1 recovery ambiguity.

**Fix:** authority eligibility now requires affected DB/Sheets/Graph/Intelligence/governance reconciliation; Library is cold recovery, local Git is cache, CI does not prove runtime sync.

**Post-fix state:** PASS.

### F-07 — Drive/Sheets connector unavailable

**Severity:** P0 for authoritative writes in this execution environment; not a design defect.

**Fix in this wave:** fail closed. Do not promote V16. Persist all non-Drive work to GitHub/Library. The next write-capable wave begins `RECOVERY_RECONCILE`.

**Post-fix state:** BLOCKED externally until connector availability returns.

## Architecture scorecard

Scores are engineering-readiness heuristics, not probabilities.

| Vertical | Before audit | After audit | Residual |
|---|---:|---:|---|
| North Star / goal integrity | 9.5 | 9.8 | live business outcome still external |
| Authority / state model | 9.0 | 9.8 | Drive runtime unavailable now |
| Wave transaction model | 9.5 | 9.8 | needs next live authority rehearsal |
| Engine ownership / interfaces | 7.5 | 9.8 | no need for extra engines currently |
| Documentation / agent consistency | 7.0 | 9.8 | CI must remain green |
| SQLite/data constraints | 9.2 | 9.5 | full private DB not duplicated publicly by design |
| Entity resolution | 9.0 | 9.3 | ongoing live edge cases expected |
| Evidence semantics | 9.2 | 9.5 | ongoing source freshness work |
| Scheduler / TTL | 8.7 | 9.1 | deeper runtime scheduler features only when needed |
| Operational Graph | 8.8 | 9.3 | live cross-plane rehearsal required after Drive recovery |
| Intelligence | 8.6 | 9.0 | depth backlog is product work, not architecture gap |
| QA / Governance | 8.8 | 9.8 | production gauntlet now canonical |
| Observability | 8.8 | 9.4 | depends on live control-plane availability |
| Git / CI | 8.8 | 9.8 | PR CI must pass |
| Recovery / Library | 9.0 | 9.5 | Drive cold copy pending connector recovery |
| Security / privacy | 9.5 | 9.7 | continuous review remains required |
| Outbound isolation | 10.0 | 10.0 | hard lock retained |
| Concurrency / stale-parent safety | 9.0 | 9.6 | next live recovery wave is proof rehearsal |
| Operator UX / runbook | 8.2 | 9.7 | `/wave` remains the canonical operator abstraction |
| Cross-plane production runtime | 6.5 | 6.5 | blocked only by Drive capability in current session |

### Overall interpretation

**System design / governance:** production-ready.  
**Repository / executable core:** production-ready after PR CI passes.  
**Cross-plane authoritative writes:** temporarily blocked until Drive/Sheets can be read/written and reconciled.  
**Read-only research / canary production:** safe to continue under WOP.

## Why this is not overengineered

The audit explicitly rejects adding infrastructure without a measured bottleneck.

Not required now:

- Kubernetes;
- Terraform;
- distributed queues;
- microservices;
- always-on background agents;
- Postgres migration solely for fashion;
- a second workflow platform;
- duplicated operational DB data in GitHub;
- automated outbound.

The current architecture uses the minimum mechanisms that materially prevent observed failures: SQLite constraints, WOP transaction semantics, Git/CI, control-plane mirrors, graph contracts and recovery bundles.

## Canonical production protocol after this audit

```text
/wave
→ reconstruct live authority
→ scan P0/SLO/TTL/drift
→ choose scheduler task
→ identify affected engines
→ declare mode + graph impact + batch ceiling
→ execute bounded work
→ stage/canary
→ run applicable production gauntlet
→ constrained commit
→ Sheets PK mirror
→ Intelligence
→ Operational Graph
→ metrics/health/SLO
→ scheduler/issues/checkpoints
→ transitions/run log
→ GitHub STATE/handoff
→ Library + Drive recovery
→ final reconciliation
→ closure state
```

## Immediate production continuation plan

### Wave P0 — Drive recovery / V16 authority reconciliation

When Drive capability returns:

1. enter `RECOVERY_RECONCILE`;
2. re-read live GOAL_STATE, CHECKPOINT_REGISTRY, scheduler, issues/SLO, active manifest and HOTELS tail;
3. verify whether another agent advanced the parent/frontier;
4. anti-join all V16 provisional candidates by ID/name+city/domain/alias/group/task key;
5. discard/reallocate provisional IDs if the live frontier moved;
6. rebuild V16-equivalent canary from the actual live authority parent;
7. rerun integrity/FK/duplicates/replay/logical-restore gauntlet;
8. commit constrained DB;
9. mirror Sheets by PK;
10. sync Intelligence and Operational Graph exactly once per active PK;
11. create next entity/snapshot epoch;
12. update metrics, health, SLO, scheduler, issues, checkpoint and transitions;
13. update `STATE.md` only after the live layers agree;
14. persist authoritative recovery artifacts to Library and Drive;
15. close `COMPLETE_AUTHORITY` only if final reconciliation is exact.

### Wave P1 — Complete CP-0750 without blind volume chasing

After the recovery wave, continue bounded current-detail discovery only as needed to close the checkpoint quality gates.

Do not let CP-0750 delay higher-value vacancy/careers/candidate work when those paths are unblocked.

### Wave P1 — Acquisition readiness in parallel

Prioritize:

- current careers/vacancy resolution for strongest properties;
- direct property/group recruitment routes;
- people/channel resolution where useful;
- candidate lane completion as user-confirmed facts become available;
- deterministic application assets;
- fit/priority ranking from evidence-backed features.

The system should move from “more hotels” to “higher expected verified-offer value” as soon as market coverage is sufficient.

### Outbound remains separate

No wave automatically sends applications. Outbound activation requires an explicit future authorization event and its independent gates.

## Production Definition of Done for the OS itself

The OS is considered architecturally ready when:

- WOP is canonical and followed;
- engine responsibilities are explicit;
- stable docs cannot drift silently;
- constrained data semantics are executable;
- restore/replay/idempotency gates exist;
- authority vs canary is mechanically/policy separated;
- Graph and Intelligence are promotion dependencies;
- recovery artifacts survive context loss;
- CI protects public/security + architecture contracts;
- no applicable internal P0 remains;
- missing external capability causes fail-closed degraded mode, not false success.

This audit reaches that architectural DoD.

## Residual blockers / accepted risks

### External blocker

`Google Drive` connector is disabled in the current session. Therefore:

- this audit `.md` cannot be uploaded to Drive in this session;
- Drive/Sheets/meta-graph/control-plane writes cannot be truthfully claimed;
- V16 cannot be canonically promoted;
- the next authoritative wave must begin with recovery reconciliation.

### Accepted design boundaries

- no background daemon exists;
- no local Git clone in ChatGPT is shared authority;
- the public repo does not contain private operational DB/PII;
- live external evidence can change and requires TTL/search-proof discipline.

These are intentional boundaries, not hidden defects.

## Closure

Repository/architecture result target after CI: **PASS**.  
Cross-plane result in this session: **SAFE_STOP_CANARY** due Drive connector unavailability.  
Canonical operational counts: **unchanged** by this meta-wave.  
Outbound: **CLOSED**.

Next production entrypoint: **`/wave recover` when Drive capability is available; otherwise `/wave` may continue safe read-only research/canary work.**

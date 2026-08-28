# META EXECUTION PROTOCOL — SWITZERLAND_JOB_OS

Version: **MEP-2.0**  
Status: **CANONICAL CROSS-ENGINE EXECUTION CONTRACT**

## 1. Purpose

MEP-2.0 defines how SWITZERLAND_JOB_OS continues making safe progress across changing tool/capability conditions without confusing activity with authority.

It wraps the existing engines and `WAVE_OPERATING_PROTOCOL.md`; it is **not** a new daemon, microservice, or authority plane.

The protocol exists to prevent four recurring failure modes:

1. an agent stops because one preferred connector/path is unavailable even though productive safe alternatives exist;
2. an agent continues on a stale parent after another agent advanced `main` or operational authority;
3. a canary/cache/staging result is promoted merely because it is locally valid;
4. architecture, Graph, Drive, Library, CI and operational state diverge after a material wave.

## 2. North Star and hard gates

Every cycle optimizes G-0001, subject to the current dominant prerequisite.

For the hotel-universe phase:

```text
CRM_UNIVERSE_COMPLETE = TRUE
```

is a prerequisite before outbound eligibility may even be evaluated.

Default irreversible-action state remains:

```text
OUTBOUND = CLOSED
send_allowed = 0
```

MEP never converts research permission into send permission.

When CRM-universe completion eventually passes, control returns to the global North-Star scheduler. CRM completion never itself authorizes outbound.

## 3. The COLETTE loop

The canonical continuous execution loop is:

```text
C — COLLECT authority, ancestry, state and capabilities
O — OBSERVE drift, blockers, SLO/TTL debt and concurrent changes
L — LOCATE the current highest-value safe bottleneck
E — EXECUTE one bounded WAVE through the affected engines
T — TEST with invariants, gauntlets, replay/restore and adversarial review
T — TRANSACT/PERSIST every affected durable plane that is actually available
E — EVOLVE state, record learning, choose NEXT and immediately repeat when safe
```

A chat message is not a COLETTE cycle. A cycle is a bounded operational execution envelope.

Completing one wave does not mean the activation should stop. The activation computes `NEXT` under `NEXT_POINTER_PROTOCOL.md` and immediately continues into the next safe cycle while the runtime remains available.

## 4. No-idle rule

A recoverable capability failure MUST NOT by itself end productive execution.

When the preferred path is blocked, the agent computes the best allowed fallback that still reduces the current bottleneck.

Examples:

```text
native Sheets writer unavailable
→ Drive-mount authority/read reconciliation
→ source acquisition
→ source-scope reconciliation
→ mass staging
→ exact-current refresh
→ QA / recovery persistence
```

```text
discover.swiss API key unavailable
→ coherent member-directory evidence collection
→ historical-cache anti-join discovery only
→ exact-detail refresh of known missing identities
→ code/QA hardening only when it closes an observed blocker
```

```text
Drive connector unavailable but authenticated Drive mount available
→ rehydrate Drive through mounted external-gdrive surface
→ do not claim native Sheet mutation
```

The no-idle rule does **not** permit unsafe improvisation. If no route can reduce the bottleneck without violating authority, privacy, evidence, provider controls, or outbound rules, the cycle closes `BLOCKED_P0`.

## 5. Ancestry reconstruction is mandatory

Before every material cycle:

1. read current GitHub `main` HEAD;
2. read `STATE.md` from that HEAD;
3. read the latest relevant protocol versions;
4. reconcile live Drive/Sheets/DB/Library authority where available;
5. inspect current authority-blocking P0s and active scheduler work;
6. compare the last known parent with current ancestry;
7. absorb non-conflicting concurrent progress instead of overwriting it.

If another agent advanced a shared layer, transition to `RECOVERY_RECONCILE` before allocating IDs, changing checkpoint state, or committing operational authority.

No agent may assume that the last chat response is still the current system frontier.

## 6. Capability matrix

Each cycle classifies capabilities/state independently. Machine input uses strict JSON types; strings such as `"false"` are invalid substitutes for booleans.

Planner keys include:

```text
authority_reconstructable
ancestry_current
authority_blocking_p0

constrained_db_read
constrained_db_write
native_sheets_read
native_sheets_write
drive_mount_read
drive_create_only_write

github_read
github_write
github_ci
library_read
library_write
web_research

discover_swiss_subscription
discover_capture_valid
member_directory_evidence
member_directory_manifest_complete
source_scope_reconciled
frozen_candidate
ingest_records_ready

operational_graph_write
intelligence_write
observability_write

unresolved_source_records
reconcile_required
exact_current_refresh_backlog
crm_universe_complete
promotion_ready
scheduler_task_available
```

Count fields are non-negative integers. Capability booleans are JSON booleans.

Capability state is operational state and belongs in cycle/run state, not hard-coded stable docs.

A missing capability changes route/mode; it does not rewrite truth.

## 7. Deterministic route lattice

### R0 — AUTHORITY_RECOVERY

Use when authority/ancestry is ambiguous, a parent moved, a partial write is suspected, or a P0 explicitly blocks authority reconstruction/promotion.

Mode:

```text
RECOVERY_RECONCILE
```

No new canonical allocation.

### R1 — STRUCTURED_SOURCE_CAPTURE

Preferred bulk acquisition route while CRM universe is incomplete and discover.swiss is usable.

```text
discover.swiss / dsod-hs
→ DSA-1.0 capture validation
```

Capture remains non-authoritative.

### R2 — MEMBER_DIRECTORY_MANIFEST

Collect one coherent member-directory evidence set when the selected source snapshot is not yet complete.

Historical page/cache observations remain discovery only and may not set `coverage_complete=true`.

### R3 — SOURCE_SCOPE_RECONCILIATION

When API capture + complete directory evidence exist:

```text
SSR-1.0
EXACT_HSID
→ EXACT_DETAIL_URL
→ EXACT_NAME_CITY
```

Unexplained deltas fail closed.

### R4 — FROZEN_CANDIDATE_EXPORT

When SSR is `EXACT | EXPLAINED` with zero unexplained/conflicts:

```text
FROZEN_CANDIDATE
→ candidate_export
→ CMI-1.0 records
```

Still:

```text
H_ID_ALLOCATIONS = 0
AUTHORITY_ADVANCED = FALSE
```

### R5 — MASS_INGEST_STAGING

Run deterministic anti-join/classification/scheduler on the constrained staging backend.

Allowed outputs include:

```text
EXISTING_CANONICAL
ALIAS_CANDIDATE
NEW_IDENTITY_CANDIDATE
RECONCILE_REQUIRED
EXCLUSION_REVIEW
```

Staging never reserves an H-ID.

### R6 — EXACT_CURRENT_REFRESH

Resolve identities/claims that still require current evidence before terminal mapping.

Prefer exact current first-party entity evidence. Historical-cache discovery is a candidate generator, never promotion proof.

If current-evidence backlog remains and compliant web research is available, this route precedes terminal mapping.

### R7 — ENTITY_RESOLUTION / TERMINAL_MAPPING

Run after required current-evidence backlog is cleared for the affected records.

Every frozen source record must terminate exactly once as:

```text
ACTIVE_CANONICAL
ALIAS_TO_CANONICAL
EXCLUDED_WITH_REASON
```

with:

```text
RECONCILE_REQUIRED = 0
UNMAPPED = 0
```

### R8 — AUTHORITATIVE_PROMOTION

Only when every affected authority plane is available and all applicable WOP/PRG gates pass:

```text
constrained DB
→ HOTELS_MASTER / CRM mirror
→ Intelligence
→ Operational Graph
→ snapshot/entity epoch
→ observability
→ scheduler/issues/checkpoints
→ transitions/run log
→ GitHub STATE/handoff
→ Drive/Library recovery
→ final exact reconciliation
```

Only this route may set:

```text
authority_advance_allowed = TRUE
canonical_id_allocation_allowed = TRUE
```

MEP itself still keeps:

```text
outbound_allowed = FALSE
```

### R9 — ENGINEERING_QA / RECOVERY

If operational routes are temporarily blocked, perform engineering work only when it closes measured execution/integrity debt:

- invariant/test coverage;
- deterministic adapters;
- recovery manifests;
- source-scope contracts;
- stale-state guards;
- Graph/authority reconciliation tools.

Do not build infrastructure merely to remain busy.

### R10 — NEXT_GOAL_SCHEDULER

Once `CRM_UNIVERSE_COMPLETE = TRUE`, return control to the global North-Star scheduler for the next prerequisite/task instead of idling or assuming outreach should begin.

The global scheduler may dispatch candidate readiness, intelligence, asset, vacancy, housing, people/channel, scoring or later engines according to the actual state.

## 8. Route selection objective

Choose the route with the highest expected reduction in the current hard bottleneck subject to safety.

Conceptually:

```text
priority(route)
=
blocked_north_star_value_released
× evidence_quality
× dependency_unlock
× recoverability
÷ execution_cost
```

This is a decision heuristic, not a calibrated probability.

Tie-break order during incomplete CRM universe:

1. closes authority-blocking P0 / restores authority;
2. unlocks frozen CRM universe;
3. removes many unresolved source records at once;
4. creates deterministic reusable throughput;
5. improves QA against an observed failure;
6. deep enrichment of already-known hotels.

During CRM universe completion, deep L4/L9 enrichment loses to source-universe closure unless it directly unblocks a gate.

## 9. Planner output contract

Every meta-cycle emits a deterministic decision record containing at minimum:

```text
execution_mode
selected_route
reason
hard_blocks
capabilities_used
graph_impact
authority_advance_allowed
canonical_id_allocation_allowed
outbound_allowed
next_fallback_routes
```

Default:

```text
authority_advance_allowed = FALSE
canonical_id_allocation_allowed = FALSE
outbound_allowed = FALSE
```

Only `AUTHORITATIVE_PROMOTION` may set the first two true. No MEP route grants outbound.

The durable continuation record is a separate fail-closed `NEXT` pointer under NPP-1.0; every persisted NEXT keeps **all three** permission flags false and requires revalidation on resume.

## 10. Failure substitution table

| Failure | Automatic safe substitution |
|---|---|
| Native Sheets write unavailable | Continue read/recovery/source/staging/QA; no authority promotion |
| Drive direct connector unavailable | Try authenticated Drive mount; distinguish read/create-only from in-place mutation |
| discover.swiss key unavailable | Build/reconcile directory evidence + exact-current refresh; never invent API output |
| Member-directory pagination unstable | Use snapshot-scoped source identity; never page number as record identity |
| Web cache stale | Discovery/anti-join only; exact-current refresh before promotion |
| Git CLI unavailable | Use GitHub connector as VCS actuator |
| Local filesystem ephemeral | Persist durable artifacts to Library/Drive and GitHub public-safe state |
| Another agent advanced `main` | Reconstruct ancestry and rebase/recreate wave from new HEAD |
| Canary valid but one authority plane unavailable | `SAFE_STOP_CANARY`; preserve artifacts; continue another safe route |
| CI fails | Fix/revert; never merge through failure |
| No safe productive route | `BLOCKED_P0`; record exact blocker, no fabricated progress |

## 11. Meta-PR concatenation

System-definition work is serially chained:

```text
branch from current main
→ implementation
→ tests
→ PR
→ CI
→ adversarial review
→ merge
→ reread main
→ reconstruct ancestry/authority/capabilities
→ persist NEXT
→ only then branch the next meta-PR from fresh main
```

Do not stack multiple dependent PRs from a stale parent merely to look continuous.

## 12. Persistence after every material cycle

Persist according to affected scope.

### GitHub

When contracts/code/public-safe state changed:

```text
branch
→ implementation
→ tests
→ PR
→ CI
→ adversarial diff review
→ merge
```

### Drive

When available:

- project docs/handoffs;
- control-plane mirror;
- recovery artifacts;
- Graph/meta-memory projections.

A create-only Drive path is not equivalent to native in-place Sheets mutation.

### ChatGPT Library

Persist latest recovery/NEXT pointers for material cycles. Library is cold recovery, never operational authority.

### Meta graph

Material decisions/waves/artifacts/blockers require META graph lineage. Operational entity mutation additionally requires OPERATIONAL graph synchronization before authority closes.

## 13. Context-compaction survival

A cycle must leave enough durable state that a new agent/chat can reconstruct the project without relying on conversation memory.

Minimum persistent pointers:

```text
STATE.md
latest authority manifest / constrained parent
LATEST_RECOVERY
LATEST_CRM_UNIVERSE (when applicable)
NEXT
latest meta-cycle handoff
current authority-blocking P0s
protocol versions
GitHub main SHA
```

Any chat-specific reasoning that materially changes execution must become a durable decision/contract/handoff before cycle closure.

## 14. Adversarial evolution loop

After each meaningful wave, ask:

1. What fact did we believe that is now contradicted by stronger evidence?
2. Which layer could silently drift from another?
3. Which capability failure still causes unnecessary idle time?
4. Which manual reconciliation can safely become deterministic code?
5. Are we optimizing a proxy instead of the North Star?
6. Did concurrent work move our parent?
7. Can this artifact survive context loss?
8. Could staging be mistaken for authority?
9. Did we create a new unresolved ambiguity while closing another?
10. What is now the single highest-value bottleneck?

Material answers update the relevant protocol/test/issue rather than remaining only in chat.

## 15. Continuous execution semantics

MEP supports repeated cycles but never falsely claims an always-on daemon.

Inside one available runtime activation:

```text
wave → persist → NEXT → immediate next safe cycle
```

The activation keeps chaining while safe work and runtime capacity remain.

An external scheduler/automation, when actually configured, is only a **re-entry mechanism after the runtime ends**. Each scheduled activation reconstructs ancestry/authority from durable state before acting. Platform scheduling limits do not change OS semantics.

## 16. Stop / escalation conditions

A cycle may stop without selecting a fallback only when one of these is true:

```text
P0 authority ambiguity with no safe read/recovery path
irreversible action requires explicit user authorization
provider/legal/access control prevents further compliant work
all safe routes have zero expected bottleneck reduction
required private fact must come from the user
runtime/tool limits force activation closure after NEXT is durably persisted
```

The cycle records the blocker/pointer durably and never fabricates completion.

## 17. Relationship to existing contracts

```text
MEP-2.0 — choose the next safe productive route and preserve continuity
  ↓
NPP-1.0 — persist fail-closed NEXT across runtime/context boundaries
  ↓
WOP-1.1 — execute one material wave transactionally
  ↓
ENGINE_REGISTRY — dispatch responsibilities
  ↓
CUP / DSA / SSR / CMI — domain-specific CRM-universe gates
  ↓
PRG — adversarial production-readiness QA
  ↓
STATE / manifests / Graph / Drive / Library — durable truth and recovery
```

MEP does not lower any WOP, CUP, SSR, PRG, privacy, evidence or outbound gate.

## 18. Definition of success

MEP-2.0 is working when:

- concurrent progress is absorbed rather than overwritten;
- recoverable capability failures trigger safe alternate routes automatically;
- one completed wave automatically produces NEXT and chains the next safe wave in the same activation;
- meta-PRs are serially reconstructed from fresh `main`;
- no canary/cache/staging value is promoted by convenience;
- every material cycle leaves durable recovery state;
- agents converge on the same current bottleneck after context loss;
- CRM-universe production continues toward complete frozen-source mapping;
- after CRM completion the system returns to the global North-Star scheduler;
- outbound remains independently locked until all prerequisites and explicit authorization pass.

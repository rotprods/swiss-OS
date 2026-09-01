# AGENT AUTORESEARCH PROGRAM — GRAPH-REFACTOR-V2

Status: IMPLEMENTED_CONTRACT / ACTIVATION_GATED
Source inspiration: karpathy/autoresearch experiment loop. Adapted for a multi-agent production system with authority, security, recovery and multi-objective quality gates.

## Prime rule

Every material agent iteration MUST execute under `GRAPH-REFACTOR-V2` and MUST have durable identity:

- project_id
- agent_id
- session_id
- workstream_id
- objective_id
- correlation_id
- goal_ids[]
- plan_id
- task_id
- claim_id
- fencing_token
- worktree
- branch
- PR when one exists
- base_main_sha
- authority_ceiling

An agent without these fields is not authorized for material mutation.

## Autoresearch adaptation

Autoresearch uses a fixed baseline, one bounded experimental change, objective evaluation, and keep/discard. SWISS-OS adopts that pattern but adds hard invariants and durable graph/evidence semantics.

```text
LIVE TRUTH / BASELINE
        ↓
GRAPH-REFACTOR-V2 PREFLIGHT
        ↓
REGISTER AGENT + SESSION + CLAIM
        ↓
SELECT GOAL / PLAN / TASK
        ↓
CREATE/REUSE ISOLATED WORKTREE + BRANCH
        ↓
FORM ONE TESTABLE HYPOTHESIS
        ↓
EXECUTE ONE BOUNDED ITERATION
        ↓
RUN FIXED EVALUATION SUITE
        ↓
COMPARE BASELINE ↔ CANDIDATE
        ↓
KEEP | DISCARD | CRASH | BLOCKED
        ↓
PERSIST EXPERIMENT RECEIPT + GRAPH DELTA
        ↓
UPDATE PR / TASK / CHECKPOINT / HANDOFF
        ↓
SELECT NEXT SAFE ITERATION
```

## Keep/discard law

KEEP only when:

1. all applicable hard QA/security/authority gates pass;
2. no protected metric regresses beyond declared tolerance;
3. at least one declared metric materially improves; OR complexity is reduced without material metric regression;
4. the result remains recoverable and attributable to one agent/session/claim/task/worktree/branch.

DISCARD when the candidate does not beat the baseline, introduces protected regression, fails tests, or increases complexity without justified gain.

CRASH when execution itself fails. Revert experimental code, but persist the crash evidence.

BLOCKED when authority, human approval, credentials, provider state or another genuine dependency prevents valid evaluation.

## Experiments are append-only knowledge

Code from a discarded experiment may be reset/reverted. Its experiment receipt MUST NOT disappear.

Persist public-safe records for:

- hypothesis;
- baseline metrics;
- candidate metrics;
- exact evaluation suite;
- result;
- changed paths;
- reason;
- graph delta;
- commit/PR refs when applicable;
- failure family when discarded/crashed.

Never persist PII/secrets merely to make an experiment reproducible. Use private authority refs/hashes where needed.

## Metric model

No universal single metric exists for SWISS-OS. Each experiment declares its metric vector before execution.

Typical protected metrics:

- critical_integrity_errors = 0
- unsupported_external_claims = 0
- duplicate_external_actions = 0
- claim_collisions = 0
- DB↔control-plane authority drift = 0
- recovery violations = 0
- secret/PII leaks = 0

Typical optimization metrics:

- zero-context recovery time ↓
- unresolved graph contradictions ↓
- test coverage ↑
- deterministic replay coverage ↑
- task throughput ↑
- source reconciliation rate ↑
- positive employer-response rate ↑ once acquisition is authorized
- complexity / LOC / dependency burden ↓ when behavior is preserved

A metric must never be called a hiring probability unless it is actually calibrated as one.

## Fixed evaluation suites

Comparability requires that iterations in the same experiment series use the same declared evaluation suite. Changing the evaluator creates a new experiment series/baseline.

Examples:

### Coordination series
`repo_guard + contract_guard + deterministic_rebuild + context_survival + death_drill + unit_tests`

### Candidate asset series
`claim_provenance + text_extraction + ATS + visual_QA + human_approval_gate`

### Market/entity series
`source_scope + entity_resolution + duplicate_scan + evidence + DB/Sheet reconciliation + restore`

### Acquisition series
`candidate_gate + claim_gate + freshness + channel_policy + suppression + idempotency + explicit_authorization`

## Worktree / PR runtime graph

Every active work item must be graph-queryable as:

```text
Agent
  └─ EXECUTES → Session
       ├─ OWNS → Claim[fencing_token]
       ├─ EXECUTES → Workstream
       └─ OPERATES_IN → Worktree
                         └─ CHECKS_OUT → Branch
                                            └─ PROPOSED_BY → PR

Task → CONTRIBUTES_TO → Goal
Task → PART_OF → Plan
Task → TESTED_BY → Experiment
Experiment → MODIFIES → Files
Experiment → VERIFIED_BY → Tests/Evidence
Experiment → RESULTS_IN → KEEP|DISCARD|CRASH|BLOCKED
```

## Death-safe iteration boundary

An iteration is not allowed to start the next mutation until the current iteration has persisted enough state that a zero-context agent can recover:

- exact main/base SHA;
- agent/session/claim/fencing;
- goal/plan/task;
- worktree/branch/PR;
- hypothesis;
- current baseline;
- tests already run;
- result or current blocker;
- next safe action.

This is the heartbeat boundary. An agent may die after any heartbeat without taking the workstream context with it.

## Agent death / takeover

If heartbeat/lease is stale:

1. replay durable events;
2. verify branch/PR/worktree state;
3. verify provider state for irreversible operations;
4. terminate/supersede the stale claim;
5. acquire a strictly higher fencing token;
6. resume from the latest persisted iteration receipt;
7. never reuse the dead agent's session_id.

## Concurrency

Parallel agents are allowed only for non-overlapping claimed resource/semantic scopes or explicitly coordinated hyperedges. Every agent uses a distinct worktree and branch.

A PR is not ownership. The claim/fencing token is ownership.

## Human gates

Autonomy stops at genuine human boundaries including candidate-facing asset approval, subjective brand/positioning approval when required, legal/financial acceptance decisions, and explicit outbound authorization.

The loop may continue on independent safe work instead of fabricating completion.

## Anti-overengineering

Every kept experiment must answer:

- what measured problem improved?
- by how much?
- what complexity was added?
- what new failure modes appeared?
- would deleting/simplifying code produce equal guarantees?

No experiment is kept merely because it is architecturally interesting.

## Activation gate

The runtime code can be merged independently, but global mandatory activation must occur only after the current coordination lifecycle claim is terminal and the active-claims projection is collision-free. Activation then adds the agent-runtime registry/iteration ledger to canonical coordination projections.

# CONTEXT SURVIVAL PROTOCOL — CSP-1.0

**Project:** SWITZERLAND_JOB_OS  
**Layer:** COS / Project Memory Meta Graph  
**Authority:** coordination and continuity only; never hotel operational authority  
**Principle:** chat/model context is disposable cache. Durable project state must survive arbitrary context compaction, model replacement, process death, tool reset, chat archival, or zero-context re-entry.

## 1. Objective

CSP-1.0 guarantees that a successor model can resume materially correct work without conversational memory.

The survival chain is:

```text
live Git main + durable project events + active claims/fencing
+ STATE/NEXT + ProjectState/ContextPack + latest domain handoff
+ live external authority readback where required
→ deterministic zero-context bootstrap
→ safe continuation
```

Compaction is an optimization, never an authority mechanism.

## 2. Runtime classes

### CHATGPT_HARNESS

The assistant may not be able to request or inspect native context compaction for the current ChatGPT conversation. Do not depend on a live token counter, hidden summaries, memory, or the continued existence of the model instance.

Before a long/tool-heavy phase, after every material merge or durable external-state mutation, and before voluntary chat/archive handoff:

1. persist material knowledge/state/decision/evidence changes;
2. persist or refresh a zero-context NEXT/handoff;
3. refresh the CSP checkpoint over the survival-critical files;
4. verify the checkpoint readback;
5. continue from durable state, not from an unpersisted conversational assumption.

### RESPONSES_API_OR_CODEX_HARNESS

When the runtime exposes OpenAI Responses context management:

- count input tokens before large phases when practical;
- use native context management / compaction before exhaustion;
- compact after major milestones rather than every turn;
- preserve compacted items as opaque continuation state;
- keep the functional system/developer prompt stable across compaction;
- still emit the durable CSP checkpoint because native compaction does not replace project persistence.

Recommended policy for tool-heavy sessions:

```text
< 55% effective context budget       normal execution
55–70%                              checkpoint after every bounded wave
>= 70%                              durable checkpoint, then compact when runtime supports it
unknown token occupancy             behave as >=55% after any long multi-tool phase
```

These percentages are operational heuristics, not model limits.

## 3. Survival-critical surfaces

The current CSP checkpoint MUST content-address at least:

- `GOAL.md`
- `STATE.md`
- `HANDOFF.md`
- `TASKS.md`
- `docs/state/NEXT.json`
- `docs/state/v2/project-state.json`
- `docs/state/v2/context-pack.json`
- the latest explicit domain NEXT pointer selected by the current handoff
- the canonical next-iteration metaprompt

Additional domain artifacts may be pinned as recovery inputs.

## 4. Checkpoint semantics

`docs/state/v2/context-survival.json` is a recovery attestation, not authority.

It contains:

- schema version;
- project/repository;
- generated timestamp;
- ancestry floor SHA;
- authority epoch/revision;
- ProjectState projection revision;
- ContextPack revision and event watermark;
- active claim IDs;
- primary architecture/program route;
- current production route;
- Git blob OID for every survival-critical file;
- safety locks;
- deterministic payload SHA-256.

The ancestry floor need only remain an ancestor of the execution head. A newer descendant is valid only if every content-addressed survival file still matches the checkpoint. Any mismatch means `SURVIVAL_CHECKPOINT_STALE` and requires rebuild before material continuation.

## 5. Mandatory checkpoint triggers

Emit/rebuild the checkpoint when any of these occurs:

- `STATE.md` changes;
- canonical or explicit NEXT changes;
- ProjectState/ContextPack changes;
- active claim/fencing semantics change;
- current handoff changes;
- architecture/program-of-work changes;
- a system-definition PR merges;
- Drive/DB/Graph authority changes;
- a material provider blocker clears or appears;
- a long session is about to compact/hand off;
- a model/session is about to be replaced voluntarily.

A no-op conversational turn does not require a Git commit. A material project change does.

## 6. Zero-context bootstrap

A successor MUST execute in this order:

1. read live `main` and its first-parent ancestry;
2. read `GOAL.md`, `STATE.md`, `HANDOFF.md`, `TASKS.md`;
3. read `docs/state/v2/context-survival.json`;
4. verify all pinned Git blob OIDs;
5. read ProjectState, ContextPack, active claims and latest explicit domain NEXT;
6. compare active claims/fencing against branches/PRs;
7. reread Drive/DB/other authority planes required by the next material action;
8. classify stale/superseded pointers rather than silently trusting them;
9. resume the highest-value safe route.

If the checkpoint is stale but durable sources are available, reconstruct and emit a fresh checkpoint; stale checkpoint state is not a project blocker by itself.

## 7. Dual-track continuation

CSP preserves two separate lanes when both are active:

### Architecture lane
`REPO_ARCHAEOLOGY_GRAPHIFY_V1`

- freeze/inventory;
- issue archaeology;
- non-merged PR archaeology;
- semantic salvage;
- current-main perfection;
- graphify history;
- graph invariants;
- graph-derived STATE/NEXT/TASKS;
- issue/PR/branch cleanup;
- Golden Main gauntlet/attestation.

### Production lane
Resume from the latest explicit domain NEXT on live main. Architecture cleanup must not overwrite or regress a newer production frontier. Production may continue in parallel when claims/resource scopes are disjoint.

## 8. Losslessness rules

Never rely on compaction to preserve an unpersisted fact that would change:

- authority;
- a canonical/entity-resolution decision;
- current task/NEXT;
- active claim/fencing;
- blocker/capability state;
- test/CI outcome;
- recovery input;
- user authorization boundary;
- application/outbound eligibility.

If it matters after model death, it must exist in a durable project plane.

## 9. Safety invariants

CSP can never grant authority.

```text
authority_advance_allowed = false
canonical_id_allocation_allowed = false
canonical_id_reservations_from_staging = 0
authority_from_canary_or_cache = false
CRM_UNIVERSE_COMPLETE = false unless separately proven by CUP gates
OUTBOUND = CLOSED
send_allowed = 0
irreversible_external_actions = 0
```

## 10. Recovery acceptance

A context-death drill passes when a fresh model with only repository/connector access can determine, without chat history:

- North Star;
- live main ancestry;
- authority epoch/revision;
- active claims/fencing;
- current CRM/source frontier;
- current architecture program;
- current production NEXT;
- exact blockers/capabilities;
- recovery inputs;
- hard safety boundaries;
- the next safe executable action.

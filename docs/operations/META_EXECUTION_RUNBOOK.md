# META EXECUTION RUNBOOK

Version: **MER-1.0**  
Protocol: `META_EXECUTION_PROTOCOL.md` / MEP-2.0

## Operator entrypoints

### Plan one deterministic NEXT

```bash
PYTHONPATH=src python -m swiss_os.meta_cli plan \
  examples/meta_planner_input.example.json \
  --out /tmp/NEXT.json
```

### Apply no-progress loop guards before planning

```bash
PYTHONPATH=src python -m swiss_os.meta_cli chained-plan \
  examples/meta_planner_input.example.json \
  examples/meta_journal.example.json \
  --out /tmp/NEXT_CHAINED.json
```

### Execute an activation conceptually

```text
1. reconstruct current main SHA and authority lineage;
2. validate/recover the execution lease;
3. materialize planner context from STATE, capabilities and scheduler;
4. run chained-plan;
5. execute selected route through one bounded WOP wave;
6. append a ProgressEvent with a changed progress token or artifact hash;
7. run the applicable gauntlet;
8. persist state/recovery;
9. recompute NEXT;
10. continue immediately when disposition=NEXT_CONTINUE;
11. exit only with an allowed activation stop reason.
```

## Progress tokens

A progress token must represent a measurable changed state, not a prose claim.

Examples:

```text
api_records_captured:<count>:<records_sha>
directory_manifest_records:<count>:<manifest_sha>
source_scope_unresolved:<count>:<reconciliation_sha>
crm_stage_terminal:<count>:<staging_sha>
exact_refresh_resolved:<count>:<evidence_sha>
entity_conflicts_open:<count>:<resolution_sha>
repo_tests_passed:<count>:<commit_sha>
```

Repeated work with the same progress token and no new artifact hash triggers the loop guard.

## Capability fallback matrix

| Missing capability | Do not do | Safe fallback order |
|---|---|---|
| discover.swiss key | claim API scope or idle | recovery import → directory manifest → cache harvest → exact refresh → adapter engineering |
| native Sheets writer | promote authority or rewrite by row offset | DB/read-only QA → staging → graph/meta engineering → exact refresh → persist recovery |
| Drive mount | claim Drive sync | GitHub + local canary + Library recovery; reconcile when Drive returns |
| web/current source | promote historical cache | process existing exact evidence, entity conflicts, schemas/tests/recovery |
| outbound authorization | send | continue market/candidate readiness; keep send gate closed |

## Issue mutation guard

Before creating an issue:

```text
issue_dedupe_key = project + concern + protocol_version
→ search open and closed issues
→ update/link equivalent issue when found
→ verify max_new_issues budget
→ create at most one new issue per activation by default
```

After issue-create lock:

```text
NO MORE ISSUE CREATION
→ branch/code/test/PR or data route
```

## Lease operation

A write-capable activation must acquire a lease tied to the current main SHA and authority epoch. The lease duration should exceed one normal bounded wave but remain short enough for stale recovery.

Recommended initial policy:

```text
lease_ttl = 20 minutes
renew before irreversible DB commit
release after final persistence
```

A scheduled activation that finds a live foreign lease may reconstruct truth and perform read-only analysis, but cannot compete for writes.

## Schedule

The scheduled activation is a wake-up safety net. Configure a short practical interval with overlap protection. Each activation must chain multiple waves before exit; it must not perform only one wave and wait for the next tick when another safe route is available.

Recommended safety-net cadence while CRM_UNIVERSE_COMPLETE is false:

```text
15 minutes
```

A shorter cadence is permitted only when lease/idempotency and provider-rate limits are verified. A one-minute loop is not justified by current provider and control-plane constraints.

## Activation budget defaults

```text
max_waves_per_activation = 8
max_system_definition_prs = 3
max_new_issues = 1
max_same_action_without_progress = 2
```

Budgets are protection against runaway recursion, not targets. Stop earlier when the next route is unsafe or genuinely blocked.

## Activation closure checklist

- [ ] WOP closure recorded for every wave.
- [ ] Progress token changed or loop guard fired.
- [ ] Applicable tests/gauntlet passed.
- [ ] Authority versus canary explicitly separated.
- [ ] State/recovery artifacts persisted where available.
- [ ] NEXT hash emitted by executable planner.
- [ ] Parent SHA and authority epoch recorded.
- [ ] Outbound remains CLOSED and `send_allowed=0`.
- [ ] If `NEXT_CONTINUE`, continue in the same activation unless budget/runtime prevents it.
- [ ] If exiting for budget/runtime, schedule safety net remains enabled and NEXT contains exact recovery inputs.

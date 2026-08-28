# META EXECUTION RUNBOOK

Version: **MER-1.0**  
Protocol: `META_EXECUTION_PROTOCOL.md` / MEP-2.0

## Deterministic NEXT

```bash
PYTHONPATH=src python -m swiss_os.meta_cli plan \
  examples/meta_planner_input.example.json \
  --out /tmp/NEXT.json
```

## Chained planning with loop guards

```bash
PYTHONPATH=src python -m swiss_os.meta_cli chained-plan \
  examples/meta_planner_input.example.json \
  examples/meta_journal.example.json \
  --out /tmp/NEXT_CHAINED.json
```

## Activation procedure

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

A progress token represents measurable changed state, not prose.

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

| Missing capability | Forbidden response | Safe fallback order |
|---|---|---|
| discover.swiss key | claim API scope or idle | recovery import → directory manifest → cache harvest → exact refresh → adapter engineering |
| native Sheets writer | promote authority or write by row offset | DB/read-only QA → staging → graph/meta engineering → exact refresh → recovery persistence |
| Drive mount | claim Drive sync | GitHub + local canary + Library; reconcile when Drive returns |
| current web source | promote historical cache | process existing exact evidence, conflicts, schemas/tests and recovery |
| outbound authorization | send | continue readiness; keep send gate closed |

## Issue mutation guard

```text
issue_dedupe_key = project + concern + protocol_version
→ search open and closed issues
→ update/link equivalent issue
→ verify max_new_issues budget
→ create at most one new issue per activation by default
```

After issue-create lock:

```text
NO MORE ISSUE CREATION
→ branch/code/test/PR or data route
```

## Lease policy

Recommended initial lease:

```text
lease_ttl = 20 minutes
renew before irreversible DB commit
release after final persistence
```

A scheduled activation that finds a live foreign lease may reconstruct truth and perform read-only analysis, but cannot compete for writes.

## Schedule

The schedule is a recovery safety net. Each activation chains multiple waves before exit.

Recommended cadence while `CRM_UNIVERSE_COMPLETE = FALSE`:

```text
15 minutes
```

A shorter cadence requires verified lease/idempotency and provider-rate-limit safety. A one-minute loop is not justified by current provider/control-plane constraints.

## Activation budget defaults

```text
max_waves_per_activation = 8
max_system_definition_prs = 3
max_new_issues = 1
max_same_action_without_progress = 2
```

## Closure checklist

- [ ] Every WOP wave has one closure state.
- [ ] Progress token changed or loop guard fired.
- [ ] Applicable tests/gauntlet passed.
- [ ] Authority and canary are separated.
- [ ] State/recovery persisted where available.
- [ ] NEXT hash emitted by executable planner.
- [ ] Parent SHA and authority epoch recorded.
- [ ] `OUTBOUND=CLOSED` and `send_allowed=0`.
- [ ] `NEXT_CONTINUE` continues in the same activation unless budget/runtime prevents it.
- [ ] Budget/runtime exit preserves exact recovery inputs.

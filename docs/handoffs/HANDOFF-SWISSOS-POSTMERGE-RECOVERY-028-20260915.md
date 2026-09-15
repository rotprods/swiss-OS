# HANDOFF-SWISSOS-POSTMERGE-RECOVERY-028-20260915

status: ACTIVE_RECOVERY_NOT_MERGE_AUTHORIZED
authority: CONVERGENCE_ORCHESTRATION_AND_LEASE_REPAIR_ONLY_NO_DOMAIN_OR_OUTBOUND_AUTHORITY
project: SWITZERLAND_JOB_OS
repo: rotprods/swiss-OS
chat_id: CHAT-SWISSOS-20260915-POSTMERGE-RECOVERY-001 (logical chat identifier; platform UUID unavailable)
agent_id: AGENT-GPT56SOL-CONVERGENCE-028
session_id: SES-20260915T144337Z-CONVERGENCE-028
workstream_id: WS-CONVERGENCE-POSTMERGE-RECOVERY
objective_id: OBJ-SWISS-MAIN-SINGULARITY
claim_id: CLAIM-CONVERGENCE-POSTMERGE-028
fencing_token: 28
lease_id: LEASE-24a5183caf30af75e74a
run_id: RUN-20260915-144337-postmerge-recovery
branch: convergence/postmerge-recovery-token28-20260915
pr: 466
base_main_sha: 38d52d60f109f373741ce95021a60b03ea69dffc
checkpoint_head_at_handoff_start: e6c64c228e07eb8a2c8f437fa8575c6d3423b158
handoff_id: HANDOFF-SWISSOS-POSTMERGE-RECOVERY-028-20260915

## North Star
Secure at least one truthful, legal and economically viable Swiss employment offer Roberto can rationally accept, then support relocation.

## Why this wave exists
PR #464 was exact-head green but its post-merge main run 34959545311 failed at Material Mutation Lineage with `MATERIAL_CHANGE_REQUIRES_ONE_ACTIVE_OR_TERMINALIZED_CLAIM:2`. This proved PR-context terminal-owner resolution was not invariant under merge into `main`. Recovery also found an orphan/expired external writer lease and insufficient continuous parent-main freshness enforcement.

## Current candidate repair
PR #466 repairs only orchestration/recovery semantics:
- terminal lineage no longer relies on branch-name tiebreaking on main;
- cross-lineage collapse requires durable causal evidence and monotonic fencing;
- active token19+ claim/lease must remain bound to current canonical main;
- historical one-shot convergence executables are removed while evidence is preserved.

## Verified evidence
- PR #466 exact-head `e6c64c228e07eb8a2c8f437fa8575c6d3423b158` repo-guard run 34988226558 / #4484: PASS.
- Token28 active projection reseal report exists.
- Fresh heartbeat `HB-AGENT-GPT56SOL-CONVERGENCE-028-151559.json` exists.
- Live external lease readback at handoff time: token28 ACTIVE, generation22, watermark28, parent main `38d52d60...`, expires_at `2026-09-15T15:45:59Z` (historical expiry timestamp; successor MUST re-read live state and never assume it is still valid).

## Hard locks / non-effects
- E4 active canonical = 690.
- H-0691 remains UNALLOCATED.
- terminal mappings = 658.
- RECONCILE_REQUIRED = 1403.
- CRM_UNIVERSE_COMPLETE = false.
- OUTBOUND = CLOSED.
- send_allowed = 0.
- No B12, H-ID allocation, Candidate private truth mutation, Gmail mutation or application submission is authorized.

## Exact recovery procedure for successor
1. Re-read live `main`; do not trust the SHA in this file as current authority.
2. Re-read `coordination/execution-lease:docs/state/execution-leases/current.json`.
3. Re-read PR #466 state/head and latest workflow runs.
4. Re-read claim28, its latest heartbeat, Runtime Graph, active-claims, NEXT, coordination config and Context Survival.
5. If token28 lease is expired or no longer the active lease, DO NOT resume it. Acquire a new globally fenced session/token through CAS/takeover and explicitly supersede/recover lineage.
6. If another fresh writer owns the lease/scope, do not compete.
7. If still legitimately owned and fresh, continue only the terminalization sequence: persist iteration receipt from evidence, terminalize branch claim, release external lease by exact CAS/readback, emit COMPLETE only after release readback, rebuild zero-writer Runtime Graph/V2/Context Survival, run final exact-head gauntlet.
8. Re-read live main after final CI. Merge only an expected qualified head with no relevant-scope drift.
9. Mandatory post-merge main repo-guard must PASS. If it fails, downstream remains blocked.
10. Only after exact-main zero-writer qualification may issue #54/convergence be considered for closure. #441 remains independent platform-pre-receive debt while main is unprotected.

## Important negative knowledge
- Green PR CI is not merge authority and not post-merge evidence.
- A historical ACTIVE claim file does not prove a live writer; external lease freshness is temporal.
- Never fabricate a terminal receipt or COMPLETE heartbeat merely to release a stale writer.
- If lease has expired, recovery must use a new session/token, not backdate/revive token28.
- Do not open B12 automatically after convergence.

## Next safe action
Re-read the live external lease first. The timestamp in this handoff indicates token28 may already be expired by the time a successor reads it. If expired, execute stale-writer takeover/recovery with a new token; if still fresh and legitimately owned, finish two-surface terminalization. Preserve all hard locks.

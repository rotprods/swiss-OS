from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

BASE_MAIN_SHA = "1072d5cfb33beee3f2afcd31a59ba00c514df170"
TOKEN16_HB = "docs/state/agent-runtime/heartbeats/HB-AGENT-GPT56SOL-GRAPHV2-001-SES-016-153000.json"
TOKEN16_CLAIM = "docs/state/v2/claims/CLAIM-GRAPHV2-WAVE-LEASE-016.json"
TOKEN16_EVENT = "docs/state/v2/events/EVT-20260902T153000Z-GRAPHV2-TOKEN16-ACQUIRED.json"


def patch_execution_lease() -> None:
    path = Path("src/swiss_os/execution_lease.py")
    text = path.read_text()
    old = (
        "            self.project_id, self.wave_id, self.owner_agent_id, self.run_id,\n"
        "            self.session_id, f\"TOKEN{self.fencing_token}\",\n"
    )
    new = (
        "            self.project_id, self.wave_id, self.owner_agent_id, self.run_id,\n"
        "            self.session_id, self.parent_main_sha, self.authority_epoch,\n"
        "            f\"TOKEN{self.fencing_token}\",\n"
    )
    if old in text:
        text = text.replace(old, new, 1)
    elif "self.session_id, self.parent_main_sha, self.authority_epoch" not in text:
        raise RuntimeError("execution_lease idempotency patch anchor missing")
    path.write_text(text)


def patch_meta_execution() -> None:
    path = Path("src/swiss_os/meta_execution.py")
    text = path.read_text()
    if "from .execution_lease import LeaseAdmission" not in text:
        text = text.replace(
            "from typing import Any, Mapping\n",
            "from typing import Any, Mapping\n\nfrom .execution_lease import LeaseAdmission\n",
            1,
        )
    if "LEASE_READ_ONLY_FALLBACK" not in text:
        text = text.replace(
            '    RECOVERY_PERSISTENCE = "RECOVERY_PERSISTENCE"\n    NO_SAFE_ROUTE = "NO_SAFE_ROUTE"',
            '    RECOVERY_PERSISTENCE = "RECOVERY_PERSISTENCE"\n    LEASE_READ_ONLY_FALLBACK = "LEASE_READ_ONLY_FALLBACK"\n    NO_SAFE_ROUTE = "NO_SAFE_ROUTE"',
            1,
        )
    if "def _choose_meta_route_unleased(" not in text:
        text = text.replace(
            "def choose_meta_route(c: MetaCapabilities) -> MetaDecision:",
            "def _choose_meta_route_unleased(c: MetaCapabilities) -> MetaDecision:",
            1,
        )
    if "_MUTATION_CAPABLE_MODES" not in text:
        text += '''

_MUTATION_CAPABLE_MODES = {
    ExecutionMode.AUTHORITATIVE_WRITE,
    ExecutionMode.DEGRADED_CANARY,
    ExecutionMode.RECOVERY_RECONCILE,
}


def choose_meta_route(
    c: MetaCapabilities,
    lease_admission: LeaseAdmission | None = None,
) -> MetaDecision:
    """Choose the safest productive route and apply writer-lease admission last.

    Lease admission may only remove mutation authority. Existing read-only or
    blocked decisions are never widened by the lease layer.
    """
    decision = _choose_meta_route_unleased(c)
    if (
        lease_admission is None
        or lease_admission.writer_allowed
        or decision.execution_mode not in _MUTATION_CAPABLE_MODES
    ):
        return decision
    return MetaDecision(
        execution_mode=ExecutionMode.READ_ONLY_RESEARCH,
        route=MetaRoute.LEASE_READ_ONLY_FALLBACK,
        reason=(
            f"Writer lease denied ({lease_admission.kind.value}): "
            f"{lease_admission.reason}. Intended route was {decision.route.value}."
        ),
        graph_impact="META",
        hard_blocks=decision.hard_blocks + (
            f"EXECUTION_LEASE_{lease_admission.kind.value}",
        ),
        capabilities_used=decision.capabilities_used + ("execution_lease_gate",),
        next_fallback_routes=(decision.route,) + decision.next_fallback_routes,
        authority_advance_allowed=False,
        canonical_id_allocation_allowed=False,
        outbound_allowed=False,
    )
'''
    path.write_text(text)


def patch_cli() -> None:
    path = Path("src/swiss_os/cli.py")
    text = path.read_text()
    if "from datetime import datetime, timezone" not in text:
        text = text.replace("import argparse\n", "import argparse\nfrom datetime import datetime, timezone\n", 1)
    if "from .execution_lease import (" not in text:
        text = text.replace(
            "from .db import connect, foreign_key_violations, initialize, integrity_check\n",
            "from .db import connect, foreign_key_violations, initialize, integrity_check\n"
            "from .execution_lease import (\n"
            "    DEFAULT_LEASE_STATE_PATH,\n"
            "    LeaseRequest,\n"
            "    evaluate_lease,\n"
            "    load_lease_projection,\n"
            "    parse_utc,\n"
            ")\n",
            1,
        )
    text = text.replace(
        "def cmd_meta_next(path: str) -> int:\n",
        "def cmd_meta_next(path: str, lease_state: str, lease_request: str | None = None, now: str | None = None) -> int:\n",
        1,
    )
    old = "    capabilities = MetaCapabilities.from_mapping(payload)\n    decision = choose_meta_route(capabilities)\n"
    new = '''    capabilities = MetaCapabilities.from_mapping(payload)
    current_lease = load_lease_projection(lease_state)
    request = None
    if lease_request:
        request_payload = _read_json(lease_request)
        if not isinstance(request_payload, dict):
            raise ValueError("lease request payload must be a JSON object")
        request = LeaseRequest.from_mapping(request_payload)
    observed_at = parse_utc(now) if now else datetime.now(timezone.utc)
    lease_admission = evaluate_lease(current_lease, request, observed_at)
    decision = choose_meta_route(capabilities, lease_admission=lease_admission)
'''
    if old in text:
        text = text.replace(old, new, 1)
    elif "lease_admission = evaluate_lease" not in text:
        raise RuntimeError("cli meta admission patch anchor missing")
    if '"execution_lease": lease_admission.as_dict(),' not in text:
        text = text.replace(
            "        **decision.as_dict(),\n",
            "        **decision.as_dict(),\n        \"execution_lease\": lease_admission.as_dict(),\n",
            1,
        )
    anchor = '    meta_next.add_argument("capabilities_json")\n'
    if "--lease-state" not in text:
        if anchor not in text:
            raise RuntimeError("cli parser anchor missing")
        text = text.replace(
            anchor,
            anchor
            + '    meta_next.add_argument("--lease-state", default=str(DEFAULT_LEASE_STATE_PATH))\n'
            + '    meta_next.add_argument("--lease-request")\n'
            + '    meta_next.add_argument("--now")\n',
            1,
        )
    text = text.replace(
        "        return cmd_meta_next(args.capabilities_json)\n",
        "        return cmd_meta_next(args.capabilities_json, args.lease_state, args.lease_request, args.now)\n",
        1,
    )
    path.write_text(text)


def patch_local_ci() -> None:
    path = Path("scripts/local_ci.sh")
    text = path.read_text()
    anchor = 'run "Heartbeat liveness guard" "$PYTHON_BIN" scripts/heartbeat_liveness_guard.py --receipt "$RECEIPT_DIR/heartbeat-liveness.json"\n'
    if "Wave execution lease guard" not in text:
        if anchor not in text:
            raise RuntimeError("local_ci lease guard anchor missing")
        text = text.replace(
            anchor,
            anchor + 'run "Wave execution lease guard" "$PYTHON_BIN" scripts/wave_lease_guard.py --receipt "$RECEIPT_DIR/wave-execution-lease.json"\n',
            1,
        )
    path.write_text(text)


def materialize_final_workflow() -> None:
    original = subprocess.check_output(
        ["git", "show", f"{BASE_MAIN_SHA}:.github/workflows/repo-guard.yml"], text=True
    )
    anchor = (
        "      - name: Heartbeat liveness guard\n"
        "        run: python scripts/heartbeat_liveness_guard.py --receipt /tmp/heartbeat-liveness.json\n"
    )
    if anchor not in original:
        raise RuntimeError("repo-guard lease step anchor missing")
    final = original.replace(
        anchor,
        anchor
        + "      - name: Wave execution lease guard\n"
        + "        run: python scripts/wave_lease_guard.py --receipt /tmp/wave-execution-lease.json\n",
        1,
    )
    final = final.replace(
        "            /tmp/heartbeat-liveness.json\n",
        "            /tmp/heartbeat-liveness.json\n            /tmp/wave-execution-lease.json\n",
        1,
    )
    Path(".github/workflows/repo-guard.yml").write_text(final)


def write_protocol_and_claim_scope() -> None:
    protocol_path = "docs/operations/WAVE_EXECUTION_LEASE_PROTOCOL.md"
    claim_path = Path(TOKEN16_CLAIM)
    claim = json.loads(claim_path.read_text())
    if protocol_path not in claim["resource_scopes"]:
        claim["resource_scopes"].append(protocol_path)
    claim_path.write_text(json.dumps(claim, separators=(",", ":")) + "\n")

    Path(protocol_path).write_text('''# WAVE EXECUTION LEASE PROTOCOL — WELP-1.0

## Purpose

Prevent short-interval scheduled or manual re-entry from creating overlapping state-mutating waves. This is an orchestration-safety contract, not an always-on daemon, distributed lock service, or replacement for GRAPH-REFACTOR-V2 fencing/heartbeat authority.

## Three-layer concurrency model

1. **Execution lease — admission:** one time-bounded writer identity for a wave activation.
2. **Fencing token — ordering:** stale or consumed writer generations cannot regain authority.
3. **Heartbeat — liveness:** an admitted active writer must remain observably alive.

No layer may impersonate or silently replace another.

## Durable public-safe lease

Canonical projection: `docs/state/execution-leases/current.json`.

An active lease contains: `project_id`, deterministic `lease_id`, `owner_agent_id`, `run_id`, `session_id`, `wave_id`, `acquired_at`, `expires_at`, `parent_main_sha`, `authority_epoch`, `fencing_token`, `state`, `idempotency_key`, and `mutation_allowed`.

`idempotency_key` binds project + wave + owner + run + session + parent SHA + authority epoch + fencing token. Changing ancestry or authority therefore creates a different identity.

## Admission rules

- No active lease: acquisition may proceed if the ordinary ancestry/authority/fencing gates also pass.
- Same live holder: renewal is idempotent; `lease_id` does not change.
- Different activation while a live lease exists: writer admission is denied and the activation MUST downgrade to `READ_ONLY_RESEARCH`; it may gather evidence but must not mutate durable state.
- Expired ACTIVE lease: the same run/session MUST NOT resurrect it. Recovery requires a new run, new session and strictly higher fencing token.
- Released lease: the same identity is terminal; a successor requires a new identity and higher fencing token.
- Parent SHA or authority-epoch mismatch: fail closed into recovery/read-only behavior.

## Renewal

Renew only before `expires_at`, by the same owner/run/session/wave/ancestry/authority/fencing identity. Renewal moves only expiry; it does not mint a new generation.

## Release

Release is explicit and terminal for that lease identity. Persist `state=RELEASED`, `mutation_allowed=false`, `released_at`, and a non-empty reason. The canonical `current.json` projection should then return to `active_lease=null`.

## Stale recovery

Expiry is not permission to resume. A takeover is admissible only with a new run/session and a fencing token greater than the expired lease. Fencing and heartbeat guards remain independently mandatory.

## MEP scheduled re-entry

`swiss-os meta next` reads the canonical lease projection by default. When a foreign live lease blocks a mutation-capable MEP route, the planner returns `LEASE_READ_ONLY_FALLBACK` with `execution_mode=READ_ONLY_RESEARCH` and all authority/ID/outbound permissions false. Existing read-only routes may continue.

A scheduled trigger is only a re-entry mechanism: it reconstructs state, evaluates the lease, chooses a safe route, persists bounded work, and terminates. WELP-1.0 does not authorize a resident background process.

## Acceptance

WELP-1.0 is green only when unit/adversarial tests prove acquire, renew, foreign overlap fallback, expiry, stale takeover, release terminality, ancestry/epoch fail-closed behavior, durable projection validation, MEP downgrade, and CI guard execution.
''')


def update_control_plane(pr_number: int) -> None:
    cfg_path = Path("docs/refactor-v2/coordination_current_config.json")
    cfg = json.loads(cfg_path.read_text())
    cfg.update(
        primary_program="GRAPH_REFACTOR_V2_WAVE_EXECUTION_LEASE",
        base_main_sha=BASE_MAIN_SHA,
        generated_at="2026-09-02T15:30:00Z",
        state="GRAPH_V2_WAVE_EXECUTION_LEASE_ACTIVE",
        current_objective_id="OBJ-WAVE-LEASE-OVERLAP-PROTECTION",
        branch="feat/wave-lease-token16",
        open_prs=[pr_number, 425, 414],
    )
    cfg["state_refs"] = [
        "GOAL.md", "STATE.md", "ARCHITECTURE.md", "HANDOFF.md", "TASKS.md", "LEXICON.md",
        "docs/architecture/V2_2_CANONICAL_ARCHITECTURE.md",
        "docs/operations/AGENT_AUTORESEARCH_PROGRAM.md",
        "docs/operations/WAVE_EXECUTION_LEASE_PROTOCOL.md",
        "docs/state/v2/project-state.json", "docs/state/v2/active-claims.json",
        "docs/state/agent-runtime/runtime-graph.json", "docs/state/execution-leases/current.json",
        "docs/state/platform/GRAPH_V2_PLATFORM_ENFORCEMENT_REQUIREMENT.json",
        "docs/state/platform/GRAPH_V2_PLATFORM_READBACK.json",
        "issue:#54", "issue:#441", f"pr:#{pr_number}",
    ]
    cfg["relevant_paths"] = [
        "GOAL.md", "STATE.md", "ARCHITECTURE.md", "HANDOFF.md", "TASKS.md", "AGENTS.md", "docs/state/NEXT.json",
        "docs/architecture/V2_2_CANONICAL_ARCHITECTURE.md", "docs/operations/AGENT_AUTORESEARCH_PROGRAM.md",
        "docs/operations/META_EXECUTION_PROTOCOL.md", "docs/operations/WAVE_OPERATING_PROTOCOL.md",
        "docs/operations/NEXT_POINTER_PROTOCOL.md", "docs/operations/WAVE_EXECUTION_LEASE_PROTOCOL.md",
        "src/swiss_os/v2_coordination.py", "src/swiss_os/agent_improvement_runtime.py", "src/swiss_os/agent_runtime_graph.py",
        "src/swiss_os/execution_lease.py", "src/swiss_os/meta_execution.py", "src/swiss_os/cli.py",
        "scripts/material_mutation_lineage_guard.py", "scripts/stale_branch_fencing_guard.py", "scripts/heartbeat_liveness_guard.py",
        "scripts/wave_lease_guard.py", "scripts/platform_enforcement_guard.py", "scripts/rebuild_v2_coordination.py",
        "scripts/rebuild_agent_runtime_graph.py", "scripts/agent_improvement_guard.py", "scripts/context_survival_guard.py",
        "scripts/local_ci.sh", ".github/workflows/repo-guard.yml", "docs/state/execution-leases/current.json",
        "tests/test_execution_lease.py", "docs/state/platform/GRAPH_V2_PLATFORM_ENFORCEMENT_REQUIREMENT.json",
        "docs/state/platform/GRAPH_V2_PLATFORM_READBACK.json", "docs/state/agent-runtime/runtime-graph.json",
        TOKEN16_HB, TOKEN16_CLAIM, TOKEN16_EVENT, "docs/state/v2/project-state.json", "docs/state/v2/active-claims.json",
    ]
    cfg["survival_paths"] = [
        "GOAL.md", "STATE.md", "HANDOFF.md", "TASKS.md", "AGENTS.md", "docs/state/NEXT.json",
        "docs/state/v2/project-state.json", "docs/state/v2/context-pack.json", "docs/state/v2/active-claims.json",
        "docs/state/agent-runtime/runtime-graph.json", TOKEN16_HB, "docs/state/execution-leases/current.json",
        "docs/operations/WAVE_EXECUTION_LEASE_PROTOCOL.md",
        "docs/state/platform/GRAPH_V2_PLATFORM_ENFORCEMENT_REQUIREMENT.json",
        "docs/state/platform/GRAPH_V2_PLATFORM_READBACK.json", "docs/operations/AGENT_AUTORESEARCH_PROGRAM.md",
        "docs/operations/CONTEXT_SURVIVAL_PROTOCOL.md", "docs/handoffs/NEXT_ITERATION_METAPROMPT_V3.md",
        "docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B06.json",
    ]
    cfg["source_refs"] = [
        f"main:{BASE_MAIN_SHA}", "issue:#54:OPEN", "issue:#441:OPEN_PLATFORM_BLOCKER",
        f"pr:#{pr_number}:OPEN", "claim:CLAIM-GRAPHV2-WAVE-LEASE-016:ACTIVE",
        "fencing_high_watermark:15", "active_claims:0",
    ]
    cfg["blockers"] = [
        "GitHub main is not platform-protected; issue #441 remains fail-closed for production authority.",
        "RECONCILE_REQUIRED=1403 remains domain work outside this repo-orchestration claim.",
        "H-0580 remains a separate hotel authority blocker.",
        "Candidate external assets remain subject to private human approval.",
    ]
    cfg["verified_work"] = [
        "Token15 stale-fencing and heartbeat-liveness work is merged and terminalized on main 1072d5cfb33beee3f2afcd31a59ba00c514df170 with zero active writers.",
        "Issue #54 is an independent P1 gap: fencing orders writers and heartbeat proves liveness, but neither grants time-bounded scheduled-activation admission.",
        "Token16 was acquired from exact idle main with fencing token16 and repo-only orchestration authority.",
        "No hotel, CRM, H-ID, candidate, application, outbound or Gmail authority is widened.",
    ]
    cfg["unverified_work"] = [
        "WELP-1.0 acquire/renew/release/expiry/takeover semantics must pass adversarial unit tests.",
        "Foreign live leases must downgrade mutation-capable MEP routes to read-only while preserving existing read-only work.",
        "The durable lease projection and wave lease guard must be enforced in local and PR CI.",
        "The complete repo/death/unit/canary gauntlet must pass on one final tested head before KEEP or merge.",
        "Token16 must be explicitly released after merge and zero active writers proven.",
    ]
    cfg["risks"] = [
        "Short-interval scheduled activations can overlap before one sees another writer unless admission is durable and time-bounded.",
        "Lease expiry must not be confused with permission to resurrect the same run/session.",
        "Lease logic must not duplicate or weaken fencing-token ordering or heartbeat liveness.",
        "A missing/invalid lease projection must fail closed rather than silently granting mutation authority.",
        "A future unprotected direct push can still land before CI until #441 is resolved.",
    ]
    cfg["next_safe_actions"] = [
        "Run targeted WELP-1.0 tests and reject any overlap path that can retain mutation authority.",
        "Run the complete repo/death/unit/canary gauntlet and persist KEEP/DISCARD only from measured evidence.",
        "Merge the bounded #54 PR only from fresh main with expected tested head SHA, then release token16 to zero writers.",
    ]
    cfg["liveness_findings"] = [
        "Execution lease controls admission; fencing controls writer generation; heartbeat controls liveness.",
        "A foreign live lease permits read-only research but never a concurrent state-mutating wave.",
        "Expired leases require explicit recovery with new run/session and a higher fencing token.",
        "Scheduled activation remains finite re-entry rather than an always-on daemon.",
        "GitHub platform enforcement remains independently fail-closed while main is unprotected.",
    ]
    cfg["resume_contract"] = [
        f"verify live main is {BASE_MAIN_SHA} or a descendant",
        "replay events/claims and verify token16 is the sole active claim with fencing watermark 16",
        "verify NEXT active_claim and Runtime Graph point to token16 session SES-20260902T153000Z-GRAPHV2-WAVE-LEASE-016",
        "verify WELP-1.0 never grants writer authority when a foreign live lease exists",
        "verify stale lease recovery requires a new run/session and fencing token > prior lease token",
        "verify stale-fencing, heartbeat-liveness and wave-lease guards all remain green",
        "verify platform readback remains production_authority_allowed=false while #441 is open",
        "keep E4/690, H-0691, CRM and outbound locks unchanged",
    ]
    cfg["graph"] = {
        "nodes": [
            {"id": "P:SWITZERLAND_JOB_OS", "type": "Project", "state": "ACTIVE"},
            {"id": "G:G-0001", "type": "NorthStar", "state": "ACTIVE"},
            {"id": "C:CLAIM-GRAPHV2-WAVE-LEASE-016", "type": "Claim", "state": "ACTIVE_TOKEN_16"},
            {"id": "ISSUE:54", "type": "WaveLeaseCapability", "state": "ACTIVE"},
            {"id": f"PR:{pr_number}", "type": "PullRequest", "state": "OPEN"},
            {"id": "LEASE:WELP-1.0", "type": "ExecutionLeaseProtocol", "state": "IMPLEMENTED_CANARY"},
            {"id": "GUARD:WAVE-EXECUTION-LEASE", "type": "Guard", "state": "IMPLEMENTED_CANARY"},
            {"id": "GUARD:STALE-BRANCH-FENCING", "type": "Guard", "state": "PRODUCTION"},
            {"id": "GUARD:HEARTBEAT-LIVENESS", "type": "Guard", "state": "PRODUCTION"},
            {"id": "ISSUE:441", "type": "PlatformBlocker", "state": "OPEN"},
            {"id": "RUNTIME:AGENT-AUTORESEARCH", "type": "AgentRuntime", "state": "PRODUCTION"},
        ],
        "edges": [
            {"from": "C:CLAIM-GRAPHV2-WAVE-LEASE-016", "to": "ISSUE:54", "type": "IMPLEMENTS"},
            {"from": f"PR:{pr_number}", "to": "ISSUE:54", "type": "IMPLEMENTS"},
            {"from": "LEASE:WELP-1.0", "to": "RUNTIME:AGENT-AUTORESEARCH", "type": "ADMITS_WRITER"},
            {"from": "GUARD:WAVE-EXECUTION-LEASE", "to": "LEASE:WELP-1.0", "type": "VALIDATES"},
            {"from": "GUARD:STALE-BRANCH-FENCING", "to": "LEASE:WELP-1.0", "type": "ORDERS_GENERATIONS"},
            {"from": "GUARD:HEARTBEAT-LIVENESS", "to": "LEASE:WELP-1.0", "type": "OBSERVES_LIVENESS"},
            {"from": "ISSUE:441", "to": "G:G-0001", "type": "BLOCKS_PLATFORM_PREVENTION"},
        ],
        "hyperrelations": [{
            "id": "HR:WAVE-LEASE-016",
            "type": "TIME_BOUNDED_WRITER_ADMISSION_GATE",
            "members": [
                "C:CLAIM-GRAPHV2-WAVE-LEASE-016", "ISSUE:54", f"PR:{pr_number}",
                "LEASE:WELP-1.0", "GUARD:WAVE-EXECUTION-LEASE", "GUARD:STALE-BRANCH-FENCING",
                "GUARD:HEARTBEAT-LIVENESS", "RUNTIME:AGENT-AUTORESEARCH",
            ],
            "semantics": "WELP-1.0 prevents overlapping state-mutating scheduled activations while preserving read-only fallback and composing with fencing plus heartbeat liveness without widening domain authority.",
        }],
    }
    cfg_path.write_text(json.dumps(cfg, separators=(",", ":")) + "\n")

    next_path = Path("docs/state/NEXT.json")
    payload = json.loads(next_path.read_text())
    payload["active_claim"] = {
        "claim_id": "CLAIM-GRAPHV2-WAVE-LEASE-016",
        "fencing_token": 16,
        "authority_ceiling": "REPO_WAVE_LEASE_ORCHESTRATION_SAFETY_ONLY_NO_DOMAIN_OR_EXTERNAL_MUTATION",
    }
    next_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    pr_number = int(os.environ["PR_NUMBER"])
    patch_execution_lease()
    patch_meta_execution()
    patch_cli()
    patch_local_ci()
    materialize_final_workflow()
    write_protocol_and_claim_scope()
    update_control_plane(pr_number)


if __name__ == "__main__":
    main()

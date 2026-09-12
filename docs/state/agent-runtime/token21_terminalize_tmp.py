from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "SWITZERLAND_JOB_OS"
MAIN = "3c902a791be0e8df1db564034e211ea90c41f1b3"
AGENT = "AGENT-GPT56SOL-CONVERGENCE-021"
SESSION = "SES-20260912T203915Z-CONVERGENCE-021"
CLAIM = "CLAIM-CONVERGENCE-LINEAGE-021"
WORKSTREAM = "WS-CONVERGENCE-LEASE-REPAIR"
OBJECTIVE = "OBJ-SWISS-MAIN-SINGULARITY"
CORR = "CORR-20260912T203915Z-CONVERGENCE-021"
TOKEN = 21
ITERATION = "ITER-convergence-main-singularity-token21"
GREEN_RUN = 34718476671
GREEN_HEAD = "3c7cf285e5d9f474c4df58aede300b26e442d3d3"
LEASE_ID = "LEASE-0479ab715ce626b5422f"


def now_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def dump(path: str | Path, value: object, *, indent: int | None = None) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=indent) if indent else json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    p.write_text(text + "\n", encoding="utf-8")


def main() -> None:
    ts = now_z()

    claim_path = Path(f"docs/state/v2/claims/{CLAIM}.json")
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    assert claim["state"] == "ACTIVE"
    assert claim["fencing_token"] == TOKEN
    claim["state"] = "RELEASED"
    claim["released_at"] = ts
    dump(claim_path, claim)

    event = {
        "schema_version": "COS-V2-EVENT-1.1",
        "event_id": f"EVT-{ts.replace('-','').replace(':','').replace('Z','')}-CONVERGENCE-TOKEN21-CLAIM-RELEASED",
        "event_type": "CLAIM_RELEASED",
        "occurred_at": ts,
        "project_id": PROJECT,
        "agent_id": AGENT,
        "session_id": SESSION,
        "workstream_id": WORKSTREAM,
        "objective_id": OBJECTIVE,
        "correlation_id": CORR,
        "repo": "rotprods/swiss-OS",
        "main_sha_observed": MAIN,
        "base_sha": MAIN,
        "authority_ceiling": "CONVERGENCE_ORCHESTRATION_AND_LEASE_REPAIR_ONLY_NO_DOMAIN_OR_OUTBOUND_AUTHORITY",
        "summary": "Token21 released after terminal-lineage succession repair, cumulative claim-scope reconciliation and exact-head full repository gauntlet all passed with zero domain/outbound authority mutation.",
        "next_action": "Rebuild zero-writer Runtime Graph/V2/Context Survival, release the external CAS lease, run one final exact-head terminal gauntlet, re-read live main and await explicit owner merge instruction for PR #463.",
        "idempotency_key": f"{PROJECT}|{CLAIM}|RELEASED|MAIN-SINGULARITY",
        "canonical_hotel_mutation_allowed": False,
        "h_id_allocation_allowed": False,
        "outbound_allowed": False,
        "causation": [f"claim:{CLAIM}", "predecessor:CLAIM-CONVERGENCE-LEASE-020", f"lease:{LEASE_ID}", "pr:463", f"run:{GREEN_RUN}", "wave:WAVE-20260912-CONVERGENCE-LINEAGE-003"],
    }
    event_name = event["event_id"] + ".json"
    dump(Path("docs/state/v2/events") / event_name, event)

    heartbeat = {
        "heartbeat_id": "HB-AGENT-GPT56SOL-CONVERGENCE-021-COMPLETE",
        "project_id": PROJECT,
        "agent_id": AGENT,
        "session_id": SESSION,
        "workstream_id": WORKSTREAM,
        "objective_id": OBJECTIVE,
        "goal_ids": ["G-0001"],
        "plan_id": "PLAN-MAIN-SINGULARITY-P0",
        "task_id": "TASK-TERMINAL-LINEAGE-SUCCESSION-REPAIR",
        "claim_id": CLAIM,
        "fencing_token": TOKEN,
        "observed_at": ts,
        "state": "COMPLETE",
        "branch": "convergence/main-singularity",
        "worktree": ".worktrees/convergence-main-singularity",
        "base_main_sha": MAIN,
        "authority_ceiling": "CONVERGENCE_ORCHESTRATION_AND_LEASE_REPAIR_ONLY_NO_DOMAIN_OR_OUTBOUND_AUTHORITY",
        "graph_program": "GRAPH-REFACTOR-V2",
        "pr_number": 463,
        "current_iteration_id": ITERATION,
        "next_safe_action": "Token21 lineage repair is KEEP-qualified. Release the external CAS lease, rebuild zero-writer terminal state, run final exact-head gauntlet, re-read live main, then await explicit owner merge instruction. Do not start B12 or another feature wave.",
    }
    dump("docs/state/agent-runtime/heartbeats/HB-AGENT-GPT56SOL-CONVERGENCE-021-COMPLETE.json", heartbeat)

    receipt = {
        "schema_version": "AGENT-IMPROVEMENT-ITERATION-1.1",
        "iteration_id": ITERATION,
        "decision": "KEEP",
        "reason": "The bounded token21 repair made terminal material-lineage ownership causal rather than count-based: explicit monotonic predecessor/successor chains collapse to one effective terminal owner while unrelated terminal claims still fail closed. Claim scope was reconciled against the full cumulative PR diff, the global SHA-CAS lease remained single-writer, deterministic Runtime Graph/V2/Context Survival state was rebuilt, and exact-head repo-guard workflow 34718476671 passed all declared gates including lineage, live lease, recovery/death drill, unit tests and canary. E4/690, H-0691, terminal mappings and outbound authority did not change.",
        "tests_passed": True,
        "complexity_delta": 1,
        "security_violations": [],
        "invariant_violations": [],
        "context": {
            "project_id": PROJECT,
            "agent_id": AGENT,
            "session_id": SESSION,
            "workstream_id": WORKSTREAM,
            "objective_id": OBJECTIVE,
            "goal_ids": ["G-0001"],
            "plan_id": "PLAN-MAIN-SINGULARITY-P0",
            "task_id": "TASK-TERMINAL-LINEAGE-SUCCESSION-REPAIR",
            "claim_id": CLAIM,
            "fencing_token": TOKEN,
            "correlation_id": CORR,
            "graph_program": "GRAPH-REFACTOR-V2",
            "branch": "convergence/main-singularity",
            "worktree": ".worktrees/convergence-main-singularity",
            "base_main_sha": MAIN,
            "authority_ceiling": "CONVERGENCE_ORCHESTRATION_AND_LEASE_REPAIR_ONLY_NO_DOMAIN_OR_OUTBOUND_AUTHORITY",
            "pr_number": 463,
        },
        "proposal": {
            "hypothesis": "Explicit causal succession plus globally serialized CAS ownership can preserve strict fail-closed material lineage across supersession/release transitions without weakening unrelated-claim ambiguity checks.",
            "reversible": True,
            "budget_seconds": 10800,
            "complexity_delta": 1,
            "changed_paths": [
                "scripts/material_mutation_lineage_guard.py",
                "tests/test_material_mutation_lineage.py",
                f"docs/state/v2/claims/{CLAIM}.json",
                "docs/state/v2/events/**TOKEN21**",
                "docs/state/agent-runtime/**CONVERGENCE-021**",
                "docs/refactor-v2/coordination_current_config.json",
                "docs/state/NEXT.json",
                "docs/state/v2/**",
                "docs/continuity/CONTEXT_SURVIVAL.json",
            ],
            "evaluation_suite": [
                "repo_guard","system_contract_guard","agent_improvement_guard","material_mutation_lineage_guard","stale_branch_fencing_guard","heartbeat_liveness_guard","execution_lease_live_guard","platform_enforcement_guard","agent_runtime_graph_guard","v2_coordination_rebuild","v2_contract_guard","v2_forward_event_guard","context_survival_guard","zero_context_death_drill","cwp_lineage_guard","handoff_frontier_guard","unit_tests","manifest_semantics_canary"
            ],
            "notes": f"Exact-head acceptance workflow {GREEN_RUN} / repo-guard 4448 passed every declared evaluator on durable head {GREEN_HEAD}. Bootstrap validation also exercised the full cumulative main...HEAD material surface. No merge is implied by KEEP.",
        },
        "metric_results": [
            {"metric_id":"terminal_lineage_false_ambiguity","baseline":1.0,"candidate":0.0,"direction":"MIN","min_meaningful_delta":1.0,"max_allowed_regression":0.0,"protected":True},
            {"metric_id":"unrelated_terminal_claims_fail_closed","baseline":1.0,"candidate":1.0,"direction":"MAX","min_meaningful_delta":0.0,"max_allowed_regression":0.0,"protected":True},
            {"metric_id":"exact_head_gauntlet_pass","baseline":0.0,"candidate":1.0,"direction":"MAX","min_meaningful_delta":1.0,"max_allowed_regression":0.0,"protected":False},
            {"metric_id":"authority_mutations","baseline":0.0,"candidate":0.0,"direction":"MIN","min_meaningful_delta":0.0,"max_allowed_regression":0.0,"protected":True},
            {"metric_id":"h_id_allocations","baseline":0.0,"candidate":0.0,"direction":"MIN","min_meaningful_delta":0.0,"max_allowed_regression":0.0,"protected":True},
            {"metric_id":"outbound_actions","baseline":0.0,"candidate":0.0,"direction":"MIN","min_meaningful_delta":0.0,"max_allowed_regression":0.0,"protected":True},
        ],
        "graph_nodes": [
            {"id":f"AGENT:{AGENT}","type":"Agent"},{"id":f"SESSION:{SESSION}","type":"Session"},{"id":f"CLAIM:{CLAIM}","type":"Claim","fencing_token":21},{"id":"LEASE:GLOBAL-EXECUTION-LEASE-021","type":"ExecutionLease"},{"id":"TASK:TASK-TERMINAL-LINEAGE-SUCCESSION-REPAIR","type":"Task"},{"id":f"ITERATION:{ITERATION}","type":"Experiment","decision":"KEEP"},{"id":"PR:463","type":"PullRequest"}
        ],
        "graph_edges": [
            {"from":f"AGENT:{AGENT}","to":f"SESSION:{SESSION}","type":"EXECUTES"},{"from":f"SESSION:{SESSION}","to":f"CLAIM:{CLAIM}","type":"OWNS"},{"from":"LEASE:GLOBAL-EXECUTION-LEASE-021","to":f"CLAIM:{CLAIM}","type":"SERIALIZES"},{"from":"TASK:TASK-TERMINAL-LINEAGE-SUCCESSION-REPAIR","to":f"ITERATION:{ITERATION}","type":"TESTED_BY"},{"from":f"ITERATION:{ITERATION}","to":"PR:463","type":"QUALIFIES"}
        ],
    }
    dump(Path("docs/state/agent-runtime/iterations") / f"{ITERATION}.json", receipt)

    config_path = Path("docs/refactor-v2/coordination_current_config.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["generated_at"] = ts
    config["state"] = "CONVERGENCE_QUALIFIED_TOKEN21_RELEASED_AWAITING_EXPLICIT_MERGE"
    for key in ("state_refs", "relevant_paths", "survival_paths"):
        values = config.get(key, [])
        if isinstance(values, list):
            values = ["docs/state/agent-runtime/heartbeats/HB-AGENT-GPT56SOL-CONVERGENCE-021-COMPLETE.json" if value == "docs/state/agent-runtime/heartbeats/HB-AGENT-GPT56SOL-CONVERGENCE-021-INIT.json" else value for value in values]
            config[key] = list(dict.fromkeys(values))
    refs = []
    for value in config.get("source_refs", []):
        if value == f"claim:{CLAIM}:ACTIVE":
            value = f"claim:{CLAIM}:RELEASED"
        elif value == "lease:coordination/execution-lease:TOKEN21:ACTIVE_CAS":
            value = "lease:coordination/execution-lease:TOKEN21:RELEASED_CAS"
        refs.append(value)
    config["source_refs"] = refs
    config["blockers"] = [
        "Explicit owner merge instruction is required before PR #463 may be promoted.",
        "The global execution-lease/CAS contract remains candidate-only until merge into canonical main.",
        "CRM_UNIVERSE_COMPLETE remains false because RECONCILE_REQUIRED=1403; convergence does not authorize B12 execution or authority promotion.",
        "OUTBOUND remains CLOSED and send_allowed=0; no convergence result grants send authority.",
    ]
    config["next_safe_actions"] = [
        "Require zero-writer Runtime Graph/V2/Context Survival projections with fencing high-watermark 21.",
        "Release external CAS lease token21 and run one final exact-head terminal-state repository gauntlet.",
        "Re-read live main for relevant-scope drift after final CI.",
        "Await explicit owner merge instruction for PR #463; do not open B12 or another feature wave.",
    ]
    verified = config.setdefault("verified_work", [])
    fact = f"Exact-head token21 qualification workflow {GREEN_RUN} / repo-guard 4448 passed every gate after causal lineage and full cumulative claim-scope repair."
    if fact not in verified:
        verified.append(fact)
    config["unverified_work"] = [
        "External token21 CAS lease must be released after branch terminal state is durable.",
        "One final exact-head zero-writer terminal-state gauntlet must pass.",
        "Fresh-main relevant-scope drift must be checked after final CI.",
        "Promotion/merge remains an explicit owner action and is not implied by KEEP or CI green.",
    ]
    config["liveness_findings"] = [
        "Token21 terminal-lineage repair claim is RELEASED with iteration KEEP and heartbeat COMPLETE.",
        "Terminal coordination must project zero active claims with fencing high-watermark 21.",
        "The external CAS lease must be released before final terminal certification; no successor writer is authorized.",
        "Operational authority remains E4/690 with H-0691 unallocated, terminal mappings 658, RECONCILE_REQUIRED=1403 and outbound CLOSED.",
    ]
    graph = config.get("graph", {})
    for node in graph.get("nodes", []):
        if node.get("id") == f"C:{CLAIM}":
            node["state"] = "RELEASED_TOKEN_21_KEEP"
        elif node.get("id") == "L:GLOBAL-EXECUTION-LEASE-021":
            node["state"] = "RELEASED_CAS"
        elif node.get("id") == "PR:463":
            node["state"] = "QUALIFIED_AWAITING_EXPLICIT_MERGE"
    dump(config_path, config)

    root_path = Path("docs/state/NEXT.json")
    root = json.loads(root_path.read_text(encoding="utf-8"))
    root["generated_at"] = ts
    root["active_claim"] = None
    root["execution_mode"] = "RECOVERY_RECONCILE"
    root["selected_route"] = "CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION"
    root["next_route"] = "CURRENT_UNRESOLVED_1403_ENTITY_RESOLUTION"
    root["convergence_route"] = "CONVERGENCE_QUALIFIED_AWAITING_EXPLICIT_MERGE"
    root["successor_execution_allowed"] = False
    root["exact_dependency"] = "CRM domain remains unresolved at 1403 records, but no successor batch is authorized while the qualified convergence candidate awaits explicit owner merge instruction."
    root["hard_blockers"] = ["EXPLICIT_OWNER_MERGE_INSTRUCTION_REQUIRED_FOR_PR_463","GLOBAL_EXECUTION_LEASE_NOT_CANONICAL_UNTIL_EXPLICITLY_AUTHORIZED_MERGE","RECONCILE_REQUIRED_1403_NOT_ZERO","GOAL_DRAIN_BLOCKS_B12_AUTOMATIC_EXECUTION","OUTBOUND_CLOSED"]
    root["next_safe_actions"] = ["Verify terminal projections show zero active writers and fencing high-watermark 21.","Release token21 CAS lease and run final exact-head terminal-state gauntlet.","Re-read live main for relevant-scope drift.","Await explicit owner merge instruction; do not start B12 or another feature wave."]
    root.setdefault("safety", {}).update({"authority_advanced":False,"h_id_allocations":0,"canonical_id_reservations":0,"crm_universe_complete":False,"outbound":"CLOSED","send_allowed":0,"irreversible_external_actions":0})
    dump(root_path, root, indent=2)

    for pointer in ["docs/state/NEXT_CONVERGENCE_ONLY_2026-09-12.json", "docs/state/v2/NEXT_CONVERGENCE_ONLY_2026-09-12.json"]:
        path = Path(pointer)
        data = json.loads(path.read_text(encoding="utf-8"))
        if "status" in data:
            data["status"] = "QUALIFIED_AWAITING_EXPLICIT_MERGE"
        data["claim_id"] = CLAIM
        data["claim_state"] = "RELEASED"
        data["session_id"] = SESSION
        data["fencing_token"] = TOKEN
        data["blockers"] = ["Explicit owner merge instruction is required before PR #463 promotion.","CRM_UNIVERSE_COMPLETE remains FALSE because RECONCILE_REQUIRED=1403.","No successor writer or outbound action is authorized."]
        data["next_safe_actions"] = ["Release external token21 CAS lease.","Run final exact-head zero-writer gauntlet.","Re-read live main for relevant-scope drift.","Await explicit owner merge instruction; do not start B12."]
        if isinstance(data.get("backlog"), dict):
            data["backlog"]["execution_allowed"] = False
        dump(path, data)

    print(json.dumps({"released_at": ts, "release_event": event_name, "iteration": ITERATION}, sort_keys=True))


if __name__ == "__main__":
    main()

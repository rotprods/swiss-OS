from __future__ import annotations

import json
from pathlib import Path

MAIN = "3c902a791be0e8df1db564034e211ea90c41f1b3"
CLAIM_ID = "CLAIM-CONVERGENCE-LINEAGE-021"
SESSION_ID = "SES-20260912T203915Z-CONVERGENCE-021"
AGENT_ID = "AGENT-GPT56SOL-CONVERGENCE-021"
LEASE_ID = "LEASE-0479ab715ce626b5422f"
TS = "2026-09-12T20:39:15Z"


def write_json(path: str | Path, data: object, *, indent: int | None = None) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if indent is None:
        text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    else:
        text = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=indent)
    p.write_text(text + "\n", encoding="utf-8")


def materialize_claim_event_heartbeat() -> None:
    claim = {
        "schema_version": "COS-V2-CLAIM-1.0",
        "project_id": "SWITZERLAND_JOB_OS",
        "claim_id": CLAIM_ID,
        "agent_id": AGENT_ID,
        "session_id": SESSION_ID,
        "workstream_id": "WS-CONVERGENCE-LEASE-REPAIR",
        "objective_id": "OBJ-SWISS-MAIN-SINGULARITY",
        "correlation_id": "CORR-20260912T203915Z-CONVERGENCE-021",
        "state": "ACTIVE",
        "claimed_at": TS,
        "base_sha": MAIN,
        "branch": "convergence/main-singularity",
        "fencing_token": 21,
        "authority_ceiling": "CONVERGENCE_ORCHESTRATION_AND_LEASE_REPAIR_ONLY_NO_DOMAIN_OR_OUTBOUND_AUTHORITY",
        "idempotency_key": "SWITZERLAND_JOB_OS|WS-CONVERGENCE-LEASE-REPAIR|MAIN-SINGULARITY|TOKEN21",
        "resource_scopes": [
            "scripts/material_mutation_lineage_guard.py",
            "tests/test_material_mutation_lineage.py",
            "scripts/wave_lease_guard.py",
            "scripts/execution_lease_live_guard.py",
            "src/swiss_os/execution_lease.py",
            "src/swiss_os/github_execution_lease.py",
            "docs/refactor-v2/coordination_current_config.json",
            "docs/continuity/CONTEXT_SURVIVAL.json",
            "docs/state/NEXT.json",
            "docs/state/NEXT_CONVERGENCE_ONLY_2026-09-12.json",
            "docs/state/v2/**",
            "docs/state/agent-runtime/**",
            ".github/workflows/**",
            "STATE.md",
            "AGENTS.md",
        ],
        "semantic_scopes": [
            "CONVERGENCE_ONLY",
            "GLOBAL_WRITER_SERIALIZATION",
            "TERMINAL_LINEAGE_SUCCESSION_REPAIR",
            "DURABLE_HANDOFF",
        ],
        "excluded_scopes": [
            "HOTELS_AUTHORITY_MUTATION",
            "CRM_ENTITY_RESOLUTION_DECISION",
            "H_ID_ALLOCATION",
            "CANONICAL_ID_RESERVATION",
            "TERMINAL_SOURCE_MAPPING_MUTATION",
            "CANDIDATE_PRIVATE_TRUTH_MUTATION",
            "APPLICATION_SUBMISSION",
            "OUTBOUND_EXECUTION",
            "GMAIL_MUTATION",
        ],
        "preconditions": {
            "main_sha": MAIN,
            "authority_epoch": "HS_ENTITY_EPOCH_2026-08-25_E4",
            "authority_revision": "70307f4aea05f8625a3c9c64947d5791535b9d245ce1c278920394c998d94cc6",
            "active_canonical": 690,
            "next_h_id": "H-0691_UNALLOCATED",
            "terminal_mappings": 658,
            "reconcile_required": 1403,
            "global_lease_watermark": 20,
            "active_global_lease": None,
            "predecessor_claim": "CLAIM-CONVERGENCE-LEASE-020",
            "predecessor_claim_state": "RELEASED",
            "outbound": "CLOSED",
            "send_allowed": 0,
            "convergence_mode": "CONVERGENCE_ONLY",
        },
    }
    write_json(f"docs/state/v2/claims/{CLAIM_ID}.json", claim)

    event = {
        "schema_version": "COS-V2-EVENT-1.1",
        "event_id": "EVT-20260912T203915Z-CONVERGENCE-TOKEN21-ACQUIRED",
        "event_type": "CLAIM_ACQUIRED",
        "occurred_at": TS,
        "project_id": "SWITZERLAND_JOB_OS",
        "agent_id": AGENT_ID,
        "session_id": SESSION_ID,
        "workstream_id": "WS-CONVERGENCE-LEASE-REPAIR",
        "objective_id": "OBJ-SWISS-MAIN-SINGULARITY",
        "correlation_id": "CORR-20260912T203915Z-CONVERGENCE-021",
        "repo": "rotprods/swiss-OS",
        "main_sha_observed": MAIN,
        "base_sha": MAIN,
        "authority_ceiling": "CONVERGENCE_ORCHESTRATION_AND_LEASE_REPAIR_ONLY_NO_DOMAIN_OR_OUTBOUND_AUTHORITY",
        "summary": "Acquire token21 under the global CAS lease to repair terminal lineage succession without reopening domain or outbound authority.",
        "next_action": "Treat explicit predecessor/successor causality as one terminal lineage while preserving failure for unrelated terminal claims; test, rebuild projections and run exact-head gauntlet.",
        "idempotency_key": "SWITZERLAND_JOB_OS|CLAIM-CONVERGENCE-LINEAGE-021|ACQUIRED",
        "canonical_hotel_mutation_allowed": False,
        "h_id_allocation_allowed": False,
        "outbound_allowed": False,
        "causation": [
            f"claim:{CLAIM_ID}",
            "predecessor:CLAIM-CONVERGENCE-LEASE-020",
            f"lease:{LEASE_ID}",
            f"main:{MAIN}",
            "fencing_high_watermark:20",
            "repair:TERMINAL_LINEAGE_SUCCESSION",
        ],
    }
    write_json("docs/state/v2/events/EVT-20260912T203915Z-CONVERGENCE-TOKEN21-ACQUIRED.json", event)

    heartbeat = {
        "heartbeat_id": "HB-AGENT-GPT56SOL-CONVERGENCE-021-INIT",
        "project_id": "SWITZERLAND_JOB_OS",
        "agent_id": AGENT_ID,
        "session_id": SESSION_ID,
        "workstream_id": "WS-CONVERGENCE-LEASE-REPAIR",
        "objective_id": "OBJ-SWISS-MAIN-SINGULARITY",
        "goal_ids": ["G-0001"],
        "plan_id": "PLAN-MAIN-SINGULARITY-P0",
        "task_id": "TASK-TERMINAL-LINEAGE-SUCCESSION-REPAIR",
        "claim_id": CLAIM_ID,
        "fencing_token": 21,
        "observed_at": TS,
        "state": "ACTIVE",
        "branch": "convergence/main-singularity",
        "worktree": ".worktrees/convergence-main-singularity",
        "base_main_sha": MAIN,
        "authority_ceiling": "CONVERGENCE_ORCHESTRATION_AND_LEASE_REPAIR_ONLY_NO_DOMAIN_OR_OUTBOUND_AUTHORITY",
        "graph_program": "GRAPH-REFACTOR-V2",
        "pr_number": 463,
        "current_iteration_id": None,
        "next_safe_action": "Patch and adversarially test terminal lineage succession, rebuild token21 projections, run exact-head gauntlet, then release token21 only after objective green evidence.",
    }
    write_json("docs/state/agent-runtime/heartbeats/HB-AGENT-GPT56SOL-CONVERGENCE-021-INIT.json", heartbeat)


def patch_lineage_guard() -> None:
    path = Path("scripts/material_mutation_lineage_guard.py")
    text = path.read_text(encoding="utf-8")
    if "def raw_terminal_claims_from_change(" in text:
        return
    old = "def terminal_claims_from_change(paths: list[str]) -> list[dict[str, Any]]:"
    if text.count(old) != 1:
        raise RuntimeError("unexpected terminal_claims_from_change definition count")
    text = text.replace(old, "def raw_terminal_claims_from_change(paths: list[str]) -> list[dict[str, Any]]:", 1)
    marker = "\n\ndef validate(paths: list[str], *, require_receipt: bool) -> list[str]:"
    if marker not in text:
        raise RuntimeError("validate marker missing")
    helper = '''

def _same_terminal_lineage(predecessor: dict[str, Any], successor: dict[str, Any]) -> bool:
    for key in ("project_id", "workstream_id", "objective_id", "branch"):
        if str(predecessor.get(key, "")) != str(successor.get(key, "")):
            return False
    p_token = predecessor.get("fencing_token")
    s_token = successor.get("fencing_token")
    if isinstance(p_token, bool) or isinstance(s_token, bool):
        return False
    if not isinstance(p_token, int) or not isinstance(s_token, int):
        return False
    return s_token > p_token


def collapse_terminal_successions(
    claims: list[dict[str, Any]], acquisition_events: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Collapse only explicit, monotonic predecessor->successor chains.

    Unrelated terminal claims remain separate and therefore fail closed in validate().
    """
    by_id = {str(c.get("claim_id", "")): c for c in claims if c.get("claim_id")}
    edges: set[tuple[str, str]] = set()

    def add_edge(predecessor_id: str, successor_id: str) -> None:
        predecessor = by_id.get(predecessor_id)
        successor = by_id.get(successor_id)
        if predecessor and successor and _same_terminal_lineage(predecessor, successor):
            edges.add((predecessor_id, successor_id))

    for claim in claims:
        cid = str(claim.get("claim_id", ""))
        successor_id = claim.get("superseded_by")
        if cid and isinstance(successor_id, str) and successor_id:
            add_edge(cid, successor_id)

    for event in acquisition_events:
        if event.get("event_type") != "CLAIM_ACQUIRED":
            continue
        causation = event.get("causation", [])
        if not isinstance(causation, list):
            continue
        successor_ids = [
            x.split(":", 1)[1]
            for x in causation
            if isinstance(x, str) and x.startswith("claim:")
        ]
        predecessor_ids = [
            x.split(":", 1)[1]
            for x in causation
            if isinstance(x, str) and (x.startswith("supersedes:") or x.startswith("predecessor:"))
        ]
        for predecessor_id in predecessor_ids:
            for successor_id in successor_ids:
                add_edge(predecessor_id, successor_id)

    replaced = {predecessor for predecessor, _successor in edges}
    return sorted(
        [claim for claim in claims if str(claim.get("claim_id", "")) not in replaced],
        key=lambda claim: (int(claim.get("fencing_token", 0)), str(claim.get("claim_id", ""))),
    )


def terminal_claims_from_change(paths: list[str]) -> list[dict[str, Any]]:
    terminal = raw_terminal_claims_from_change(paths)
    if len(terminal) <= 1:
        return terminal
    acquisition_events: list[dict[str, Any]] = []
    for event_path in sorted(set(paths)):
        if not event_path.startswith("docs/state/v2/events/") or not event_path.endswith(".json"):
            continue
        payload = load_json(ROOT / event_path)
        if payload.get("event_type") == "CLAIM_ACQUIRED":
            acquisition_events.append(payload)
    return collapse_terminal_successions(terminal, acquisition_events)
'''
    text = text.replace(marker, helper + marker, 1)
    path.write_text(text, encoding="utf-8")


def patch_tests() -> None:
    path = Path("tests/test_material_mutation_lineage.py")
    text = path.read_text(encoding="utf-8")
    if "test_terminal_succession_chain_selects_unique_effective_owner" in text:
        return
    marker = '\n\nif __name__ == "__main__":\n'
    if marker not in text:
        raise RuntimeError("test main marker missing")
    addition = '''

    def test_terminal_succession_chain_selects_unique_effective_owner(self):
        base = {"project_id":"SWITZERLAND_JOB_OS","workstream_id":"WS-X","objective_id":"OBJ-X","branch":"feat/x"}
        c19 = {**base,"claim_id":"CLAIM-19","fencing_token":19,"state":"SUPERSEDED","superseded_by":"CLAIM-20"}
        c20 = {**base,"claim_id":"CLAIM-20","fencing_token":20,"state":"RELEASED"}
        c21 = {**base,"claim_id":"CLAIM-21","fencing_token":21,"state":"RELEASED"}
        events = [
            {"event_type":"CLAIM_ACQUIRED","causation":["claim:CLAIM-20","supersedes:CLAIM-19"]},
            {"event_type":"CLAIM_ACQUIRED","causation":["claim:CLAIM-21","predecessor:CLAIM-20"]},
        ]
        result = guard.collapse_terminal_successions([c19,c20,c21], events)
        self.assertEqual([c["claim_id"] for c in result], ["CLAIM-21"])

    def test_unrelated_terminal_claims_remain_ambiguous(self):
        common = {"project_id":"SWITZERLAND_JOB_OS","objective_id":"OBJ-X","branch":"feat/x"}
        c20 = {**common,"workstream_id":"WS-A","claim_id":"CLAIM-20","fencing_token":20,"state":"RELEASED"}
        c21 = {**common,"workstream_id":"WS-B","claim_id":"CLAIM-21","fencing_token":21,"state":"RELEASED"}
        result = guard.collapse_terminal_successions([c20,c21], [])
        self.assertEqual({c["claim_id"] for c in result}, {"CLAIM-20","CLAIM-21"})

    def test_invalid_cross_lineage_predecessor_edge_does_not_collapse(self):
        common = {"project_id":"SWITZERLAND_JOB_OS","objective_id":"OBJ-X","branch":"feat/x"}
        c20 = {**common,"workstream_id":"WS-A","claim_id":"CLAIM-20","fencing_token":20,"state":"RELEASED"}
        c21 = {**common,"workstream_id":"WS-B","claim_id":"CLAIM-21","fencing_token":21,"state":"RELEASED"}
        event = {"event_type":"CLAIM_ACQUIRED","causation":["claim:CLAIM-21","predecessor:CLAIM-20"]}
        result = guard.collapse_terminal_successions([c20,c21], [event])
        self.assertEqual({c["claim_id"] for c in result}, {"CLAIM-20","CLAIM-21"})
'''
    text = text.replace(marker, addition + marker, 1)
    path.write_text(text, encoding="utf-8")


def update_pointers() -> None:
    config_path = Path("docs/refactor-v2/coordination_current_config.json")
    c = json.loads(config_path.read_text(encoding="utf-8"))
    c["generated_at"] = TS
    c["state"] = "CONVERGENCE_LINEAGE_REPAIR_TOKEN21_ACTIVE"
    c["blockers"] = [
        "Terminal material-lineage guard must collapse only explicit monotonic predecessor/successor chains; unrelated terminal claims must still fail closed.",
        "Explicit owner merge instruction remains required before PR #463 promotion.",
        "CRM_UNIVERSE_COMPLETE remains false because RECONCILE_REQUIRED=1403; B12/domain authority stays blocked.",
        "OUTBOUND remains CLOSED and send_allowed=0.",
    ]
    c["next_safe_actions"] = [
        "Adversarially test token19 SUPERSEDED -> token20 RELEASED -> token21 repair succession and unrelated-terminal ambiguity.",
        "Rebuild Runtime Graph/V2/Context Survival with token21 as the sole active writer.",
        "Run exact-head full repository gauntlet under the live token21 global CAS lease.",
        "Release token21 only after objective green evidence; terminalize to zero writers and re-certify exact terminal head.",
    ]
    refs = [
        x
        for x in c.get("source_refs", [])
        if not (
            x.startswith("claim:CLAIM-CONVERGENCE-LEASE-020:")
            or x.startswith("lease:coordination/execution-lease:TOKEN20:")
        )
    ]
    refs += [
        "claim:CLAIM-CONVERGENCE-LEASE-020:RELEASED_PREDECESSOR",
        f"claim:{CLAIM_ID}:ACTIVE",
        "lease:coordination/execution-lease:TOKEN21:ACTIVE_CAS",
        "repair:TERMINAL_LINEAGE_SUCCESSION",
    ]
    c["source_refs"] = list(dict.fromkeys(refs))
    additions = {
        "relevant_paths": [
            f"docs/state/v2/claims/{CLAIM_ID}.json",
            "docs/state/v2/events/EVT-20260912T203915Z-CONVERGENCE-TOKEN21-ACQUIRED.json",
            "docs/state/agent-runtime/heartbeats/HB-AGENT-GPT56SOL-CONVERGENCE-021-INIT.json",
            "tests/test_material_mutation_lineage.py",
        ],
        "survival_paths": [
            f"docs/state/v2/claims/{CLAIM_ID}.json",
            "docs/state/agent-runtime/heartbeats/HB-AGENT-GPT56SOL-CONVERGENCE-021-INIT.json",
        ],
    }
    for key, values in additions.items():
        current = c.get(key, [])
        if isinstance(current, list):
            for value in values:
                if value not in current:
                    current.append(value)
            c[key] = current
    c["resume_contract"] = [
        f"verify live main remains {MAIN} or an ancestry-safe descendant with no relevant-scope drift",
        "read coordination/execution-lease current.json and require token21/session021/parent-main/E4 parity plus live TTL",
        f"replay claims/events and require {CLAIM_ID} as the sole active claim with fencing token21",
        "verify predecessor claim20 is RELEASED and acquisition event21 explicitly references predecessor:CLAIM-CONVERGENCE-LEASE-020",
        "verify E4/690, H-0691 unallocated, terminal mappings 658 and RECONCILE_REQUIRED 1403",
        "keep B12 backlog-only and OUTBOUND=CLOSED/send_allowed=0",
        "require exact Runtime Graph/V2/Context Survival equality before qualification",
        "do not merge without explicit owner instruction",
    ]
    c["liveness_findings"] = [
        "Token20 bounded convergence claim remains terminal RELEASED and is the explicit predecessor of token21.",
        f"Token21 is the sole active writer under global GitHub SHA-CAS lease {LEASE_ID}.",
        "The repair changes lineage interpretation only; operational hotel/CRM/H-ID/outbound authority remains unchanged.",
    ]
    c["unverified_work"] = [
        "Token21 terminal-lineage succession regression tests and exact-head gauntlet must pass.",
        "Token21 Runtime Graph/V2/Context Survival active projections must be deterministic.",
        "Token21 must be released only after KEEP evidence; terminal exact-head must then be re-certified.",
    ]
    verified = c.setdefault("verified_work", [])
    fact = "Global CAS lease token21 was acquired from zero-writer watermark20 using expected blob SHA; no main-watermark-only allocation was used."
    if fact not in verified:
        verified.append(fact)
    graph = c.setdefault("graph", {})
    nodes = graph.setdefault("nodes", [])
    existing = {n.get("id") for n in nodes if isinstance(n, dict)}
    for node in [
        {"id": f"C:{CLAIM_ID}", "state": "ACTIVE_TOKEN_21", "type": "Claim"},
        {"id": "L:GLOBAL-EXECUTION-LEASE-021", "state": "ACTIVE_CAS", "type": "ExecutionLease"},
    ]:
        if node["id"] not in existing:
            nodes.append(node)
    for node in nodes:
        if node.get("id") == "PR:463":
            node["state"] = "LINEAGE_REPAIR_ACTIVE_TOKEN21"
    edges = graph.setdefault("edges", [])
    for edge in [
        {"from": "C:CLAIM-CONVERGENCE-LEASE-020", "to": f"C:{CLAIM_ID}", "type": "PREDECESSOR_OF"},
        {"from": f"C:{CLAIM_ID}", "to": "PR:463", "type": "EXECUTES_ON"},
        {"from": "L:GLOBAL-EXECUTION-LEASE-021", "to": f"C:{CLAIM_ID}", "type": "SERIALIZES_WRITER"},
    ]:
        if edge not in edges:
            edges.append(edge)
    write_json(config_path, c)

    root_path = Path("docs/state/NEXT.json")
    root = json.loads(root_path.read_text(encoding="utf-8"))
    root["generated_at"] = TS
    root["active_claim"] = {
        "authority_ceiling": "CONVERGENCE_ORCHESTRATION_AND_LEASE_REPAIR_ONLY_NO_DOMAIN_OR_OUTBOUND_AUTHORITY",
        "branch": "convergence/main-singularity",
        "claim_id": CLAIM_ID,
        "fencing_token": 21,
        "session_id": SESSION_ID,
    }
    root["convergence_route"] = "CONVERGENCE_LINEAGE_REPAIR_TOKEN21_ACTIVE"
    root["exact_dependency"] = "The sole convergence writer is token21 under global CAS, bounded to terminal lineage succession repair; CRM domain remains unresolved at 1403 and B12 is not authorized."
    root["hard_blockers"] = [
        "TOKEN21_TERMINAL_LINEAGE_SUCCESSION_REPAIR_NOT_YET_QUALIFIED",
        "EXPLICIT_OWNER_MERGE_INSTRUCTION_REQUIRED_FOR_PR_463",
        "RECONCILE_REQUIRED_1403_NOT_ZERO",
        "GOAL_DRAIN_BLOCKS_B12_AUTOMATIC_EXECUTION",
        "OUTBOUND_CLOSED",
    ]
    root["next_safe_actions"] = [
        "Run token21 lineage regression tests and deterministic active projection rebuild.",
        "Run exact-head full gauntlet under live global lease token21.",
        "Release and terminalize token21 only after green evidence, then re-certify terminal head.",
        "Await explicit owner merge instruction; do not start B12 or another feature wave.",
    ]
    root["successor_execution_allowed"] = False
    write_json(root_path, root, indent=2)

    for pointer_path in [
        "docs/state/NEXT_CONVERGENCE_ONLY_2026-09-12.json",
        "docs/state/v2/NEXT_CONVERGENCE_ONLY_2026-09-12.json",
    ]:
        p = Path(pointer_path)
        d = json.loads(p.read_text(encoding="utf-8"))
        if "status" in d:
            d["status"] = "LINEAGE_REPAIR_ACTIVE"
        d["claim_id"] = CLAIM_ID
        d["claim_state"] = "ACTIVE"
        d["session_id"] = SESSION_ID
        d["fencing_token"] = 21
        d["blockers"] = [
            "Token21 terminal-lineage succession repair must pass exact-head qualification.",
            "Explicit owner merge instruction is required before PR #463 promotion.",
            "CRM_UNIVERSE_COMPLETE remains FALSE because RECONCILE_REQUIRED=1403.",
            "No outbound action is authorized.",
        ]
        d["next_safe_actions"] = [
            "Run token21 terminal-lineage regression tests and active projection rebuild.",
            "Run the full exact-head repository gauntlet under the live global CAS lease.",
            "Release token21 only after KEEP evidence; rebuild zero-writer terminal state and re-certify.",
            "Await explicit owner merge instruction; do not start B12.",
        ]
        write_json(p, d)


def main() -> None:
    materialize_claim_event_heartbeat()
    patch_lineage_guard()
    patch_tests()
    update_pointers()


if __name__ == "__main__":
    main()

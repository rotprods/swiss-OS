#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from swiss_os.v2_coordination import build_context_pack, reduce_coordination, sha256_json

ROOT = Path(__file__).resolve().parents[1]
GENERATED_REL = {
    "docs/state/v2/active-claims.json": "active-claims.json",
    "docs/state/v2/project-state.json": "project-state.json",
    "docs/state/v2/context-pack.json": "context-pack.json",
    "docs/state/v2/graph-snapshot.json": "graph-snapshot.json",
    "docs/continuity/CONTEXT_SURVIVAL.json": "CONTEXT_SURVIVAL.json",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def git_blob_oid_bytes(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def git_blob_oid_existing(rel: str) -> str:
    return subprocess.check_output(["git", "hash-object", rel], cwd=ROOT, text=True).strip()


def domain_route(payload: dict[str, Any]) -> str:
    for key in ("route", "next_route", "selected_route"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError("domain NEXT has no route")


def build_outputs(config_path: Path) -> dict[str, dict[str, Any]]:
    config = load_json(config_path)
    events = [load_json(p) for p in sorted((ROOT / "docs/state/v2/events").glob("*.json"))]
    claims = [load_json(p) for p in sorted((ROOT / "docs/state/v2/claims").glob("*.json"))]
    projection = reduce_coordination(events, claims)
    if projection.get("violations"):
        raise ValueError(f"coordination projection violations: {projection['violations']}")

    active = sorted(
        (c for c in claims if c.get("state") == "ACTIVE"),
        key=lambda c: (int(c.get("fencing_token", 0)), str(c.get("claim_id", ""))),
    )
    active_claims = {
        "schema_version": "COS-V2-ACTIVE-CLAIMS-1.0",
        "project_id": config["project_id"],
        "as_of_main_sha": config["base_main_sha"],
        "claims": active,
        "collisions": projection.get("claim_collisions", []),
        "fencing_high_watermark": max((int(c.get("fencing_token", 0)) for c in claims), default=0),
    }

    prior_state = load_json(ROOT / "docs/state/v2/project-state.json")
    state = dict(prior_state)
    state.update(
        {
            "main_sha_observed": config["base_main_sha"],
            "state": config["state"],
            "current_objective_id": config["current_objective_id"],
            "branch": config["branch"],
            "projection_revision": projection["projection_revision"],
            "event_watermark": projection["event_watermark"],
            "active_claim_ids": projection["active_claim_ids"],
            "open_prs": config["open_prs"],
            "blockers": config["blockers"],
            "verified_work": config["verified_work"],
            "unverified_work": config["unverified_work"],
            "risks": config["risks"],
            "next_safe_actions": config["next_safe_actions"],
            "source_refs": [
                "GOAL.md",
                "STATE.md",
                "docs/state/NEXT.json",
                "docs/refactor-v2/GRAPH_REFACTOR_V2_RECONSOLIDATION_2026-09-01.md",
                "docs/refactor-v2/implementation_program_2026-09-01.json",
                "issue:#416",
                "pr:#404:SUPERSEDED_UNMERGED",
                f"main:{config['base_main_sha']}",
            ],
        }
    )

    graph = {
        "schema_version": "COS-V2-HYPERGRAPH-SNAPSHOT-1.0",
        "project_id": config["project_id"],
        "main_sha_observed": config["base_main_sha"],
        "projection_revision": projection["projection_revision"],
        "context_pack_revision": "PENDING_CONTEXT_BUILD",
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "nodes": [
            {"id": "P:SWITZERLAND_JOB_OS", "type": "Project", "state": "ACTIVE"},
            {"id": "G:G-0001", "type": "NorthStar", "state": "ACTIVE"},
            {"id": "O:OBJ-GRAPH-V2-CURRENT-TRUTH", "type": "Objective", "state": "ACTIVE"},
            {"id": "A:HOTEL_AUTHORITY", "type": "Authority", "state": "LOCKED_E4_690"},
            {"id": "C:CLAIM-CRM-SRR-SPECIAL-006", "type": "Claim", "state": "SUPERSEDED_TOKEN_6"},
            {"id": "C:CLAIM-GRAPHV2-RECOVERY-008", "type": "Claim", "state": "ACTIVE_TOKEN_8"},
            {"id": "ISSUE:416", "type": "Bug", "state": "REPAIR_IN_PROGRESS"},
            {"id": "PR:404", "type": "PullRequest", "state": "SUPERSEDED_UNMERGED_EVIDENCE"},
            {"id": "ARCH:GRAPH_V2_RECONSOLIDATION", "type": "Architecture", "state": "CURRENT_RECONSOLIDATION"},
        ],
        "edges": [
            {"from": "O:OBJ-GRAPH-V2-CURRENT-TRUTH", "to": "P:SWITZERLAND_JOB_OS", "type": "PART_OF"},
            {"from": "C:CLAIM-GRAPHV2-RECOVERY-008", "to": "C:CLAIM-CRM-SRR-SPECIAL-006", "type": "SUPERSEDES"},
            {"from": "C:CLAIM-GRAPHV2-RECOVERY-008", "to": "A:HOTEL_AUTHORITY", "type": "ISOLATES"},
            {"from": "ISSUE:416", "to": "C:CLAIM-GRAPHV2-RECOVERY-008", "type": "MITIGATED_BY"},
            {"from": "PR:404", "to": "C:CLAIM-GRAPHV2-RECOVERY-008", "type": "EVIDENCE_FOR"},
        ],
        "hyperrelations": [
            {
                "id": "HR:GRAPHV2-RECOVERY-008",
                "type": "FENCED_COORDINATION_RECOVERY",
                "members": [
                    "O:OBJ-GRAPH-V2-CURRENT-TRUTH",
                    "C:CLAIM-CRM-SRR-SPECIAL-006",
                    "C:CLAIM-GRAPHV2-RECOVERY-008",
                    "ISSUE:416",
                    "A:HOTEL_AUTHORITY",
                ],
                "semantics": "Token8 repairs stale coordination state while explicitly isolating operational hotel authority and external action.",
            }
        ],
    }

    generated: dict[str, dict[str, Any]] = {
        "active-claims.json": active_claims,
        "project-state.json": state,
        "graph-snapshot.json": graph,
    }

    def oid_for_rel(rel: str) -> str:
        mapped = GENERATED_REL.get(rel)
        if mapped and mapped in generated:
            return git_blob_oid_bytes(canonical_bytes(generated[mapped]))
        return git_blob_oid_existing(rel)

    relevant_paths = list(config["relevant_paths"])
    entries = [f"{rel}:{oid_for_rel(rel)}" for rel in relevant_paths]
    scope_revision = hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()
    context = build_context_pack(
        project_id=config["project_id"],
        base_main_sha=config["base_main_sha"],
        authority_revision=str(state["authority_revision"]),
        projection=projection,
        state_refs=list(config["state_refs"]),
        relevant_paths=relevant_paths,
        relevant_scope_revision=scope_revision,
        blockers=list(config["blockers"]),
        next_safe_actions=list(config["next_safe_actions"]),
    )
    generated["context-pack.json"] = context
    graph["context_pack_revision"] = context["context_pack_revision"]
    generated["graph-snapshot.json"] = graph

    latest_domain_next = str(config["latest_domain_next"])
    domain = load_json(ROOT / latest_domain_next)
    survival_paths = [
        "GOAL.md",
        "STATE.md",
        "HANDOFF.md",
        "TASKS.md",
        "docs/state/NEXT.json",
        "docs/state/v2/project-state.json",
        "docs/state/v2/context-pack.json",
        "docs/state/v2/active-claims.json",
        "docs/operations/CONTEXT_SURVIVAL_PROTOCOL.md",
        "docs/handoffs/NEXT_ITERATION_METAPROMPT_V3.md",
        latest_domain_next,
    ]
    file_oids = {rel: oid_for_rel(rel) for rel in survival_paths}
    next_root = load_json(ROOT / "docs/state/NEXT.json")
    safety = next_root.get("safety") if isinstance(next_root.get("safety"), dict) else {}
    csp = {
        "schema_version": "COS-V2-CONTEXT-SURVIVAL-1.0",
        "project_id": config["project_id"],
        "repo": "rotprods/swiss-OS",
        "generated_at": config["generated_at"],
        "ancestry_floor_sha": config["base_main_sha"],
        "authority_epoch": str(state["authority_epoch"]),
        "authority_revision": str(state["authority_revision"]),
        "projection_revision": str(state["projection_revision"]),
        "context_pack_revision": str(context["context_pack_revision"]),
        "event_watermark": context["event_watermark"],
        "active_claim_ids": list(projection["active_claim_ids"]),
        "primary_program": "GRAPH_REFACTOR_V2_RECONSOLIDATION",
        "production_route": domain_route(domain),
        "latest_domain_next": latest_domain_next,
        "survival_paths": survival_paths,
        "git_blob_oid": file_oids,
        "liveness_findings": [
            "CSP is recovery integrity metadata, never operational hotel authority.",
            "Token8 is coordination-recovery-only; domain decisions and external actions are excluded.",
            "Historical token7 B07 work is preserved on superseded PR #404 but is not current-main state.",
        ],
        "resume_contract": [
            "verify live main and ancestry",
            "verify pinned survival-file Git blob OIDs",
            "re-read active claims and fencing high watermark",
            "re-read private candidate asset authority before candidate readiness",
            "re-read external operational authority before any material domain mutation",
            "reject stale ContextPack/CSP and rebuild from durable events/claims",
            "resume the highest-value safe task; never infer state from chat memory",
        ],
        "safety": {
            "authority_advance_allowed": False,
            "canonical_id_allocation_allowed": False,
            "canonical_id_reservations_from_staging": 0,
            "authority_from_canary_or_cache": False,
            "crm_universe_complete": bool(safety.get("crm_universe_complete", False)),
            "outbound": str(safety.get("outbound", "CLOSED")),
            "send_allowed": int(safety.get("send_allowed", 0)),
            "irreversible_external_actions": int(safety.get("irreversible_external_actions", 0)),
        },
    }
    csp["payload_sha256"] = sha256_json(csp)
    generated["CONTEXT_SURVIVAL.json"] = csp

    manifest = {
        "schema_version": "V2-COORDINATION-REBUILD-RECEIPT-1.0",
        "base_main_sha": config["base_main_sha"],
        "projection_revision": projection["projection_revision"],
        "context_pack_revision": context["context_pack_revision"],
        "event_watermark": projection["event_watermark"],
        "active_claim_ids": projection["active_claim_ids"],
        "fencing_high_watermark": active_claims["fencing_high_watermark"],
        "claim_collisions": projection["claim_collisions"],
        "generated_files": {
            name: hashlib.sha256(canonical_bytes(value)).hexdigest() for name, value in generated.items()
        },
        "safety": {
            "authority_advanced": False,
            "h_id_allocations": 0,
            "outbound": "CLOSED",
            "send_allowed": 0,
        },
    }
    generated["rebuild-receipt.json"] = manifest
    return generated


def write_outputs(outputs: dict[str, dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        (out_dir / name).write_bytes(canonical_bytes(value))


def check_outputs(outputs: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for rel, name in GENERATED_REL.items():
        expected = canonical_bytes(outputs[name])
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"MISSING:{rel}")
            continue
        actual = path.read_bytes()
        try:
            normalized_actual = canonical_bytes(json.loads(actual.decode("utf-8")))
        except Exception:
            normalized_actual = actual
        if normalized_actual != expected:
            errors.append(f"DRIFT:{rel}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default="/tmp/v2-coordination-rebuild")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build_outputs(ROOT / args.config)
    write_outputs(outputs, Path(args.output_dir))
    receipt = outputs["rebuild-receipt.json"]
    print(json.dumps(receipt, indent=2, sort_keys=True))
    if args.check:
        errors = check_outputs(outputs)
        if errors:
            print("coordination rebuild check: FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        print("coordination rebuild check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


def _string_list(config: dict[str, Any], key: str, default: list[str] | None = None) -> list[str]:
    value = config.get(key, default if default is not None else [])
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"config.{key} must be a list of non-empty strings")
    return list(value)


def _graph_payload(config: dict[str, Any], projection_revision: str) -> dict[str, Any]:
    spec = config.get("graph")
    if not isinstance(spec, dict):
        raise ValueError("config.graph is required; coordination rebuild must not hardcode a historical workstream graph")
    for key in ("nodes", "edges", "hyperrelations"):
        if not isinstance(spec.get(key), list):
            raise ValueError(f"config.graph.{key} must be a list")
    return {
        "schema_version": "COS-V2-HYPERGRAPH-SNAPSHOT-1.0",
        "project_id": config["project_id"],
        "main_sha_observed": config["base_main_sha"],
        "projection_revision": projection_revision,
        "context_pack_revision": "PENDING_CONTEXT_BUILD",
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "nodes": spec["nodes"],
        "edges": spec["edges"],
        "hyperrelations": spec["hyperrelations"],
    }


def build_outputs(config_path: Path) -> dict[str, dict[str, Any]]:
    config = load_json(config_path)
    for key in (
        "project_id",
        "base_main_sha",
        "generated_at",
        "state",
        "current_objective_id",
        "branch",
        "primary_program",
        "latest_domain_next",
    ):
        value = config.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"config.{key} required")

    events = [load_json(path) for path in sorted((ROOT / "docs/state/v2/events").glob("*.json"))]
    claims = [load_json(path) for path in sorted((ROOT / "docs/state/v2/claims").glob("*.json"))]
    projection = reduce_coordination(events, claims)
    if projection.get("violations"):
        raise ValueError(f"coordination projection violations: {projection['violations']}")

    active_ids = set(projection.get("active_claim_ids", []))
    active = sorted(
        (claim for claim in claims if str(claim.get("claim_id", "")) in active_ids),
        key=lambda claim: (int(claim.get("fencing_token", 0)), str(claim.get("claim_id", ""))),
    )
    active_claims = {
        "schema_version": "COS-V2-ACTIVE-CLAIMS-1.0",
        "project_id": config["project_id"],
        "as_of_main_sha": config["base_main_sha"],
        "claims": active,
        "collisions": projection.get("claim_collisions", []),
        "fencing_high_watermark": max((int(claim.get("fencing_token", 0)) for claim in claims), default=0),
        "lifecycle_projection_revision": projection["projection_revision"],
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
            "open_prs": config.get("open_prs", []),
            "blockers": _string_list(config, "blockers"),
            "verified_work": _string_list(config, "verified_work"),
            "unverified_work": _string_list(config, "unverified_work"),
            "risks": _string_list(config, "risks"),
            "next_safe_actions": _string_list(config, "next_safe_actions"),
            "source_refs": _string_list(config, "source_refs"),
        }
    )

    graph = _graph_payload(config, str(projection["projection_revision"]))
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

    relevant_paths = _string_list(config, "relevant_paths")
    entries = [f"{rel}:{oid_for_rel(rel)}" for rel in relevant_paths]
    scope_revision = hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()
    context = build_context_pack(
        project_id=config["project_id"],
        base_main_sha=config["base_main_sha"],
        authority_revision=str(state["authority_revision"]),
        projection=projection,
        state_refs=_string_list(config, "state_refs"),
        relevant_paths=relevant_paths,
        relevant_scope_revision=scope_revision,
        blockers=_string_list(config, "blockers"),
        next_safe_actions=_string_list(config, "next_safe_actions"),
    )
    generated["context-pack.json"] = context
    graph["context_pack_revision"] = context["context_pack_revision"]
    generated["graph-snapshot.json"] = graph

    latest_domain_next = str(config["latest_domain_next"])
    domain = load_json(ROOT / latest_domain_next)
    survival_paths = _string_list(
        config,
        "survival_paths",
        [
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
        ],
    )
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
        "primary_program": config["primary_program"],
        "production_route": domain_route(domain),
        "latest_domain_next": latest_domain_next,
        "survival_paths": survival_paths,
        "git_blob_oid": file_oids,
        "liveness_findings": _string_list(config, "liveness_findings"),
        "resume_contract": _string_list(config, "resume_contract"),
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
        "schema_version": "V2-COORDINATION-REBUILD-RECEIPT-1.1",
        "base_main_sha": config["base_main_sha"],
        "projection_revision": projection["projection_revision"],
        "context_pack_revision": context["context_pack_revision"],
        "event_watermark": projection["event_watermark"],
        "active_claim_ids": projection["active_claim_ids"],
        "claim_states": projection.get("claim_states", {}),
        "claim_lifecycle": projection.get("claim_lifecycle", []),
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

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "COS-V2-CONTEXT-SURVIVAL-1.0"
CHECKPOINT = ROOT / "docs/continuity/CONTEXT_SURVIVAL.json"
DEFAULT_DOMAIN_NEXT = "docs/state/NEXT_CURRENT_UNRESOLVED_LT350_B01.json"
DEFAULT_SURVIVAL_PATHS = (
    "GOAL.md",
    "STATE.md",
    "HANDOFF.md",
    "TASKS.md",
    "docs/state/NEXT.json",
    "docs/state/v2/project-state.json",
    "docs/state/v2/context-pack.json",
    "docs/state/v2/active-claims.json",
    DEFAULT_DOMAIN_NEXT,
    "docs/operations/CONTEXT_SURVIVAL_PROTOCOL.md",
    "docs/handoffs/NEXT_ITERATION_METAPROMPT_V3.md",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def file_oid(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise ValueError(f"missing survival file: {rel}")
    return git("hash-object", rel)


def load_json(rel: str) -> dict[str, Any]:
    value = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{rel}: expected JSON object")
    return value


def is_ancestor(base: str, head: str = "HEAD") -> bool:
    if not isinstance(base, str) or len(base) != 40:
        return False
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, head],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def domain_route(payload: dict[str, Any]) -> str:
    for key in ("route", "next_route", "selected_route"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError("domain NEXT has no route/next_route/selected_route")


def build_checkpoint(
    *,
    base_main_sha: str,
    generated_at: str,
    latest_domain_next: str = DEFAULT_DOMAIN_NEXT,
    primary_program: str = "REPO_ARCHAEOLOGY_GRAPHIFY_V1",
) -> dict[str, Any]:
    if len(base_main_sha) != 40 or any(c not in "0123456789abcdef" for c in base_main_sha):
        raise ValueError("base_main_sha must be lowercase 40-hex")
    if not generated_at.strip():
        raise ValueError("generated_at required")

    project = load_json("docs/state/v2/project-state.json")
    context = load_json("docs/state/v2/context-pack.json")
    active_claims = load_json("docs/state/v2/active-claims.json")
    next_root = load_json("docs/state/NEXT.json")
    domain = load_json(latest_domain_next)

    paths = list(DEFAULT_SURVIVAL_PATHS)
    if latest_domain_next != DEFAULT_DOMAIN_NEXT:
        paths = [latest_domain_next if p == DEFAULT_DOMAIN_NEXT else p for p in paths]

    claim_ids = sorted(
        str(item.get("claim_id", ""))
        for item in active_claims.get("claims", [])
        if isinstance(item, dict) and item.get("claim_id")
    )
    file_oids = {rel: file_oid(rel) for rel in paths}

    safety = next_root.get("safety") if isinstance(next_root.get("safety"), dict) else {}
    checkpoint: dict[str, Any] = {
        "schema_version": SCHEMA,
        "project_id": "SWITZERLAND_JOB_OS",
        "repo": "rotprods/swiss-OS",
        "generated_at": generated_at,
        "ancestry_floor_sha": base_main_sha,
        "authority_epoch": str(project.get("authority_epoch", "")),
        "authority_revision": str(project.get("authority_revision", "")),
        "projection_revision": str(project.get("projection_revision", "")),
        "context_pack_revision": str(context.get("context_pack_revision", "")),
        "event_watermark": context.get("event_watermark"),
        "active_claim_ids": claim_ids,
        "primary_program": primary_program,
        "production_route": domain_route(domain),
        "latest_domain_next": latest_domain_next,
        "survival_paths": paths,
        "git_blob_oid": file_oids,
        "liveness_findings": [
            "CSP sidecar is authoritative only for recovery integrity, never hotel authority.",
            "The COS event watermark may lag live main; zero-context bootstrap MUST verify live ancestry and pinned files rather than infer freshness from event time alone.",
        ],
        "resume_contract": [
            "verify live main and ancestry",
            "verify every pinned survival-file Git blob OID",
            "re-read active claims/fencing",
            "re-read external authority before material mutation",
            "rebuild checkpoint on any survival-file drift",
            "resume highest-value safe route; never resume from chat memory alone",
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
    checkpoint["payload_sha256"] = sha256_json(checkpoint)
    return checkpoint


def validate_checkpoint(checkpoint: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if checkpoint.get("schema_version") != SCHEMA:
        errors.append("INVALID_SCHEMA")
    if checkpoint.get("project_id") != "SWITZERLAND_JOB_OS":
        errors.append("INVALID_PROJECT")
    if checkpoint.get("repo") != "rotprods/swiss-OS":
        errors.append("INVALID_REPO")

    floor = checkpoint.get("ancestry_floor_sha")
    if not isinstance(floor, str) or not is_ancestor(floor):
        errors.append("ANCESTRY_FLOOR_NOT_ANCESTOR")

    paths = checkpoint.get("survival_paths")
    digests = checkpoint.get("git_blob_oid")
    if not isinstance(paths, list) or not paths:
        errors.append("INVALID_SURVIVAL_PATHS")
        paths = []
    if not isinstance(digests, dict):
        errors.append("INVALID_FILE_OIDS")
        digests = {}
    for rel in paths:
        if not isinstance(rel, str) or not rel.strip():
            errors.append("INVALID_SURVIVAL_PATH")
            continue
        try:
            current = file_oid(rel)
        except (ValueError, subprocess.SubprocessError):
            errors.append(f"MISSING_SURVIVAL_FILE:{rel}")
            continue
        if digests.get(rel) != current:
            errors.append(f"SURVIVAL_FILE_DRIFT:{rel}")

    project = load_json("docs/state/v2/project-state.json")
    context = load_json("docs/state/v2/context-pack.json")
    active_claims = load_json("docs/state/v2/active-claims.json")
    domain = load_json(str(checkpoint.get("latest_domain_next", DEFAULT_DOMAIN_NEXT)))

    if checkpoint.get("authority_epoch") != project.get("authority_epoch"):
        errors.append("STALE_AUTHORITY_EPOCH")
    if checkpoint.get("authority_revision") != project.get("authority_revision"):
        errors.append("STALE_AUTHORITY_REVISION")
    if checkpoint.get("projection_revision") != project.get("projection_revision"):
        errors.append("STALE_PROJECTION_REVISION")
    if checkpoint.get("context_pack_revision") != context.get("context_pack_revision"):
        errors.append("STALE_CONTEXT_PACK_REVISION")
    if checkpoint.get("event_watermark") != context.get("event_watermark"):
        errors.append("STALE_EVENT_WATERMARK")

    claim_ids = sorted(
        str(item.get("claim_id", ""))
        for item in active_claims.get("claims", [])
        if isinstance(item, dict) and item.get("claim_id")
    )
    if checkpoint.get("active_claim_ids") != claim_ids:
        errors.append("STALE_ACTIVE_CLAIMS")

    try:
        route = domain_route(domain)
    except ValueError:
        route = ""
        errors.append("INVALID_DOMAIN_NEXT")
    if checkpoint.get("production_route") != route:
        errors.append("STALE_PRODUCTION_ROUTE")

    safety = checkpoint.get("safety")
    expected_safety = {
        "authority_advance_allowed": False,
        "canonical_id_allocation_allowed": False,
        "canonical_id_reservations_from_staging": 0,
        "authority_from_canary_or_cache": False,
        "crm_universe_complete": False,
        "outbound": "CLOSED",
        "send_allowed": 0,
        "irreversible_external_actions": 0,
    }
    if not isinstance(safety, dict):
        errors.append("INVALID_SAFETY")
    else:
        for key, expected in expected_safety.items():
            value = safety.get(key)
            if value != expected or (type(expected) is int and isinstance(value, bool)):
                errors.append(f"SAFETY_LOCK_MISMATCH:{key}")

    payload_hash = checkpoint.get("payload_sha256")
    expected_hash = sha256_json({k: v for k, v in checkpoint.items() if k != "payload_sha256"})
    if payload_hash != expected_hash:
        errors.append("PAYLOAD_HASH_MISMATCH")

    protocol = (ROOT / "docs/operations/CONTEXT_SURVIVAL_PROTOCOL.md").read_text(encoding="utf-8")
    prompt = (ROOT / "docs/handoffs/NEXT_ITERATION_METAPROMPT_V3.md").read_text(encoding="utf-8")
    handoff = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")
    for marker in (
        "chat/model context is disposable cache",
        "Zero-context bootstrap",
        "REPO_ARCHAEOLOGY_GRAPHIFY_V1",
    ):
        if marker.lower() not in protocol.lower():
            errors.append(f"PROTOCOL_MARKER_MISSING:{marker}")
    for marker in ("ROUTING OVERRIDE", "ZERO CONTEXT", "REPO_ARCHAEOLOGY_GRAPHIFY_V1", "CONTEXT SURVIVAL / COMPACTION"):
        if marker not in prompt:
            errors.append(f"METAPROMPT_MARKER_MISSING:{marker}")
    if "A successor does not resume from chat memory." not in handoff:
        errors.append("HANDOFF_ZERO_CONTEXT_RULE_MISSING")

    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--base-main-sha")
    parser.add_argument("--generated-at")
    parser.add_argument("--latest-domain-next", default=DEFAULT_DOMAIN_NEXT)
    args = parser.parse_args(argv)

    if args.write:
        base = args.base_main_sha or git("rev-parse", "HEAD~1")
        generated_at = args.generated_at
        if not generated_at:
            raise SystemExit("--generated-at is required with --write for deterministic checkpoints")
        checkpoint = build_checkpoint(
            base_main_sha=base,
            generated_at=generated_at,
            latest_domain_next=args.latest_domain_next,
        )
        CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
        CHECKPOINT.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"context_survival_guard: WROTE {CHECKPOINT.relative_to(ROOT)} {checkpoint['payload_sha256']}")
        return 0

    if not CHECKPOINT.is_file():
        print("context_survival_guard: FAIL\n- MISSING_CONTEXT_SURVIVAL_CHECKPOINT")
        return 1
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    errors = validate_checkpoint(checkpoint)
    if errors:
        print("context_survival_guard: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "context_survival_guard: PASS "
        f"route={checkpoint['production_route']} "
        f"program={checkpoint['primary_program']} "
        f"checkpoint={checkpoint['payload_sha256']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

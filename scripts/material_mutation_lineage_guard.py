#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from swiss_os.v2_coordination import reduce_coordination

ROOT = Path(__file__).resolve().parents[1]
NON_MATERIAL_PREFIXES = (
    ".github/ISSUE_TEMPLATE/",
    "docs/reports/",
)
NON_MATERIAL_EXACT = {
    "README.md",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def changed_paths() -> list[str]:
    explicit = os.environ.get("GRAPH_V2_CHANGED_PATHS")
    if explicit:
        return sorted({p.strip() for p in explicit.split("\n") if p.strip()})
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    base_ref = os.environ.get("GITHUB_BASE_REF", "")
    if event == "pull_request" and base_ref:
        subprocess.run(["git", "fetch", "origin", base_ref, "--quiet"], cwd=ROOT, check=False)
        base = git("merge-base", f"origin/{base_ref}", "HEAD")
        out = git("diff", "--name-only", f"{base}...HEAD")
    else:
        try:
            out = git("diff", "--name-only", "HEAD^", "HEAD")
        except subprocess.CalledProcessError:
            out = ""
    return sorted({p for p in out.splitlines() if p})


def is_material(path: str) -> bool:
    if path in NON_MATERIAL_EXACT or any(path.startswith(prefix) for prefix in NON_MATERIAL_PREFIXES):
        return False
    return True


def path_allowed(path: str, scopes: list[str]) -> bool:
    for scope in scopes:
        if scope.endswith("/**") and path.startswith(scope[:-3]):
            return True
        if any(ch in scope for ch in "*?[") and fnmatch.fnmatch(path, scope):
            return True
        if path == scope:
            return True
    return False


def latest_heartbeats() -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "docs/state/agent-runtime/heartbeats").glob("*.json")):
        hb = load_json(path)
        sid = str(hb.get("session_id", ""))
        if not sid:
            continue
        prior = latest.get(sid)
        if prior is None or str(hb.get("observed_at", "")) > str(prior.get("observed_at", "")):
            latest[sid] = hb
    return latest


def receipt_sessions() -> set[str]:
    sessions: set[str] = set()
    for path in sorted((ROOT / "docs/state/agent-runtime/iterations").glob("*.json")):
        receipt = load_json(path)
        context = receipt.get("context")
        if (
            receipt.get("schema_version") == "AGENT-IMPROVEMENT-ITERATION-1.1"
            and receipt.get("tests_passed") is True
            and receipt.get("decision") in {"KEEP", "DISCARD", "BLOCKED", "CRASH"}
            and isinstance(context, dict)
            and context.get("session_id")
        ):
            sessions.add(str(context["session_id"]))
    return sessions


def active_claims() -> list[dict[str, Any]]:
    events = [load_json(p) for p in sorted((ROOT / "docs/state/v2/events").glob("*.json"))]
    claims = [load_json(p) for p in sorted((ROOT / "docs/state/v2/claims").glob("*.json"))]
    projection = reduce_coordination(events, claims)
    violations = projection.get("violations", [])
    if violations:
        raise ValueError(f"coordination violations: {violations}")
    active_ids = set(projection.get("active_claim_ids", []))
    return [claim for claim in claims if str(claim.get("claim_id", "")) in active_ids]


def validate(paths: list[str], *, require_receipt: bool) -> list[str]:
    material = [p for p in paths if is_material(p)]
    if not material:
        return []
    errors: list[str] = []
    claims = active_claims()
    if len(claims) != 1:
        return [f"MATERIAL_CHANGE_REQUIRES_EXACTLY_ONE_ACTIVE_CLAIM:{len(claims)}"]
    claim = claims[0]
    branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or git("branch", "--show-current")
    expected_branch = str(claim.get("branch", ""))
    if branch and branch not in {expected_branch, "main"}:
        errors.append(f"CLAIM_BRANCH_MISMATCH:{branch}!={expected_branch}")
    scopes = [str(x) for x in claim.get("resource_scopes", []) if isinstance(x, str)]
    for path in material:
        if not path_allowed(path, scopes):
            errors.append(f"MATERIAL_PATH_OUTSIDE_CLAIM_SCOPE:{path}")
    session_id = str(claim.get("session_id", ""))
    heartbeat = latest_heartbeats().get(session_id)
    if not heartbeat:
        errors.append(f"MISSING_SESSION_HEARTBEAT:{session_id}")
    else:
        if heartbeat.get("graph_program") != "GRAPH-REFACTOR-V2":
            errors.append("NON_GRAPH_V2_HEARTBEAT")
        if heartbeat.get("claim_id") != claim.get("claim_id"):
            errors.append("HEARTBEAT_CLAIM_MISMATCH")
        if heartbeat.get("fencing_token") != claim.get("fencing_token"):
            errors.append("HEARTBEAT_FENCING_MISMATCH")
        if heartbeat.get("state") not in {"ACTIVE", "BLOCKED"} and not require_receipt:
            errors.append(f"MATERIAL_WORK_HEARTBEAT_NOT_ACTIVE:{heartbeat.get('state')}")
    if require_receipt and session_id not in receipt_sessions():
        errors.append(f"MATERIAL_CHANGE_MISSING_ITERATION_RECEIPT:{session_id}")
    return sorted(set(errors))


def main() -> int:
    paths = changed_paths()
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    # PRs are in-flight and may be guarded by claim+heartbeat before their final receipt.
    # Main/direct-push qualification is stricter: a completed durable receipt is mandatory.
    require_receipt = event == "push" and (os.environ.get("GITHUB_REF_NAME") == "main")
    errors = validate(paths, require_receipt=require_receipt)
    if errors:
        print("material_mutation_lineage_guard: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"material_mutation_lineage_guard: PASS changed={len(paths)} receipt_required={require_receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

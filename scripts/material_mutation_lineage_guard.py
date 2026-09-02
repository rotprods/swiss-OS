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
NON_MATERIAL_PREFIXES = (".github/ISSUE_TEMPLATE/", "docs/reports/")
NON_MATERIAL_EXACT = {"README.md"}
TERMINAL_CLAIM_STATES = {"RELEASED", "SUPERSEDED"}
TERMINAL_HEARTBEAT_STATES = {"COMPLETE", "SUPERSEDED"}


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
    return not (path in NON_MATERIAL_EXACT or any(path.startswith(prefix) for prefix in NON_MATERIAL_PREFIXES))


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


def all_claims_and_projection() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events = [load_json(p) for p in sorted((ROOT / "docs/state/v2/events").glob("*.json"))]
    claims = [load_json(p) for p in sorted((ROOT / "docs/state/v2/claims").glob("*.json"))]
    projection = reduce_coordination(events, claims)
    if projection.get("violations"):
        raise ValueError(f"coordination violations: {projection['violations']}")
    return claims, projection


def active_claims() -> list[dict[str, Any]]:
    claims, projection = all_claims_and_projection()
    active_ids = set(projection.get("active_claim_ids", []))
    return [claim for claim in claims if str(claim.get("claim_id", "")) in active_ids]


def terminal_claims_from_change(paths: list[str]) -> list[dict[str, Any]]:
    claims, projection = all_claims_and_projection()
    states = projection.get("claim_states", {}) if isinstance(projection.get("claim_states"), dict) else {}
    changed = set(paths)
    result: list[dict[str, Any]] = []
    for claim in claims:
        cid = str(claim.get("claim_id", ""))
        if not cid or states.get(cid) not in TERMINAL_CLAIM_STATES:
            continue
        claim_path = f"docs/state/v2/claims/{cid}.json"
        if claim_path not in changed:
            continue
        has_terminal_event = False
        for event_path in changed:
            if not event_path.startswith("docs/state/v2/events/") or not event_path.endswith(".json"):
                continue
            payload = load_json(ROOT / event_path)
            if payload.get("event_type") not in {"CLAIM_RELEASED", "CLAIM_SUPERSEDED"}:
                continue
            causation = payload.get("causation", [])
            if isinstance(causation, list) and f"claim:{cid}" in causation:
                has_terminal_event = True
                break
        if has_terminal_event:
            result.append(claim)
    return result


def validate(paths: list[str], *, require_receipt: bool) -> list[str]:
    material = [p for p in paths if is_material(p)]
    if not material:
        return []
    errors: list[str] = []
    active = active_claims()
    terminal_mode = False
    if len(active) == 1:
        claim = active[0]
    elif len(active) == 0:
        terminal = terminal_claims_from_change(paths)
        if len(terminal) != 1:
            return [f"MATERIAL_CHANGE_REQUIRES_ONE_ACTIVE_OR_TERMINALIZED_CLAIM:{len(terminal)}"]
        claim = terminal[0]
        terminal_mode = True
        require_receipt = True
    else:
        return [f"MATERIAL_CHANGE_REQUIRES_EXACTLY_ONE_ACTIVE_CLAIM:{len(active)}"]

    branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or git("branch", "--show-current")
    expected_branch = str(claim.get("branch", ""))
    if not terminal_mode and branch and branch not in {expected_branch, "main"}:
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
        allowed_hb_states = TERMINAL_HEARTBEAT_STATES if terminal_mode else {"ACTIVE", "BLOCKED"}
        if heartbeat.get("state") not in allowed_hb_states:
            errors.append(f"MATERIAL_WORK_HEARTBEAT_STATE_INVALID:{heartbeat.get('state')}")

    if require_receipt and session_id not in receipt_sessions():
        errors.append(f"MATERIAL_CHANGE_MISSING_ITERATION_RECEIPT:{session_id}")
    return sorted(set(errors))


def main() -> int:
    paths = changed_paths()
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    require_receipt = event == "push" and os.environ.get("GITHUB_REF_NAME") == "main"
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

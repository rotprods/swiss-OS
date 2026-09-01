from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .session_runtime import canonical_json, sha256_json


def _escape(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def render_progress_md(runtime: Mapping[str, Any]) -> str:
    progress = runtime["progress"]
    lines = [f"# Progress — {runtime['session_id']}", ""]
    lines.append(f"Lifecycle: **{runtime['lifecycle_state']}** / `{runtime['lifecycle_detail']}`")
    lines.append(f"Liveness: **{runtime['liveness']}** (`{runtime['liveness_evidence']}`)")
    if progress.get("completion_percent") is None:
        lines.append("Progress: **UNKNOWN / legacy or unreported**")
    else:
        lines.append(
            f"Progress: **{progress['completion_percent']}%** "
            f"({progress['completed_weight']}/{progress['total_weight']} weighted units)"
        )
    lines += ["", "| Item | State | Weight | Summary |", "|---|---|---:|---|"]
    for item in progress.get("items", []):
        lines.append(
            f"| {_escape(item.get('item_id'))} | {_escape(item.get('state'))} | "
            f"{_escape(item.get('weight', 1))} | {_escape(item.get('summary'))} |"
        )
    return "\n".join(lines) + "\n"


def render_goals_md(runtime: Mapping[str, Any]) -> str:
    identity = runtime.get("graph_runtime_identity") or {}
    goals = identity.get("goal_ids") or []
    claim = identity.get("claim_id") or ",".join((runtime.get("claims") or {}).get("active_claim_ids") or []) or "UNKNOWN"
    token = identity.get("fencing_token")
    if token is None:
        token = (runtime.get("claims") or {}).get("max_fencing_token")
    return "\n".join([
        f"# Goals — {runtime['session_id']}",
        "",
        f"- Workstream: `{runtime.get('workstream_id')}`",
        f"- Objective: `{runtime.get('objective_id')}`",
        f"- Goals: {', '.join(f'`{goal}`' for goal in goals) if goals else 'UNKNOWN'}",
        f"- Plan: `{identity.get('plan_id') or 'UNKNOWN'}`",
        f"- Task: `{identity.get('task_id') or 'UNKNOWN'}`",
        f"- Claim: `{claim}`",
        f"- Fencing token: `{token}`",
        "",
    ])


def render_context_md(runtime: Mapping[str, Any]) -> str:
    locator = runtime.get("runtime_locator") or {}
    identity = runtime.get("graph_runtime_identity") or {}
    lines = [
        f"# Context — {runtime['session_id']}",
        "",
        f"- Agent: `{runtime.get('agent_id')}`",
        f"- SRP contract: `{runtime.get('srp_contract_state')}`",
        f"- Branch: `{runtime.get('branch') or identity.get('branch') or 'UNKNOWN'}`",
        f"- PR: `{runtime.get('pr') if runtime.get('pr') is not None else identity.get('pr_number')}`",
        f"- Base main: `{runtime.get('base_sha') or identity.get('base_main_sha') or 'UNKNOWN'}`",
        f"- Latest observed main: `{runtime.get('main_sha_observed') or 'UNKNOWN'}`",
        f"- Runtime provider: `{locator.get('provider') or 'UNKNOWN'}`",
        f"- chat_id: `{locator.get('chat_id') if locator.get('chat_id') is not None else 'NULL'}`",
        f"- chat_id state: `{locator.get('chat_id_state') or 'UNKNOWN'}`",
        f"- Authority ceiling: `{identity.get('authority_ceiling') or 'UNKNOWN'}`",
    ]
    if runtime.get("recovery_inputs"):
        lines += ["", "## Recovery inputs"] + [f"- `{item}`" for item in runtime["recovery_inputs"]]
    if runtime.get("violations"):
        lines += ["", "## Runtime violations"] + [f"- `{item}`" for item in runtime["violations"]]
    return "\n".join(lines) + "\n"


def render_handoff_md(runtime: Mapping[str, Any]) -> str:
    items = runtime["progress"].get("items", [])
    completed = [item for item in items if item.get("state") in {"COMPLETED", "SKIPPED"}]
    remaining = [item for item in items if item.get("state") in {"PENDING", "IN_PROGRESS", "BLOCKED"}]
    lines = [
        f"# Handoff — {runtime['session_id']}",
        "",
        f"- Lifecycle: **{runtime['lifecycle_state']}**",
        f"- Detail: `{runtime['lifecycle_detail']}`",
        f"- Liveness: **{runtime['liveness']}**",
        f"- Last event: `{runtime.get('last_event_id')}` @ `{runtime.get('last_event_at')}`",
        f"- Last heartbeat: `{runtime.get('last_heartbeat_at') or 'NONE'}`",
        f"- Next action: {runtime.get('next_action') or 'UNKNOWN'}",
    ]
    if runtime.get("blockers"):
        lines += ["", "## Blockers"] + [f"- {item}" for item in runtime["blockers"]]
    lines += ["", "## Completed"]
    lines += [f"- `{item.get('item_id')}` — {item.get('summary', '')}" for item in completed] or ["- None reported"]
    lines += ["", "## Remaining"]
    lines += [f"- `{item.get('item_id')}` [{item.get('state')}] — {item.get('summary', '')}" for item in remaining] or ["- None reported"]
    if runtime.get("liveness") in {"STALE", "ORPHANED_CANDIDATE"}:
        lines += [
            "",
            "## Recovery rule",
            "Do not reuse this session_id for takeover. Replay durable state, verify branch/PR/provider state, "
            "release or supersede stale ownership when eligible, then acquire a strictly higher fencing token in a new session.",
        ]
    return "\n".join(lines) + "\n"


def build_session_bundle(runtime: Mapping[str, Any]) -> dict[str, str]:
    files = {
        "session.json": canonical_json(dict(runtime)) + "\n",
        "progress.state.json": canonical_json(dict(runtime["progress"])) + "\n",
        "PROGRESS.md": render_progress_md(runtime),
        "GOALS.md": render_goals_md(runtime),
        "CONTEXT.md": render_context_md(runtime),
        "HANDOFF.md": render_handoff_md(runtime),
    }
    manifest = {
        "schema_version": "COS-SRP-SESSION-BUNDLE-MANIFEST-1.0",
        "session_id": runtime["session_id"],
        "runtime_revision": runtime["runtime_revision"],
        "source_event_ids": runtime.get("event_ids", []),
        "source_claim_ids": (runtime.get("claims") or {}).get("claim_ids", []),
        "files": {
            name: hashlib.sha256(content.encode("utf-8")).hexdigest()
            for name, content in sorted(files.items())
        },
    }
    manifest["manifest_revision"] = sha256_json(manifest)
    files["MANIFEST.json"] = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return files

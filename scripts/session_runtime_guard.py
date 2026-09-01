#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swiss_os.session_runtime import validate_runtime_locator

RUNTIME_ROOT = ROOT / "docs/runtime"
REQUIRED_SESSION_FILES = {
    "session.json",
    "progress.state.json",
    "PROGRESS.md",
    "GOALS.md",
    "CONTEXT.md",
    "HANDOFF.md",
    "MANIFEST.json",
}


def fail(message: str) -> None:
    raise SystemExit(f"session_runtime_guard: {message}")


def require_text(path: str, needle: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    if needle not in text:
        fail(f"missing {needle!r} in {path}")


def main() -> int:
    for path in (
        "src/swiss_os/session_runtime.py",
        "src/swiss_os/session_runtime_views.py",
        "scripts/build_session_runtime.py",
        "docs/operations/SESSION_RUNTIME_PROTOCOL.md",
        "schemas/runtime/progress-snapshot.schema.json",
        "schemas/runtime/session-runtime.schema.json",
    ):
        if not (ROOT / path).exists():
            fail(f"missing required path {path}")

    # SRP implements the existing mandatory GRAPH-REFACTOR-V2 death-safe heartbeat law;
    # it does not define a second agent identity/ownership contract.
    require_text("AGENTS.md", "death-safe heartbeat")
    require_text("docs/operations/AGENT_AUTORESEARCH_PROGRAM.md", "Death-safe iteration boundary")
    require_text("docs/operations/SESSION_RUNTIME_PROTOCOL.md", "claim release")
    require_text("docs/operations/SESSION_RUNTIME_PROTOCOL.md", "ORPHANED_CANDIDATE")
    require_text("docs/operations/SESSION_RUNTIME_PROTOCOL.md", "UNAVAILABLE_BY_HARNESS")

    registry_path = RUNTIME_ROOT / "registry.json"
    if not registry_path.exists():
        fail("docs/runtime/registry.json missing; materialize SRP projections before merge")

    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_session_runtime.py"), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if completed.returncode:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail("deterministic runtime rebuild drift")

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("schema_version") != "COS-SRP-RUNTIME-REGISTRY-1.0":
        fail("registry schema mismatch")
    authority_contract = str(registry.get("authority_contract") or "")
    if "GIT_EVENT_CLAIM_FENCING_IS_OWNERSHIP_AUTHORITY" not in authority_contract:
        fail("registry authority boundary missing")
    if "OBSERVABILITY_ONLY" not in authority_contract:
        fail("registry does not mark lease/PR observations non-authoritative")

    sessions = registry.get("sessions")
    if not isinstance(sessions, list) or not sessions:
        fail("registry has no sessions")

    active_claim_session_ids: set[str] = set()
    native_count = 0
    session_ids = {str(row.get("session_id")) for row in sessions if isinstance(row, dict)}
    for runtime in sessions:
        if not isinstance(runtime, dict):
            fail("session row is not an object")
        session_id = str(runtime.get("session_id") or "")
        if not session_id:
            fail("session id missing")
        if runtime.get("liveness") == "DEAD":
            fail(f"timeout-derived DEAD state forbidden: {session_id}")
        locator_errors = validate_runtime_locator(runtime.get("runtime_locator"))
        if locator_errors:
            fail(f"invalid runtime locator {session_id}: {locator_errors}")
        if runtime.get("srp_contract_state") == "NATIVE_SRP":
            native_count += 1
            if runtime.get("lifecycle_state") == "ACTIVE" and not runtime.get("last_heartbeat_at"):
                fail(f"native active session lacks heartbeat: {session_id}")
            if runtime.get("violations"):
                fail(f"native session violations {session_id}: {runtime['violations']}")
        claims = runtime.get("claims") or {}
        if claims.get("active_claim_ids"):
            active_claim_session_ids.add(session_id)
        bundle_dir = RUNTIME_ROOT / "sessions" / session_id
        actual = {path.name for path in bundle_dir.iterdir() if path.is_file()} if bundle_dir.exists() else set()
        if actual != REQUIRED_SESSION_FILES:
            fail(f"session bundle file set mismatch {session_id}: {sorted(actual)}")
        manifest = json.loads((bundle_dir / "MANIFEST.json").read_text(encoding="utf-8"))
        if manifest.get("session_id") != session_id:
            fail(f"manifest session mismatch {session_id}")
        if manifest.get("runtime_revision") != runtime.get("runtime_revision"):
            fail(f"manifest runtime revision drift {session_id}")

    if native_count < 1:
        fail("no native SRP session proves activation")
    if not active_claim_session_ids.issubset(session_ids):
        fail("effective active claim missing session projection")

    token12 = [row for row in sessions if row.get("session_id") == "SES-20260901T221937Z-SRP-012"]
    if not token12:
        fail("token12 SRP activation session missing")
    token12 = token12[0]
    if token12.get("runtime_locator", {}).get("chat_id") is not None:
        fail("token12 fabricated a chat id")
    if token12.get("runtime_locator", {}).get("chat_id_state") != "UNAVAILABLE_BY_HARNESS":
        fail("token12 chat-id capability state mismatch")
    if token12.get("progress", {}).get("completion_percent") is None:
        fail("token12 weighted progress missing")

    for proposal in registry.get("unmerged_proposals") or []:
        if proposal.get("authority_state") not in {None, "OBSERVABILITY_ONLY", "UNMERGED_PROPOSAL"}:
            fail("unmerged proposal claims authority")
    for lease in registry.get("live_leases") or []:
        if lease.get("authority_state") not in {None, "OBSERVABILITY_ONLY"}:
            fail("live lease claims Git ownership authority")

    print(
        "session_runtime_guard: PASS "
        f"sessions={len(sessions)} native={native_count} "
        f"active_effective={len(active_claim_session_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

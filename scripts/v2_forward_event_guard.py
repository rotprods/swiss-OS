#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from swiss_os.v2_coordination import (
    FORWARD_EVENT_SCHEMA,
    LEGACY_EVENT_SCHEMA,
    LIFECYCLE_EVENT_TYPES,
    validate_event,
)

ROOT = Path(__file__).resolve().parents[1]
EVENT_DIR = ROOT / "docs/state/v2/events"
BOUNDARY_PATH = ROOT / "docs/state/v2/legacy-event-boundary.json"
FORWARD_SCHEMA_PATH = ROOT / "schemas/v2/event-1.1.schema.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def legacy_blob_error(base_sha: str, rel: str) -> str | None:
    try:
        baseline_oid = git("rev-parse", f"{base_sha}:{rel}")
    except subprocess.CalledProcessError:
        return f"NEW_LEGACY_EVENT_FORBIDDEN:{rel}"
    current_oid = git("hash-object", rel)
    if baseline_oid != current_oid:
        return f"LEGACY_EVENT_MUTATION_FORBIDDEN:{rel}:{baseline_oid}!={current_oid}"
    return None


def main() -> int:
    errors: list[str] = []
    if not BOUNDARY_PATH.is_file():
        errors.append("MISSING_LEGACY_EVENT_BOUNDARY")
    if not FORWARD_SCHEMA_PATH.is_file():
        errors.append("MISSING_FORWARD_EVENT_SCHEMA")
    if errors:
        print("v2_forward_event_guard: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    boundary = load(BOUNDARY_PATH)
    base_sha = boundary.get("frozen_at_main_sha")
    if not isinstance(base_sha, str) or len(base_sha) != 40:
        errors.append("INVALID_LEGACY_BOUNDARY_SHA")
        base_sha = ""
    else:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_sha, "HEAD"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 0:
            errors.append("LEGACY_BOUNDARY_NOT_ANCESTOR")

    legacy_count = 0
    forward_count = 0
    forward_lifecycle_count = 0
    for path in sorted(EVENT_DIR.glob("*.json")):
        rel = path.relative_to(ROOT).as_posix()
        event = load(path)
        for error in validate_event(event):
            errors.append(f"{path.name}:{error}")
        schema = event.get("schema_version")
        if schema == LEGACY_EVENT_SCHEMA:
            legacy_count += 1
            if base_sha:
                error = legacy_blob_error(base_sha, rel)
                if error:
                    errors.append(error)
        elif schema == FORWARD_EVENT_SCHEMA:
            forward_count += 1
            if event.get("event_type") in LIFECYCLE_EVENT_TYPES:
                forward_lifecycle_count += 1
        else:
            errors.append(f"UNSUPPORTED_EVENT_SCHEMA:{path.name}:{schema}")

    if forward_count == 0:
        errors.append("NO_FORWARD_EVENT_PRODUCTION_EVIDENCE")
    if forward_lifecycle_count == 0:
        errors.append("NO_FORWARD_LIFECYCLE_EVENT_EVIDENCE")

    if errors:
        print("v2_forward_event_guard: FAIL")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1

    print(
        "v2_forward_event_guard: PASS "
        f"legacy_frozen={legacy_count} forward={forward_count} "
        f"forward_lifecycle={forward_lifecycle_count} boundary={base_sha}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

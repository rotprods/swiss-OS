#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swiss_os.session_runtime import build_registry, canonical_json, derive_session_runtime
from swiss_os.session_runtime_views import build_session_bundle
from swiss_os.v2_coordination import derive_claim_lifecycle

EVENT_DIR = ROOT / "docs/state/v2/events"
CLAIM_DIR = ROOT / "docs/state/v2/claims"
DEFAULT_OUTPUT = ROOT / "docs/runtime"


def load_objects(directory: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"expected object: {path}")
        rows.append(value)
    return rows


def load_optional_rows(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        rows = value
    elif isinstance(value, dict) and isinstance(value.get("rows"), list):
        rows = value["rows"]
    else:
        raise ValueError(f"expected list or rows[] object: {path}")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"all rows must be objects: {path}")
    return [dict(row) for row in rows]


def effective_claims(events: list[dict[str, Any]], claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    states, _bindings, errors = derive_claim_lifecycle(events, claims)
    if errors:
        raise ValueError("claim lifecycle replay failed: " + ",".join(errors))
    output: list[dict[str, Any]] = []
    for claim in claims:
        row = dict(claim)
        claim_id = str(row.get("claim_id") or "")
        if claim_id in states:
            row["state"] = states[claim_id]
        output.append(row)
    return output


def build_runtime_tree(
    *,
    observed_at: str,
    proposals: list[dict[str, Any]],
    live_leases: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, Any]]:
    events = load_objects(EVENT_DIR)
    claims = effective_claims(events, load_objects(CLAIM_DIR))
    by_session: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        session_id = str(event.get("session_id") or "").strip()
        if not session_id:
            continue
        by_session.setdefault(session_id, []).append(event)

    runtimes: list[dict[str, Any]] = []
    files: dict[str, str] = {}
    for session_id in sorted(by_session):
        runtime = derive_session_runtime(by_session[session_id], claims, observed_at=observed_at)
        runtimes.append(runtime)
        bundle = build_session_bundle(runtime)
        for name, content in bundle.items():
            files[f"sessions/{session_id}/{name}"] = content

    registry = build_registry(
        runtimes,
        observed_at=observed_at,
        unmerged_proposals=proposals,
        live_leases=live_leases,
    )
    files["registry.json"] = canonical_json(registry) + "\n"
    return files, registry


def compare_tree(output_dir: Path, expected: dict[str, str]) -> list[str]:
    errors: list[str] = []
    expected_paths = set(expected)
    existing_paths = {
        str(path.relative_to(output_dir))
        for path in output_dir.rglob("*")
        if path.is_file()
    } if output_dir.exists() else set()
    for rel in sorted(expected_paths):
        path = output_dir / rel
        if not path.exists():
            errors.append(f"MISSING:{rel}")
        elif path.read_text(encoding="utf-8") != expected[rel]:
            errors.append(f"DRIFT:{rel}")
    for rel in sorted(existing_paths - expected_paths):
        errors.append(f"UNEXPECTED:{rel}")
    return errors


def write_tree(output_dir: Path, files: dict[str, str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(output_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
    for rel, content in sorted(files.items()):
        path = output_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def observed_at_for_check(output_dir: Path) -> str:
    registry = json.loads((output_dir / "registry.json").read_text(encoding="utf-8"))
    value = str(registry.get("observed_at") or "").strip()
    if not value:
        raise ValueError("committed registry observed_at missing")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SRP-1.0 session runtime registry and death-safe bundles")
    parser.add_argument("--observed-at", help="ISO-8601 liveness observation time; required for write mode")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--proposal-observations", type=Path)
    parser.add_argument("--live-leases", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    observed_at = args.observed_at
    if args.check and not observed_at:
        observed_at = observed_at_for_check(args.output_dir)
    if not observed_at:
        parser.error("--observed-at is required outside --check against an existing registry")

    proposals = load_optional_rows(args.proposal_observations)
    live_leases = load_optional_rows(args.live_leases)
    files, registry = build_runtime_tree(
        observed_at=observed_at,
        proposals=proposals,
        live_leases=live_leases,
    )

    if args.check:
        errors = compare_tree(args.output_dir, files)
        if errors:
            for error in errors[:100]:
                print(error)
            return 1
        print(
            "session_runtime: PASS "
            f"sessions={registry['summary']['session_count']} "
            f"live={registry['summary']['live']} "
            f"stale={registry['summary']['stale']} "
            f"orphaned={registry['summary']['orphaned_candidate']}"
        )
        return 0

    write_tree(args.output_dir, files)
    print(canonical_json(registry["summary"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

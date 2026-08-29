#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from swiss_os.v2_runtime_drills import run_all_runtime_drills  # noqa: E402
from swiss_os.v2_shadow_bridge import execute_read_only_next_shadow  # noqa: E402


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--next", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if len(args.commit_sha) != 40:
        raise SystemExit("--commit-sha must contain 40 characters")

    next_payload = read_json(args.next)
    if not isinstance(next_payload, dict):
        raise SystemExit("NEXT payload must be a JSON object")
    runtime = run_all_runtime_drills(args.commit_sha)
    shadow = execute_read_only_next_shadow(
        next_payload,
        main_sha=args.commit_sha,
        generated_at=runtime.generated_at,
    )
    if not runtime.passed:
        raise SystemExit("one or more runtime drills failed")
    if not shadow.passed:
        raise SystemExit("CRM NEXT shadow execution failed")

    args.out.mkdir(parents=True, exist_ok=True)
    runtime_path = args.out / "runtime_drills.json"
    shadow_path = args.out / "crm_next_shadow.json"
    ledger_path = args.out / "crm_next_shadow_event_ledger.jsonl"
    write_json(runtime_path, runtime.to_dict())
    write_json(shadow_path, shadow.to_dict())
    ledger_path.write_text(shadow.event_ledger_jsonl, encoding="utf-8")

    manifest_files = {}
    for path in (runtime_path, shadow_path, ledger_path):
        manifest_files[path.name] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    manifest = {
        "schema_version": "GRAPH_V2_RUNTIME_DRILL_MANIFEST_1",
        "commit_sha": args.commit_sha,
        "runtime_drills_passed": runtime.passed,
        "crm_shadow_passed": shadow.passed,
        "runtime_drill_count": len(runtime.results),
        "crm_shadow_event_count": len(
            [line for line in shadow.event_ledger_jsonl.splitlines() if line]
        ),
        "crm_shadow_graph_digest": shadow.graph["graph_digest"],
        "crm_shadow_contextpack_digest": shadow.contextpack["digest"],
        "crm_shadow_event_watermark": shadow.event_watermark,
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
        "files": manifest_files,
    }
    write_json(args.out / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

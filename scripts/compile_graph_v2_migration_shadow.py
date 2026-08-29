#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from swiss_os.v2_migration import (  # noqa: E402
    MigrationInventory,
    compile_migration_shadow,
)


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


def resolve_salt(env_name: str) -> str:
    value = os.environ.get(env_name, "")
    if len(value) < 16:
        raise SystemExit(
            f"pseudonym salt environment variable {env_name} must contain at least 16 characters"
        )
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compiler-sha", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument(
        "--salt-env",
        default="SWISS_OS_V2_PSEUDONYM_SALT",
    )
    args = parser.parse_args()

    raw = read_json(args.inventory)
    inventory = MigrationInventory.from_mapping(raw)
    result = compile_migration_shadow(
        inventory,
        compiler_sha=args.compiler_sha,
        branch=args.branch,
        generated_at=args.generated_at,
        pseudonym_salt=resolve_salt(args.salt_env),
    )

    args.out.mkdir(parents=True, exist_ok=True)
    paths = {
        "public_attestation.json": result.public_attestation,
        "private_shadow_graph.json": result.private_graph,
        "private_id_map.json": result.private_id_map,
        "contextpack.json": result.contextpack,
        "rollback_manifest.json": result.rollback_manifest,
        "migration_plan.json": result.migration_plan,
    }
    for name, payload in paths.items():
        write_json(args.out / name, payload)
    (args.out / "migration_event_ledger.jsonl").write_text(
        result.event_ledger_jsonl,
        encoding="utf-8",
    )

    manifest_files: dict[str, dict[str, object]] = {}
    for path in sorted(args.out.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            manifest_files[path.name] = {
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "public_safe": path.name
                not in {"private_shadow_graph.json", "private_id_map.json"},
            }
    manifest = {
        "schema_version": "GRAPH_V2_CP13_SHADOW_MANIFEST_1",
        "state": result.public_attestation["state"],
        "source_main_sha": result.public_attestation["source_main_sha"],
        "compiler_sha": result.public_attestation["compiler_sha"],
        "authority_epoch": result.public_attestation["authority_epoch"],
        "authority_manifest_sha256": result.public_attestation[
            "authority_manifest_sha256"
        ],
        "physical_count": result.public_attestation["parity"][
            "physical_count"
        ],
        "active_count": result.public_attestation["parity"]["active_count"],
        "alias_count": result.public_attestation["parity"]["alias_count"],
        "entity_binding_count": result.public_attestation["parity"][
            "entity_binding_count"
        ],
        "graph_digest": result.public_attestation["graph_digest"],
        "event_watermark": result.public_attestation["event_watermark"],
        "contextpack_digest": result.public_attestation[
            "contextpack_digest"
        ],
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

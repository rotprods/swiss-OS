from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .db import connect, foreign_key_violations, initialize, integrity_check
from .invariants import run_manifest_invariants
from .manifest import OperationalManifest


def cmd_manifest_validate(path: str) -> int:
    manifest = OperationalManifest.load(path)
    results = run_manifest_invariants(manifest)
    payload = {
        "manifest": manifest.public_summary(),
        "invariants": [r.__dict__ for r in results],
        "pass": all(r.passed for r in results),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["pass"] else 2


def cmd_db_init(path: str) -> int:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with connect(target) as conn:
        initialize(conn)
    print(json.dumps({"db": str(target), "initialized": True}))
    return 0


def cmd_db_check(path: str) -> int:
    with connect(path) as conn:
        integrity = integrity_check(conn)
        fk = foreign_key_violations(conn)
    payload = {
        "db": path,
        "integrity_check": integrity,
        "foreign_key_violations": len(fk),
        "pass": integrity.lower() == "ok" and not fk,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["pass"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="swiss-os")
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest", help="Validate a public-safe operational manifest")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)
    validate = manifest_sub.add_parser("validate")
    validate.add_argument("path")

    db = sub.add_parser("db", help="Initialize/check a constrained SQLite database")
    db_sub = db.add_subparsers(dest="db_command", required=True)
    init = db_sub.add_parser("init")
    init.add_argument("path")
    check = db_sub.add_parser("check")
    check.add_argument("path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "manifest" and args.manifest_command == "validate":
        return cmd_manifest_validate(args.path)
    if args.command == "db" and args.db_command == "init":
        return cmd_db_init(args.path)
    if args.command == "db" and args.db_command == "check":
        return cmd_db_check(args.path)
    return 2


if __name__ == "__main__":
    sys.exit(main())

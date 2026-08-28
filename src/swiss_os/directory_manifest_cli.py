"""CLI for provider-neutral coherent member-directory manifests."""

from __future__ import annotations

import argparse
import json
import sys

from .directory_manifest import (
    build_member_directory_manifest,
    read_json_object,
    validate_member_directory_manifest,
    write_json_atomic,
)


def cmd_build(input_path: str, out_path: str) -> int:
    manifest = build_member_directory_manifest(read_json_object(input_path))
    write_json_atomic(out_path, manifest)
    summary = {
        "snapshot_id": manifest["snapshot_id"],
        "capture_valid": manifest["capture_valid"],
        "coverage_complete": manifest["coverage_complete"],
        "expected_pages": manifest["expected_pages"],
        "observed_pages": manifest["observed_pages"],
        "reported_records": manifest["reported_records"],
        "records_count": manifest["records_count"],
        "records_sha256": manifest["records_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "violations": manifest["violations"],
        "authority_advanced": False,
        "h_id_allocations": 0,
        "outbound_opened": False,
        "send_allowed": 0,
        "out": out_path,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if manifest["coverage_complete"] else 2


def cmd_validate(path: str) -> int:
    result = validate_member_directory_manifest(read_json_object(path))
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0 if result.valid else 2


def cmd_recovery_import(input_path: str, out_path: str) -> int:
    payload = read_json_object(input_path)
    result = validate_member_directory_manifest(payload)
    if not result.valid:
        print(
            json.dumps(
                {"recovery_import_valid": False, **result.as_dict(), "output_written": False},
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    write_json_atomic(out_path, payload)
    print(
        json.dumps(
            {
                "recovery_import_valid": True,
                "coverage_complete": result.coverage_complete,
                "snapshot_id": payload.get("snapshot_id"),
                "manifest_sha256": payload.get("manifest_sha256"),
                "authority_advanced": False,
                "h_id_allocations": 0,
                "outbound_opened": False,
                "send_allowed": 0,
                "out": out_path,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.directory_manifest_cli")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("capture")
    build.add_argument("--out", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("manifest")
    recovery = sub.add_parser("recovery-import")
    recovery.add_argument("manifest")
    recovery.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            return cmd_build(args.capture, args.out)
        if args.command == "validate":
            return cmd_validate(args.manifest)
        if args.command == "recovery-import":
            return cmd_recovery_import(args.manifest, args.out)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc), "output_written": False}), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())

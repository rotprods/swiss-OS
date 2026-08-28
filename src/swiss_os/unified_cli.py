from __future__ import annotations

import json
import sys
from typing import Callable, Sequence

from . import cli as legacy_cli
from . import directory_export
from . import member_directory
from . import member_directory_capture
from . import meta_execution
from . import staging_adapter


class UnifiedCLIError(ValueError):
    """Raised when a unified command cannot be routed safely."""


LEGACY_COMMANDS = frozenset(
    {
        "manifest",
        "db",
        "crm-universe",
        "crm-snapshot",
        "discover-swiss",
        "crm-ingest",
        "crm-scope",
    }
)


def _usage() -> str:
    return """usage: swiss-os <command> [options]

Legacy commands:
  manifest
  db
  crm-universe
  crm-snapshot
  discover-swiss
  crm-ingest
  crm-scope

Meta execution / acquisition commands:
  meta-run validate-next <NEXT.json>
  meta-run select-route <routes.json> <capabilities.json> [--blockers blockers.json]
  member-directory build ...
  member-directory validate <manifest.json>
  member-directory capture ...
  staging-evidence extract-workbook ...
  directory-export <manifest.json> --records-out ... --attestation-out ...

All CRM-universe commands remain pre-outbound unless a separate future authority
and explicit-user-authorization gate passes.
"""


def _route_member_directory(args: list[str]) -> int:
    if not args:
        raise UnifiedCLIError("member-directory requires build, validate or capture")
    if args[0] == "capture":
        return member_directory_capture.main(args)
    return member_directory.main(args)


def dispatch(
    argv: Sequence[str],
    *,
    legacy_main: Callable[[list[str] | None], int] = legacy_cli.main,
    meta_main: Callable[[list[str] | None], int] = meta_execution.main,
    member_main: Callable[[list[str]], int] = _route_member_directory,
    staging_main: Callable[[list[str] | None], int] = staging_adapter.main,
    export_main: Callable[[list[str] | None], int] = directory_export.main,
) -> int:
    args = list(argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        print(_usage())
        return 0

    command, remainder = args[0], args[1:]
    if command in LEGACY_COMMANDS:
        return legacy_main(args)
    if command == "meta-run":
        return meta_main(remainder)
    if command == "member-directory":
        return member_main(remainder)
    if command == "staging-evidence":
        return staging_main(remainder)
    if command == "directory-export":
        return export_main(remainder)
    raise UnifiedCLIError(f"unknown swiss-os command: {command}")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        return dispatch(args)
    except (UnifiedCLIError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

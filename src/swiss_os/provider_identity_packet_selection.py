from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Mapping, Sequence


PACKET_RE = re.compile(r"^docs/state/PROVIDER_IDENTITY_WORK_[A-Za-z0-9_.-]+\.json$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ProviderIdentityPacketSelectionError(ValueError):
    pass


def validate_packet_path(value: str) -> str:
    path = value.strip()
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or not PACKET_RE.fullmatch(path):
        raise ProviderIdentityPacketSelectionError(f"invalid provider identity packet path: {value}")
    return path


def select_changed_paths(paths: Sequence[str]) -> str:
    candidates: set[str] = set()
    for raw in paths:
        if not isinstance(raw, str):
            continue
        try:
            candidates.add(validate_packet_path(raw))
        except ProviderIdentityPacketSelectionError:
            pass
    if len(candidates) != 1:
        raise ProviderIdentityPacketSelectionError(
            f"push must change exactly one provider identity work packet; found {len(candidates)}"
        )
    return next(iter(candidates))


def select_push_packet(event: Mapping[str, object]) -> str:
    commits = event.get("commits")
    if not isinstance(commits, list):
        raise ProviderIdentityPacketSelectionError("push event commits array missing")
    paths: list[str] = []
    for commit in commits:
        if not isinstance(commit, Mapping):
            continue
        for field in ("added", "modified"):
            values = commit.get(field, [])
            if isinstance(values, list):
                paths.extend(value for value in values if isinstance(value, str))
    return select_changed_paths(paths)


def select_from_event_file(event_path: str) -> str:
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    if not isinstance(event, Mapping):
        raise ProviderIdentityPacketSelectionError("GitHub event must be an object")
    return select_push_packet(event)


def select_from_git_diff(before: str, after: str, *, cwd: str = ".") -> str:
    if not SHA_RE.fullmatch(before) or not SHA_RE.fullmatch(after):
        raise ProviderIdentityPacketSelectionError("before/after must be lowercase 40-hex git SHAs")
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=AM", before, after, "--", "docs/state"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProviderIdentityPacketSelectionError(f"git diff packet selection failed: {exc}") from exc
    return select_changed_paths([line for line in result.stdout.splitlines() if line.strip()])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.provider_identity_packet_selection")
    parser.add_argument("event_path", nargs="?")
    parser.add_argument("--git-diff", nargs=2, metavar=("BEFORE", "AFTER"))
    args = parser.parse_args(argv)
    try:
        if args.git_diff:
            print(select_from_git_diff(args.git_diff[0], args.git_diff[1]))
        elif args.event_path:
            print(select_from_event_file(args.event_path))
        else:
            raise ProviderIdentityPacketSelectionError("event_path or --git-diff is required")
        return 0
    except (OSError, json.JSONDecodeError, ProviderIdentityPacketSelectionError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

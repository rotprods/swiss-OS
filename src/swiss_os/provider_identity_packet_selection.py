from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Mapping


PACKET_RE = re.compile(r"^docs/state/PROVIDER_IDENTITY_WORK_[A-Za-z0-9_.-]+\.json$")


class ProviderIdentityPacketSelectionError(ValueError):
    pass


def validate_packet_path(value: str) -> str:
    path = value.strip()
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or not PACKET_RE.fullmatch(path):
        raise ProviderIdentityPacketSelectionError(f"invalid provider identity packet path: {value}")
    return path


def select_push_packet(event: Mapping[str, object]) -> str:
    commits = event.get("commits")
    if not isinstance(commits, list):
        raise ProviderIdentityPacketSelectionError("push event commits array missing")
    candidates: set[str] = set()
    for commit in commits:
        if not isinstance(commit, Mapping):
            continue
        for field in ("added", "modified"):
            paths = commit.get(field, [])
            if not isinstance(paths, list):
                continue
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


def select_from_event_file(event_path: str) -> str:
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    if not isinstance(event, Mapping):
        raise ProviderIdentityPacketSelectionError("GitHub event must be an object")
    return select_push_packet(event)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m swiss_os.provider_identity_packet_selection")
    parser.add_argument("event_path")
    args = parser.parse_args(argv)
    try:
        print(select_from_event_file(args.event_path))
        return 0
    except (OSError, json.JSONDecodeError, ProviderIdentityPacketSelectionError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

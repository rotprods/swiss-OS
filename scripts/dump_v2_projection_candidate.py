#!/usr/bin/env python3
from __future__ import annotations

import base64
from pathlib import Path

from rebuild_v2_coordination import build_outputs, canonical_bytes

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "docs/refactor-v2/coordination_current_config.json"


def main() -> int:
    outputs = build_outputs(CONFIG)
    for name in (
        "active-claims.json",
        "project-state.json",
        "context-pack.json",
        "graph-snapshot.json",
        "CONTEXT_SURVIVAL.json",
    ):
        encoded = base64.b64encode(canonical_bytes(outputs[name])).decode("ascii")
        print(f"V2_CANDIDATE_B64:{name}:{encoded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
